"""
Een aantal losstaande functies en klasses voor betere verwerking van de OpenData

* StatTLineTable: klasse om de data gelezen door cbsodata te reorganiseren om het meer toegankelijk
  te maken
* DataProperties: help klasse, alleen gebruikt door StatLineTable
"""

import collections
import json
import logging
import math
import re
import sqlite3
from pathlib import Path

import matplotlib.pylab as plt
import pandas as pd
import requests
import yaml

logger = logging.getLogger(__name__)

try:
    from tabulate import tabulate
except ImportError as err:
    # tabulate is only needed for a proper doctring format of the pandas table
    logger.warning(err)


class DataProperties(object):
    """
    Class to hold the properties of an OpenData dataobject
    """

    def __init__(self, indicator_dict):
        self.id = indicator_dict.get("ID")
        self.position = indicator_dict.get("Position")
        self.parent_id = indicator_dict.get("ParentID")
        self.type = indicator_dict.get("Type")
        self.key = indicator_dict.get("Key")
        self.title = indicator_dict.get("Title")
        self.description = indicator_dict.get("Description")

        self.data_type = indicator_dict.get("Datatype")
        self.unit = indicator_dict.get("Unit")
        self.decimals = indicator_dict.get("Decimals")
        self.default = indicator_dict.get("Default")


class StatLineTable(object):
    """

    Read a statline table and save it as a Pandas dataframe.

    Parameters
    ----------
    table_id: str
        ID of the table to read, e.g. '84408NED'. The table ID can be found in the URL of the
        corresponding opendata URL. In this example: `OpenData`_
    reset: bool, optional
        In case opendata is read, all the files are written to cache. The next time you run the
        function, the data is read from cache, except when *reset* is True. In that case the
        data is read from OpenData again and the cache is refreshed
    cache_dir_name: str, optional
        Name of the cache directory (default: "cache")
    image_dir_name: str, optional
        Name of the image directory where all the plots are stored (default: "images")
    max_levels: int, optional
        Maximum number of levels to take into account (default: 5). A level referce the the depth
        of the question structure: the module is level 0, the question is level 1, the options is
        level 2. However, if a module is inside a chapter, this add to the levels, therefore, a
        save recommended value is level value of 5
    to_sql: bool, optional
        If True, store the generated table to sqlite. Each table is stored to a table inside
        a sqlite database. Default = False
    to_xls: bool, optional
        If True, store to Excel. Each table is stored to a seperate tab. Default = False
    to_pickle: bool, optional
        If True, store the tables to pickle. In case a picke file exist, not even the downloaded
        cache file are read, but the converted tables are directly obtained from the pickle files.
        Default = True
    write_questions_only: bool, optional
        Only write the questions
    reset_pickles: bool, optional
        By default, the opendata is stored to cache first and then converted from the json format
        to a proper DataFrame. This DataFrame is stored to cache in case *to_pickle* is set to
        True. In case a pickle file is found in the case, the DataFrame is directly obtained from
        the case (speeding up processing/home/eelco/PycharmProjects/CBS/cbs_utils time). If you want
        to regenerate the picke file, set this flag to true (or just empty the cache)
    section_key: str, optional
        Default column name to refer to a section. Default = "Section"
    title_key: str, optional
        Default column name to refer to a section. Default = "Title"
    value_key: str, optional
        Default column name to refer to a section. Default = "Value"
    units_key: str, optional
        Default column name to refer to the Units. Default = "Unit"
    key_key: str, optional
        Default column name to refer to the Key field. Default = "Key",
    datatype_key: str, optional
        Default column name to refer to the Datatype field. Default = "Datatype"
    id_key: str, optional
        Default column name to refer to the ID field. Default = "ID"
    parent_id_key: str, optional
        Default column name to refer to the ParentID field. Default = "ParentID"
    x_axis_key: str, optional
        Default column name to refer to the x_axis . Default = None, which means the x axis label
        is obtained from the index name of the dataframe itself
    legend_title: str, optional
       Add a legend title. Default = None, which means the legend title is obtained from the
       dataframe
    legend_position: tuple, optional
       Position of the legend.  Default is None, which means it is set at (1.05, 0)
    modules_to_plot: list or int, optional
        A list of module IDs (numbers refering the the module in statline) which we want to plot.
        If not given, or if the *plot_all_modules* flag is True, all the modules are plotted
    questions_to_plot: list or int, optional
        A list of question IDs (numbers refering the the question in statline) which we want to
        plot. If not given, or if the *plot_all_questions* flag is True, all the questions are
        plotted
    plot_all_modules: bool, optional
        Overrule the *modules_to_plot* list and plot all the modules available in the statline
        table.
    plot_all_questions: bool, optional
        Overrule the *questions_to_plot* list and plot all the modules available in the statline
        table.
    apply_selection: bool, optional
        Apply the selection given by the *selection* list. Default = True
    selection: list or dict, optional.
        Make a selection of options to plot. For instance, in case a question give the values for
        for all company sizes, normally, a bar plot for all company sizes is make. However, in case
        *apply_selection* is true, we only plot the items in the this list (or dict). A typical
        dict could be::

             selection:
                "010~020": '10 tot 20 werkzame personen'
                "020~050": '20 tot 50 werkzame personen'
                "050~100": '50 tot 100 werkzame personen'

    export_plot_data: bool, optional
        Export the data of the plot as it is to a excel data file. Easy if we want make a plot with
        another program, such as high charts. It ensures you use the same data
    image_type: str, optional
        The type of the plots to create. Default = ".png". Set it to ".pdf" in case you want to
        include it in Latex
    show_plot: bool, optional
        Show all the plots
    save_plot: bool, optional. Default = False
        Save all the plots. Default = False
    sort_choices: bool, optional
        Sort the choices of a question alphabetically. Default = False
    store_plot_data_to_xls: bool, optional
        Store the data of the plot (as shown, i.e. with the selected values) to an excel file.
        Default = False
    store_plot_data_to_tex: bool, optional
        Store the data of the plot (as shown, i.e. with the selected values) to a latex tabular
        file.
    survey_title_properties: dict, optional
        Put all the properties of the title into a dictionary. Default is None,  which means the
        following values a taken::

             loc: (0.02, 0.97),
             color: "blue",
             size: 12

    module_title_properties: dict, optional
        Put all the properties of the module title into a dictionary. Default is None,  which means
        the  following values are taken::

             loc: (0.02, 0.94),
             color: "blue",
             size: 12

    question_title_properties: dict, optional
        Put all the properties of the question title into a dictionary. Default is None,  which
        means the  following values are taken::

             loc: (0.02, 0.91),
             color: "blue",
             size: 12

    make_the_plots: bool, optional
        Make all the plots belonging to the statline question. Default is False
    describe_the_data: bool, optional
        Give a description of the loaded statline data set. Convenient to get the module and
        question ID which you need to use in the  *modules_to_plot*  *questions_to_plot*  list
    rotate_latex_columns: bool, optional
        If true, the labels of the columns names are rotated when writing the tables to latex
        format. Rotation is done by adding the *rot* command to the columns names, which is not a
        standard Latex commando. Therefore, in order to use this in latex, you need to add the
        following to your preamble::

                \\newcolumntype {R}[2] { %
                    > {\\adjustbox {angle =  # 1,lap=\\width-(#2)}\\bgroup}%
                    l %
                    < {\\egroup} %
                }
                \\newcommand *\\rot {\\multicolumn {1} {R {45} {1 em}}}

    write_info_to_image_dir: bool, optional
        Write the information of the data structure to a file in the image directory. Default = True
    color: str, optional
        Color for the plot. Default = "blue".
    fontsize: int, optional
        Font sizefor the plot. Default = 12

    Attributes
    ----------
    question_df: pd.DataFrame
        All the questions per dimension
    section_df: pd.DataFrame
        The names of the sections
    dimension_df: pd.DataFrame
        The names of the dimensions

    Examples
    --------

    An example of using the StatLineTable utility is given now

    >>> stat_line = StatLineTable(table_id="84408NED", to_sql=True, to_xls=True)

    This reads the stat line table '84408NED' and stores the results to a sqlite database

    The dataframes are accessible as:

    >>> stat_line.question_df.info()
    <class 'pandas.core.frame.DataFrame'>
    Int64Index: 8064 entries, 1 to 192
    Data columns (total 18 columns):
    L0                                   8064 non-null object
    L1                                   8064 non-null object
    L2                                   7308 non-null object
    L3                                   3444 non-null object
    L4                                   672 non-null object
    Section                              8064 non-null object
    ID                                   8064 non-null object
    ParentID                             8064 non-null object
    Key                                  8064 non-null object
    Title                                8064 non-null object
    Description                          6594 non-null object
    Datatype                             8064 non-null object
    Unit                                 8064 non-null object
    Decimals                             8064 non-null object
    Default                              8064 non-null object
    BedrijfstakkenBranchesSBI2008        8064 non-null object
    BedrijfstakkenBranchesSBI2008_Key    8064 non-null object
    Values                               8064 non-null int64
    dtypes: int64(1), object(17)
    memory usage: 1.2+ MB


    .. _OpenData:
        https://opendata.cbs.nl/statline/#/CBS/nl/dataset/84404NED/table?ts=1560412027927

    """

    def __init__(self, table_id,
                 reset: bool = False,
                 cache_dir_name: str = "cache",
                 image_dir_name: str = "images",
                 max_levels: int = 5,
                 to_sql: bool = False,
                 to_xls: bool = False,
                 to_pickle: bool = True,
                 write_questions_only: bool = False,
                 reset_pickles: bool = False,
                 units_key: str = "Unit",
                 key_key: str = "Key",
                 datatype_key: str = "Datatype",
                 id_key: str = "ID",
                 parent_id_key: str = "ParentID",
                 x_axis_key: str = None,
                 legend_title: str = None,
                 legend_position: tuple = None,
                 section_key: str = "Section",
                 title_key: str = "Title",
                 value_key: str = "Values",
                 modules_to_plot: list = None,
                 questions_to_plot: list = None,
                 plot_all_modules: bool = False,
                 plot_all_questions: bool = False,
                 apply_selection: bool = False,
                 selection: dict = None,
                 export_plot_data: bool = True,
                 image_type: str = ".png",
                 show_plot: bool = False,
                 save_plot: bool = False,
                 sort_choices: bool = False,
                 store_plot_data_to_xls: bool = False,
                 store_plot_data_to_tex: bool = False,
                 survey_title_properties: dict = None,
                 module_title_properties: dict = None,
                 question_title_properties: dict = None,
                 make_the_plots: bool = False,
                 describe_the_data: bool = False,
                 write_info_to_image_dir: bool = True,
                 rotate_latex_columns: bool = False,
                 color="blue",
                 fontsize=12,
                 ):
        """

        """

        self.table_id = table_id
        self.reset = reset
        self.max_levels = max_levels
        self.sort_choices = sort_choices
        self.rotate_latex_columns = rotate_latex_columns

        self.image_dir = Path(image_dir_name)
        self.image_dir.mkdir(exist_ok=True)
        self.image_dir = self.image_dir / Path(self.table_id)
        self.image_dir.mkdir(exist_ok=True)

        self.cache_dir = Path(cache_dir_name)
        self.cache_dir.mkdir(exist_ok=True)
        self.output_directory = self.cache_dir / Path(self.table_id)
        self.output_directory.mkdir(exist_ok=True)

        self.modules_to_plot = modules_to_plot
        self.questions_to_plot = questions_to_plot
        self.plot_all_modules = plot_all_modules
        self.plot_all_questions = plot_all_questions

        self.color = color
        self.fontsize = fontsize

        x_start = 0.02
        y_start = 0.97
        delta_y = 0.03
        if survey_title_properties is not None:
            self.survey_title_properties = survey_title_properties
        else:
            self.survey_title_properties = dict(loc=(x_start, y_start),
                                                color=self.color,
                                                size=self.fontsize)
        if module_title_properties is not None:
            self.module_title_properties = module_title_properties
        else:
            self.module_title_properties = dict(loc=(x_start, y_start - delta_y),
                                                color="blue", size=12)
        if question_title_properties is not None:
            self.question_title_properties = question_title_properties
        else:
            self.question_title_properties = dict(loc=(x_start, y_start - 2 * delta_y),
                                                  color="blue", size=12)

        self.apply_selection = apply_selection
        self.selection = selection
        # the selection_options will get the values we can select after the first plot
        self.selection_options = None

        self.export_plot_data = export_plot_data
        self.image_type = image_type
        self.show_plot = show_plot
        self.save_plot = save_plot
        self.store_plot_data_to_xls = store_plot_data_to_xls
        self.store_plot_data_to_tex = store_plot_data_to_tex

        self.connection = None

        self.typed_data_set = None
        self.table_infos = None
        self.data_properties = None
        self.dimensions = collections.OrderedDict()

        self.section_key = section_key
        self.title_key = title_key
        self.value_key = value_key
        self.units_key = units_key
        self.id_key = id_key
        self.parent_id_key = parent_id_key
        self.key_key = key_key
        self.datatype_key = datatype_key
        self.x_axis_key = x_axis_key

        self.question_df: pd.DataFrame = None
        self.section_df: pd.DataFrame = None
        self.dimension_df: pd.DataFrame = None
        self.level_keys = [f"L{d}" for d in range(self.max_levels)]
        self.level_ids: collections.OrderedDict = None

        # these data frames will cary the structure of the questionnaire
        self.module_info_df: pd.DataFrame = None
        self.question_info_df: pd.DataFrame = None

        self.pickle_files = dict()
        self.df_labels = ["question", "section", "dimensions"]
        for label in self.df_labels:
            file_name = "_".join([self.table_id, label]) + ".pkl"
            self.pickle_files[label] = self.cache_dir / Path(file_name)

        updated_dfs = False
        self.read_table_data()
        if self.pickle_files["question"].exists() and not (reset_pickles or self.reset):
            self.pkl_data(mode="read")
        else:
            self.initialize_dataframes()
            self.fill_question_list()
            self.fill_data()
            self.question_df.set_index(self.level_keys, inplace=True, drop=True)
            updated_dfs = True

        if x_axis_key is None:
            # no xlabel for the bar graph has been given. Take the first dimension
            self.x_axis_key = self.dimension_df.loc[0, self.key_key]
        else:
            self.x_axis_key = x_axis_key

        if legend_position is None:
            self.legend_position = (1.05, 0)
        else:
            self.legend_position = legend_position

        self.legend_title = legend_title

        if to_sql:
            self.write_sql_data(write_questions_only=write_questions_only)
        if to_xls:
            self.write_xls_data(write_questions_only=write_questions_only)
        if to_pickle and updated_dfs:
            self.pkl_data(mode="write")

        self.make_info_dataframes()
        if write_info_to_image_dir:
            self.write_info()

        if make_the_plots:
            self.plot()

        if describe_the_data:
            self.describe()

    def make_info_dataframes(self):
        """
        Make info data frames by taking the proper selections
        """
        col_sel = [self.key_key, self.title_key, self.units_key]
        self.question_info_df = self.question_df[col_sel].drop_duplicates()

        if not self.section_df.empty:
            col_sel = [self.parent_id_key, self.title_key]
            self.module_info_df = self.section_df[col_sel].drop_duplicates()

    def write_info(self):
        """
        Write some information to the image dir which makes it easier to analyse
        """

        table_infos_file = self.image_dir / Path("TableInfos.yml")
        logger.info(f"Writing table information to {table_infos_file}")
        with open(table_infos_file, "w") as stream:
            yaml.dump(self.table_infos, stream, default_flow_style=False)

        if tabulate is not None:
            question_info_file = self.image_dir / Path("QuestionTable.txt")
            logger.info(f"Writing question structure to {question_info_file}")
            with open(question_info_file, "w") as stream:
                stream.write(tabulate(self.question_info_df, headers="keys", tablefmt="psql"))

            section_info_file = self.image_dir / Path("SectionTable.txt")
            logger.info(f"Writing question structure to {section_info_file}")
            with open(section_info_file, "w") as stream:
                stream.write(tabulate(self.module_info_df, headers="keys", tablefmt="psql"))

    def pkl_data(self, mode="read"):
        """
        Write all the data to pickle

        Parameters
        ----------
        mode: {"read", "write")
            Option to control reading or writing
        """

        assert mode in ("read", "write")

        if mode == "read":
            action = "Reading from"
        else:
            action = "Writing to"

        for label, pkl_file in self.pickle_files.items():
            # write the result
            logger.info(f"{action} pickle database {pkl_file}")
            if mode == "read":
                if label == "question":
                    self.question_df = pd.read_pickle(pkl_file)
                elif label == "section":
                    self.section_df = pd.read_pickle(pkl_file)
                elif label == "dimensions":
                    self.dimension_df = pd.read_pickle(pkl_file)
                else:
                    raise AssertionError("label must be question, section, or dimension")
            else:
                if label == "question":
                    self.question_df.to_pickle(pkl_file)
                elif label == "section":
                    self.section_df.to_pickle(pkl_file)
                elif label == "dimensions":
                    self.dimension_df.to_pickle(pkl_file)
                else:
                    raise AssertionError("label must be question, section, or dimension")

    def write_xls_data(self, write_questions_only=True):

        """
        Write all the data to excel. Each table is written to a seperate sheet
        """
        xls = self.cache_dir / Path(self.table_id + ".xlsx")
        logger.info(f"Writing to excel database {xls}")
        with pd.ExcelWriter(xls) as stream:
            self.question_df.to_excel(stream, sheet_name="Questions", na_rep='NA')
            if not write_questions_only:
                self.section_df.to_excel(stream, sheet_name="Sections", na_rep='NA')
                self.dimension_df.to_excel(stream, sheet_name="Dimensions", na_rep='NA')

    def write_sql_data(self, write_questions_only=True):

        """
        Write all the data to the sql lite database. Each table is written in the same database
        """
        # write the result
        sqlite_db = self.cache_dir / "sqlite.db"
        self.connection = sqlite3.connect(sqlite_db)
        logger.info(f"Writing to sqlite database {sqlite_db}")
        self.question_df.to_sql("_".join([self.table_id, "question"]), self.connection,
                                if_exists="replace")
        if not write_questions_only:
            # also write the help dataframes
            self.section_df.to_sql("_".join([self.table_id, "section"]), self.connection,
                                   if_exists="replace")
            self.dimension_df.to_sql("_".join([self.table_id, "dimension"]), self.connection,
                                     if_exists="replace")

    def read_table_data(self):
        """
        Read the open data tables
        """

        type_data_set_file = self.output_directory / Path("TypedDataSet.json")
        table_infos_file = self.output_directory / Path("TableInfos.json")
        data_properties_file = self.output_directory / Path("DataProperties.json")

        if not data_properties_file.exists() or self.reset:
            logger.info(f"Importing table {self.table_id} and store to {self.output_directory}")
            # We cannot import the cbsodata module when using the debugger in PyCharm, therefore
            # only call import here
            from cbsodata import cbsodata3 as opendata
            try:
                opendata.get_data(self.table_id, dir=str(self.output_directory))
            except requests.exceptions.SSLError as err:
                logger.warning("Could not connect to opendata.cbs.nl. Check your connections")
                raise err

        # now we get the data from the json files which have been dumped by get_data
        logger.info(f"Reading json {data_properties_file}")
        with open(data_properties_file, "r") as stream:
            self.data_properties = json.load(stream)

        logger.info(f"Reading json {type_data_set_file}")
        with open(type_data_set_file, "r") as stream:
            self.typed_data_set = json.load(stream)
        logger.info(f"Reading json {table_infos_file}")
        with open(table_infos_file, "r") as stream:
            self.table_infos = json.load(stream)

    def initialize_dataframes(self):
        """
        Create empty data frame for the questions, sections and dimensions

        Notes
        -----
        * The json structure reflect the structure of the questionnaire , which has modules (L0),
          section (L1), subsection (L2), paragraphs (L3). In the json file these can be identified
          as GroupTopics.
        * In this script, the current level of the topics are kept track of, such that we can group
          items that belong to the same level
        """

        # level ids is going to contain the level id of the last seen level L0 (module),
        # section (L1), subsection (L2) and paragraph (L3)
        self.level_ids = collections.OrderedDict()
        level_labels = [f"L{level}" for level in range(self.max_levels)]
        for label in level_labels:
            # initialise all levels to None
            self.level_ids[label] = None

        # the questions dataframe will contain a column for each variable in the Topics + the label
        # for the levels + one extra column called 'Section' in which we store the multiline string
        # giving the Module/Section/Subsection/Paragraph
        question_columns = level_labels + ["Section"]
        section_columns = list()
        dimension_columns = list()
        n_dim = 0
        n_sec = 0
        n_quest = 0

        for indicator in self.data_properties:
            if indicator["Type"] == "TopicGroup":
                n_sec += 1
                keys = [_ for _ in list(indicator.keys()) if _ not in section_columns]
                section_columns.extend(keys)
            elif indicator["Type"] in ("Dimension", "TimeDimension"):
                n_dim += 1
                keys = [_ for _ in list(indicator.keys()) if _ not in dimension_columns]
                dimension_columns.extend(keys)
            else:
                n_quest += 1
                keys = [_ for _ in list(indicator.keys()) if _ not in question_columns]
                question_columns.extend(keys)

        # create all the data frames. The question_df contains the questions, the section_df
        # all the sections, and the dimensions all the dimensions
        self.question_df = pd.DataFrame(index=range(1, n_quest), columns=question_columns)
        self.section_df = pd.DataFrame(index=range(1, n_sec), columns=section_columns)
        self.dimension_df = pd.DataFrame(index=range(1, n_dim), columns=dimension_columns)

    def fill_question_list(self):
        """
        Turns the json data structures into a flat dataframe

        Notes
        -----
        * The questions are stored in modules, which again can be stored in sections and subsections
          This method keeps track of the level of the current question
        """

        # loop over all the data properties and store the questions, topic and dimensions
        for indicator in self.data_properties:
            data_props = DataProperties(indicator_dict=indicator)

            if data_props.parent_id is None:
                # if parent_id is None, we are entering a new module. Store the ID of this module
                # to L0 in levels _id
                logger.debug(f"Entering new module {data_props.title}")
                self.level_ids[self.level_keys[0]] = data_props.id
            else:
                # we have entered a module, so there is a parent. Store now the level of this
                # question
                found_parent = False
                for parent_level, (label, id) in enumerate(self.level_ids.items()):
                    # each topic has a field parent, which is the level to which the question
                    # belongs to. For instance, the first question belong to the module L0
                    # in case the parent_id as stored in this topic is equal to a previous stored
                    # level in the level_ids (id) it means that we have found the parent. Store
                    # this level to the higher level id (if the parent is in L0, the new level will
                    # be stored in L1 for instance)
                    this_level = parent_level + 1
                    if data_props.parent_id == id:
                        self.level_ids[self.level_keys[this_level]] = data_props.id
                        found_parent = True
                    elif found_parent and this_level < len(self.level_ids):
                        # we have found the parent, make sure that all the higher levels are set
                        # to None
                        self.level_ids[self.level_keys[this_level]] = None

            if data_props.type in ("Dimension", "TimeDimension"):
                # the current block is a dimension. Store it to the dimensions_df
                logger.debug(f"Reading dimension properties {data_props.key}")
                for key, value in indicator.items():
                    self.dimension_df.loc[data_props.id, key] = value
            elif data_props.type == "TopicGroup":
                # the current block is a TopicGroup (such as a Module or a Section. Store it to
                # the sections_df
                logger.debug(f"Reading topic group properties {data_props.key}")
                for key, value in indicator.items():
                    self.section_df.loc[data_props.id, key] = value
            else:
                # The current block mush be a question because it is not a dimension and not a
                # section

                # get the index in the question_df from the position property of this block
                index = int(data_props.position)

                # copy all the values from the current dict  to the data frame
                for key, value in indicator.items():
                    self.question_df.loc[index, key] = value

                section_title = None
                for level, level_id in self.level_ids.items():
                    self.question_df.loc[index, level] = level_id

        # we have looped over all the block. Clean up the dataframes

        # remove all empty rows and some unwanted columns
        self.question_df.dropna(axis=0, inplace=True, how="all")
        self.question_df.drop(["odata.type", "Type", "Position"], axis=1, inplace=True)
        self.dimension_df.dropna(axis=0, inplace=True, how="all")
        self.dimension_df.dropna(axis=1, inplace=True, how="all")

        # the dimensions dataframe contains the variables of the axis (such as 'Bedrijven'). Create
        # a column in the question_df dataframe per dimension
        for dimension_key in self.dimension_df[self.key_key]:
            self.question_df.loc[:, dimension_key] = None
            # the dimension name is retrieved here. Each dimension has its own json datafile which
            # contains more properties about this dimension, such as the Description. Read the
            # json data file here, such as e.g. 'Bedrijven.json' and store in the dimensions dict
            dimension_file = self.output_directory / Path(f"{dimension_key}.json")
            with open(dimension_file, "r") as stream:
                self.dimensions[dimension_key] = pd.DataFrame(
                    json.load(stream)).set_index(self.key_key)

        # the section df contains all the TopicGroups which we have encountered, such that we can
        # keep track of all the module and section titles. Clean the data frame here and set the
        # ID as an index
        self.section_df.dropna(axis=0, inplace=True, how="all")
        self.section_df.dropna(axis=1, inplace=True, how="all")
        if not self.section_df.empty:
            try:
                self.section_df.set_index("ID", inplace=True, drop=True)
            except KeyError:
                self.section_df = None
            else:
                try:
                    self.section_df.drop(["odata.type", "Type", "Key"], axis=1, inplace=True)
                except KeyError:
                    self.section_df = None

        # Based on the the level id which we have stored in the L0, L1, L2, L3 column we are going
        # to build a complete description of the module/section/subsection leading to the current
        # question
        level_labels = list(self.level_ids.keys())
        for index, row in self.question_df.iterrows():
            level_ids = row[level_labels]
            section_title = None
            for lev_id in level_ids.values:
                # loop over all the L0, L1, L2, L3 values stored in this row. In case that the
                # level is equal to the row ID, it means we are dealing with the current question
                # so we can stop
                if lev_id == row["ID"]:
                    break
                # If we passed this, it means we got a level L0, L1 which is referring to a module/
                # section title. Look up the title belong to the stored ID from the section df
                # and append it
                if section_title is None:
                    section_title = self.section_df.loc[lev_id, self.title_key]
                else:
                    section_title += "\n" + self.section_df.loc[lev_id, self.title_key]

            # we have build a whole module/section/subsection title for this question. Store it
            # to the Section column
            self.question_df.loc[index, self.section_key] = section_title

        # finally, we can drop any empty column in case we have any to make it cleaner
        self.question_df.dropna(axis=1, inplace=True, how="all")

        # we may of lost a level if the structure was not deep enough. Update the levels
        common_levels = self.question_df.columns.intersection(self.level_keys)
        missing_levels = set(self.level_keys).difference(set(common_levels))
        for level in list(missing_levels):
            self.level_keys.remove(level)
            del self.level_ids[level]
        self.max_levels = len(self.level_keys)

        logger.debug("Done reading data ")

    def fill_data(self):
        """

        Fill the question_df with the values found in the 'TypedDataSet'.

        Notes
        -----
        * We must have a questions_df filled by 'fill_question_list' already. Now
        * We loop over all the dimensions and store a new data frame for each dimension value.
        """

        df_list = list()
        for typed_data_set in self.typed_data_set:

            # loop over all the variables of the current block (belonging to one dimension value,
            # such as 'Bedrijven van 10 en groter'
            values = list()
            for key, data in typed_data_set.items():
                if key == "ID":
                    # the first value is always an ID, Make a copy of the question dataframe to
                    # a new data frame which we can fill with values for this dimension
                    logger.debug(f"Collecting data of {data}")
                    df = self.question_df.copy()
                elif key in list(self.dimensions.keys()):
                    # the next rows contain dimension properties. Get the values and store those
                    # in the dimension column of are question dataframe. Store both the Title
                    # and the short key
                    df.loc[:, key] = self.dimensions[key].loc[data, self.title_key]
                    df.loc[:, key + "_" + self.key_key] = data
                else:
                    # the rest of the rows in this block are the values belonging to the questions
                    # store them in a list
                    values.append(data)

            # now copy the whole list of values to our question data frame and add them to a list
            df.loc[:, self.value_key] = values
            df_list.append(df)

        # we have create a dataframe for each dimension. Now append all the data frames to one
        # big one
        logger.info("Merging all the dataframes")
        self.question_df = pd.concat(df_list, axis=0)

    def describe(self):
        """
        Show some information of  the question dataframe
        """

        if self.question_df is not None:
            logger.info("\n{}".format(self.question_df.info()))
        else:
            logger.info("Data frame with question is empty")

        logger.info(f"x axis key: {self.x_axis_key}")
        unique_x_values = self.question_df[self.x_axis_key].unique()
        logger.info("Unique x-labels\n{}".format(unique_x_values))

        for module_id, module_df in self.question_df.groupby(level=0):
            section_title = module_df[self.section_key].values[0]
            logger.info(f"module {module_id}: {section_title}")

            reported = list()
            for level_id, level_df in module_df.groupby(level=1):

                if level_id not in reported:
                    # report the questions in this module
                    logger.debug("Available questions in {}".format(level_id))
                    logger.debug("\n{}".format(level_df[self.key_key].drop_duplicates()))
                    reported.append(level_id)

    def show_question_table(self, max_width=None):
        """ Make a nice print of all questions """
        if tabulate is not None:
            if max_width is not None:
                df = dataframe_clip_strings(self.question_info_df.copy(), max_width)
            else:
                df = self.question_info_df
            df_table = tabulate(df, headers="keys", tablefmt="psql")
            logger.info("Structure of all questions\n{}".format(df_table))
        else:
            logger.info("Structure of all questions\n{}".format(self.question_info_df))

        return df_table

    def show_module_table(self, max_width=None):
        """
        Make a nice print of all modules
        """

        if tabulate is not None:
            if max_width is not None:
                df = dataframe_clip_strings(self.module_info_df.copy(), max_width)
            else:
                df = self.module_info_df
            df_table = tabulate(df, headers="keys", tablefmt="psql")
            logger.info("Structure of all modules\n{}".format(df_table))
        else:
            logger.info("Structure of all modules\n{}".format(self.module_info_df))

        return df_table

    def show_selection(self):
        """
        Show the index of the data frame
        """

        if self.selection_options is not None:
            logger.info("You can make a selection from the following values\n{}"
                        "".format(self.selection_options))
        else:
            logger.info("The available index are stored after the first plot")

        return self.selection_options

    def get_question_df(self, question_id: int):
        """
        Get the question belonging to the id *question_id*

        Parameters
        ----------
        question_id: int
            Id of the question you want to get

        Returns
        -------
        pd.DataFrame
            The dataframe of the question you want to get

        Notes
        -----
        * The question id is not in a fixed column as it depends on the depth of the current level.
          Therefore, the levels are scanned until we got the question

        """
        df_list = None
        for module_id, module_df in self.question_df.groupby(level=0):
            for level_id, level_df in module_df.groupby(level=1):
                if level_id != question_id:
                    continue
                sub_level_df = self._remove_all_section_levels(level_df)
                is_question = self._has_equal_number_of_nans(level_id, sub_level_df=sub_level_df)
                df_list = list()
                if not is_question:
                    # the block we have is not a question, because the is an unequal amount of nans
                    # in the index. Loop over the blocks and call this function again with the
                    # subsubblocks
                    logger.debug(f"looping over all levels  for {level_id}")
                    try:
                        for id, df in sub_level_df.groupby(level=1):
                            logger.debug(f"Recursive call for {level_id}: {id}")
                            df_list.append(self.get_question_df(id, df))
                    except ValueError:
                        logger.debug(f"Failed getting next level for {level_id}: {id}")
                else:
                    df_list.append(sub_level_df)

        if df_list is None:
            logger.warning(f"Could not find any question belonging to {question_id}. Please check ")
            result_df = None
        elif len(df_list) == 1:
            # if we have only on match, do not return as a list but a a dataframe
            result_df = df_list[0]
        else:
            result_df = df_list

        return result_df

    @staticmethod
    def close_plots():
        plt.close("all")

    def plot(self):
        """
        Loop over all the modules and plot all questions per module
        """
        if isinstance(self.modules_to_plot, int):
            # turn modules_to_plot into a list if only a integer was given
            self.modules_to_plot = [self.modules_to_plot]

        for module_id, module_df in self.question_df.groupby(level=0):

            if self.modules_to_plot is not None:
                if module_id not in self.modules_to_plot and not self.plot_all_modules:
                    logger.debug(f"Skipping module {module_id}")
                    continue

            logger.info(f"Processing module {module_id}:")

            reported = list()
            for level_id, level_df in module_df.groupby(level=1):

                if level_id not in reported:
                    # report the questions in this module
                    logger.debug("Available questions in {}".format(level_id))
                    logger.debug("\n{}".format(level_df[self.key_key].drop_duplicates()))
                    reported.append(level_id)

                self._plot_module_questions(level_id=level_id, level_df=level_df)

    @staticmethod
    def _remove_all_section_levels(level_df):
        """
        Remove all the levels from *level_df* that belong to a section

        Returns
        -------
        pd.DataFrame
            Dataframe with all section levels removed

        Notes
        -----
        the dataframe has a multiindex based on the level of the question L0, L1, L2. The
        first level always applies to the module, so we can drop it here. Then, there more be
        section levels we we may also drop. We can see that by looking at the next level: if that
        has at least a nan, the current level can not be a section and we can continue. Otherwise
        we drop the current level too
        """

        try:
            # for pandas version >= 0.24.0
            sub_level_df = level_df.droplevel(0)
        except AttributeError:
            # for pandas version < 0.24.0
            sub_level_df = level_df.copy()
            sub_level_df.index = level_df.index.droplevel(level=0)

        while True:
            try:
                if sub_level_df.index.get_level_values(1).isnull().any():
                    break
            except IndexError:
                break
            else:
                # we have found only valid values at the next level, so we can drop the current one
                # because it belongs to a section
                try:
                    sub_level_df = sub_level_df.droplevel(0)
                except AttributeError:
                    sub_level_df.index = sub_level_df.index.droplevel(level=0)

        return sub_level_df

    @staticmethod
    def _has_equal_number_of_nans(level_id, sub_level_df):

        equal_number = False
        last_number = None
        for index, row in sub_level_df.iterrows():
            try:
                # count number of nans in de index of the current row
                number_of_nan = sum([math.isnan(x) for x in index])
            except TypeError:
                return equal_number
            if last_number is not None and number_of_nan != last_number:
                logger.debug("Need to go one level deeper")
                return equal_number

            last_number = number_of_nan

        equal_number = True

        return equal_number

    def question_or_its_parent_in_index(self, level_df):
        """
        Check if a question or any of the parent is in de index.

        Return
        ------
        bool:
            True in case a question of its parents is in de inex
        """
        if isinstance(self.questions_to_plot, int):
            # if the questions_to_plot is given as a single int, make it a list
            self.questions_to_plot = [self.questions_to_plot]
        in_index = False
        for question_index in level_df.index.values:
            if set(question_index).intersection(set(self.questions_to_plot)):
                in_index = True
                break
        return in_index

    def _plot_module_questions(self, level_id: int, level_df: pd.DataFrame):
        """
        Plot the questions of a module

        Parameters
        ----------
        level_id: int
            The id number of a module
        level_df: pd.DataFrame
            A pandas dataframe of the current module questions
        """

        if self.questions_to_plot is not None and not self.plot_all_questions:
            plot_question = self.question_or_its_parent_in_index(level_df)
            if not plot_question:
                logger.debug(f"Skipping question {level_id}")
                return

        logger.debug(f"Question {level_id}")

        sub_level_df = self._remove_all_section_levels(level_df)

        is_question = self._has_equal_number_of_nans(level_id, sub_level_df=sub_level_df)

        if not is_question:
            # the block we have is not a question, because the is an unequal amount of nans in the
            # index. Loop over the blocks and call this fucntion again with the subsubblocks
            logger.debug(f"looping over all levels  for {level_id}")
            try:
                for id, df in sub_level_df.groupby(level=1):
                    logger.debug(f"Calling plot for {level_id}: {id}")
                    self._plot_module_questions(id, df)
            except ValueError:
                logger.debug(f"Failed getting next level for {level_id}: {id}")
            finally:
                return

        logger.debug("Making plot")

        self.make_the_plot(sub_level_df=sub_level_df)

    def prepare_data_frame(self, sub_level_df):

        datatype = sub_level_df[self.datatype_key].values[0]

        if datatype == "Integer":
            # make sure that integers are printed as integers
            sub_level_df.loc[:, self.value_key] = sub_level_df[self.value_key].astype(int).values

        # we have to create a dataframe with the questions on the indices and all the values
        # per size class in the columns.
        sub_level_df.reset_index(inplace=True)
        sub_level_df.set_index([self.title_key, self.x_axis_key], drop=True, inplace=True)
        sub_level_df = sub_level_df[self.value_key]

        # keep the original order of the size classes, as unstack is going to sorted
        # alphabetically, which is not correct.
        sorted_index_0 = sub_level_df.index.get_level_values(0).unique()
        sorted_index_1 = sub_level_df.index.get_level_values(1).unique()
        self.selection_options = sorted_index_1

        if self.apply_selection:
            # in case the apply selection flag is true, we don't use all items in a group but take
            # a selection defined the selection secions
            logger.debug("Selecting from\n{}".format(sorted_index_1))
            if isinstance(self.selection, list):
                sorted_index_1 = sorted_index_1.intersection(set(self.selection))
            elif isinstance(self.selection, dict):
                sorted_index_1 = sorted_index_1.intersection(set(self.selection.values()))
            else:
                raise AssertionError("selection should either be a list or a dict")

        logger.debug("\n{}".format(sorted_index_1.values))

        # for a proper bar plot, we need to unstack the dataframe
        try:

            sub_level_df = sub_level_df.unstack()
        except ValueError as err:
            logger.error(err)
        else:
            # reset the size class order in the columns
            sub_level_df = sub_level_df[sorted_index_1.values]

            # also restore the order of the index values which was sorted by unstack
            if not self.sort_choices:
                sub_level_df = sub_level_df.reindex(sorted_index_0.values)

        return sub_level_df

    def make_the_plot(self, sub_level_df):
        """
        Plot the data stored in the *sub_level_df* Dataframe

        Parameters
        ----------
        sub_level_df: pd.Dataframe
            Dataframe containing the data to plot

        """

        key = sub_level_df[self.key_key].values[0]
        units = sub_level_df[self.units_key].values[0]
        section_title = sub_level_df[self.section_key].values[0]
        splitted = section_title.split("\n")
        if len(splitted) > 1:
            module_title = splitted[0]
            question_title = " ".join(splitted[1:])
        else:
            module_title = section_title
            question_title = None

        survey_title = self.table_infos[0]["ShortTitle"]

        sub_level_df = self.prepare_data_frame(sub_level_df=sub_level_df)

        fig, axis = plt.subplots(nrows=1, ncols=1, figsize=(10, 6))
        fig.subplots_adjust(left=0.4, right=0.7)

        sub_level_df.plot(kind="barh", ax=axis)

        axis.set_xlabel(units)
        axis.invert_yaxis()
        if question_title is None:
            question_title = sub_level_df.index.values[0]
            axis.get_yaxis().set_visible(False)
        else:
            axis.set_ylabel("")

        patches, labels = axis.get_legend_handles_labels()
        if isinstance(self.selection, dict):
            inv_map = {v: k for k, v in self.selection.items()}
            new_labels = list()
            for label in labels:
                try:
                    new_labels.append(inv_map[label])
                except KeyError:
                    new_labels.append(label)
            labels = new_labels

        if self.legend_title is not None:
            legend_title = self.legend_title
        else:
            legend_title = self.x_axis_key

        axis.legend(patches, labels, loc="lower left", bbox_to_anchor=self.legend_position,
                    title=legend_title)

        def add_figtext(title, properties):
            location = properties["loc"]
            color = properties.get("color")
            plt.figtext(location[0], location[1], title, color=color)

        add_figtext(survey_title, self.survey_title_properties)
        add_figtext(module_title, self.module_title_properties)
        add_figtext(question_title, self.question_title_properties)

        # plt.title(df["Title"].values[0])

        if self.apply_selection:
            suffix = "sel"
        else:
            suffix = "all"
        file_base = "_".join([self.table_id,
                              re.sub("\s+", "_", module_title).lower(),
                              re.sub("\s+", "_", question_title).lower(),
                              suffix])
        file_base = re.sub("[()/]", "", file_base)
        file_name = Path(file_base + self.image_type)
        image_name = self.image_dir / file_name

        if self.save_plot:
            logger.info(f"Saving image to {image_name}")
            plt.savefig(image_name)
        if self.show_plot:
            plt.ioff()
            plt.show()

        if self.store_plot_data_to_xls:
            xls_file = Path(file_base + ".xlsx")
            xls_file = self.image_dir / xls_file
            logger.info(f"Saving plot data to {xls_file}")
            with pd.ExcelWriter(xls_file) as writer:
                sub_level_df.to_excel(writer, sheet_name=self.x_axis_key)

        if self.store_plot_data_to_tex:
            tex_file = Path(file_base + ".tex")
            tex_file = self.image_dir / tex_file

            logger.info(f"Saving plot data to {tex_file}")

            # for latex we transpose the matrix
            sub_level_df = sub_level_df.T

            if self.rotate_latex_columns:
                # in order to have the \rot command to work, add the following in the preamble

                # \newcolumntype {R}[2] { %
                #   > {\adjustbox {angle =  # 1,lap=\width-(#2)}\bgroup}%
                #   l %
                #   < {\egroup} %
                #   }
                #   \newcommand *\rot {\multicolumn {1} {R {45} {1 em}}}

                rotated_columns = dict()
                for col_name in sub_level_df.columns:
                    rotated_columns[col_name] = r"\rot{" + col_name + r"}"
                sub_level_df.rename(columns=rotated_columns, inplace=True)

            sub_level_df.to_latex(tex_file, longtable=False, decimal=",")
            if self.rotate_latex_columns:
                with open(tex_file, "r") as fp:
                    text = fp.read()
                new_tex = text.replace("\\textbackslash rot\\{", "\\rot{")
                new_tex = new_tex.replace("\\}", r"}")
                with open(tex_file, "w") as fp:
                    fp.write(new_tex)


def dataframe_clip_strings(df, max_width, include=None, exclude=None):
    """
    Clip all strings in a dataframe

    Parameters
    ----------
    df: DataFrame
        Pandas data frame
    max_width: int
        Clip strings to this width
    include: list, optional
        give a list of column names to clip. Exclude the rest
    include: list, optional
        give a list of column names not to clip. Include the rest

    Returns
    -------
    Pandas data frame with clip string columns

    """
    for cn in df.columns:
        if include is not None and cn not in include:
            continue
        if exclude is not None and cn in exclude:
            continue
        try:
            df[cn] = [vv[:min(max_width, len(vv))] for vv in df[cn].values if vv is not None]
        except TypeError:
            pass

    return df
