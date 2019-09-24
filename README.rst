Statistics Netherlands opendata API client for Python
=====================================================

|pypi| |travis|

.. |pypi| image:: https://badge.fury.io/py/cbsodata.svg
    :target: https://badge.fury.io/py/cbsodata

.. |travis| image:: https://travis-ci.org/J535D165/cbsodata.svg?branch=master
    :target: https://travis-ci.org/J535D165/cbsodata

Retrieve data from the `open data interface of Statistics Netherlands
<http://www.cbs.nl/nl-NL/menu/cijfers/statline/open-data/default.htm>`__
(Centraal Bureau voor de Statistiek) with *Python*. The data is identical in
content to the tables which can be retrieved and downloaded from `StatLine
<http://statline.cbs.nl/>`__. CBS datasets are accessed via the `CBS open data
portal <https://opendata.cbs.nl/statline/portal.html>`__.

The documentation of this
package is found at this page and on `readthedocs.io
<http://cbsodata.readthedocs.io/>`__.

R user? Use `cbsodataR <https://cran.r-project.org/web/packages/cbsodataR/index.html>`__.

Installation
------------

From PyPi

.. code:: sh

    pip install cbsodata

Usage
-----

Load the package with

.. code:: python

    >>> import cbsodata

Tables
~~~~~~

Statistics Netherlands (CBS) has a large amount of public available
data tables (more than 4000 at the moment of writing). Each table is
identified  by a unique identifier (``Identifier``).

.. code:: python

    >>> tables = cbsodata.get_table_list()
    >>> print(tables[0])
    {'Catalog': 'CBS',
     'ColumnCount': 18,
     'DefaultPresentation': '_la=nl&_si=&_gu=&_ed=LandVanUiteindelijkeZeggenschapUCI&_td=Perioden&graphType=line',
     'DefaultSelection': "$filter=((LandVanUiteindelijkeZeggenschapUCI eq '11111') or (LandVanUiteindelijkeZeggenschapUCI eq '22222')) and (Bedrijfsgrootte eq '10000') and (substringof('JJ',Perioden))&$select=LandVanUiteindelijkeZeggenschapUCI, Bedrijfsgrootte, Perioden, FiscaalJaarloonPerBaan_15",
     'ExplanatoryText': '',
     'Frequency': 'Perjaar',
     'GraphTypes': 'Table,Bar,Line',
     'ID': 0,
     'Identifier': '82010NED',
     'Language': 'nl',
     'MetaDataModified': '2014-02-04T02:00:00',
     'Modified': '2014-02-04T02:00:00',
     'OutputStatus': 'Regulier',
     'Period': '2008 t/m 2011',
     'ReasonDelivery': 'Actualisering',
     'RecordCount': 32,
     'SearchPriority': '2',
     'ShortDescription': '\nDeze tabel bevat informatie over banen en lonen bij bedrijven in Nederland, uitgesplitst naar het land van uiteindelijke zeggenschap van die bedrijven. Hierbij wordt onderscheid gemaakt tussen bedrijven onder Nederlandse zeggenschap en bedrijven onder buitenlandse zeggenschap. In de tabel zijn alleen de bedrijven met werknemers in loondienst meegenomen. De cijfers hebben betrekking op het totale aantal banen bij deze bedrijven en de samenstelling van die banen naar kenmerken van de werknemers (baanstatus, geslacht, leeftijd, herkomst en hoogte van het loon). Ook het gemiddelde fiscale jaarloon per baan is in de tabel te vinden. \n\nGegevens beschikbaar vanaf: 2008 \n\nStatus van de cijfers: \nDe cijfers in deze tabel zijn definitief.\n\nWijzigingen per 4 februari 2014\nDe cijfers van 2011 zijn toegevoegd.\n\nWanneer komen er nieuwe cijfers?\nDe cijfers over 2012 verschijnen in de eerste helft van 2015.\n',
     'ShortTitle': 'Zeggenschap bedrijven; banen, grootte',
     'Source': 'CBS.',
     'Summary': 'Banen en lonen van werknemers bij bedrijven in Nederland\nnaar land van uiteindelijke zeggenschap en bedrijfsgrootte',
     'SummaryAndLinks': 'Banen en lonen van werknemers bij bedrijven in Nederland<br />naar land van uiteindelijke zeggenschap en bedrijfsgrootte<br /><a href="http://opendata.cbs.nl/ODataApi/OData/82010NED">http://opendata.cbs.nl/ODataApi/OData/82010NED</a><br /><a href="http://opendata.cbs.nl/ODataFeed/OData/82010NED">http://opendata.cbs.nl/ODataFeed/OData/82010NED</a>',
     'Title': 'Zeggenschap bedrijven in Nederland; banen en lonen, bedrijfsgrootte',
     'Updated': '2014-02-04T02:00:00'}

Info
~~~~

Get information about a table with the ``get_info`` function.

.. code:: python

    >>> info = cbsodata.get_info('82070ENG') # Returns a dict with info
    >>> info['Title']
    'Caribbean Netherlands; employed labour force characteristics 2012'
    >>> info['Modified']
    '2013-11-28T15:00:00'

Data
~~~~

The function you are looking for!! The function ``get_data`` returns a list of
dicts with the table data.

.. code:: python

    >>> data = cbsodata.get_data('82070ENG')
    [{'CaribbeanNetherlands': 'Bonaire',
      'EmployedLabourForceInternatDef_1': 8837,
      'EmployedLabourForceNationalDef_2': 8559,
      'Gender': 'Total male and female',
      'ID': 0,
      'Periods': '2012',
      'PersonalCharacteristics': 'Total personal characteristics'},
     {'CaribbeanNetherlands': 'St. Eustatius',
      'EmployedLabourForceInternatDef_1': 2099,
      'EmployedLabourForceNationalDef_2': 1940,
      'Gender': 'Total male and female',
      'ID': 1,
      'Periods': '2012',
      'PersonalCharacteristics': 'Total personal characteristics'},
     {'CaribbeanNetherlands': 'Saba',
      'EmployedLabourForceInternatDef_1': 1045,
      'EmployedLabourForceNationalDef_2': 971,
      'Gender': 'Total male and female',
      'ID': 2,
      'Periods': '2012',
      'PersonalCharacteristics': 'Total personal characteristics'},
     # ...
    ]

The keyword argument ``dir`` can be used to download the data directly to your
file system.

.. code:: python

    >>> data = cbsodata.get_data('82070ENG', dir="dir_to_save_data")

Catalogs (dataderden)
~~~~~~~~~~~~~~~~~~~~~

There are multiple ways to retrieve data from catalogs other than
'opendata.cbs.nl'. The code below shows 3 different ways to retrieve data from
the catalog 'dataderden.cbs.nl' (known from Iv3).

On module level.

.. code:: python

   cbsodata.options.catalog_url = 'dataderden.cbs.nl'
   # list tables
   cbsodata.get_table_list()
   # get dataset 47003NED
   cbsodata.get_data('47003NED')

With context managers.

.. code:: python

   with cbsodata.catalog('dataderden.cbs.nl'):
       # list tables
       cbsodata.get_table_list()
       # get dataset 47003NED
       cbsodata.get_data('47003NED')

As a function argument.

.. code:: python

   # list tables
   cbsodata.get_table_list(catalog_url='dataderden.cbs.nl')
   # get dataset 47003NED
   cbsodata.get_data('47003NED', catalog_url='dataderden.cbs.nl')

Pandas users
~~~~~~~~~~~~

The package works well with Pandas. Convert the result easily into a pandas
DataFrame with the code below.

.. code:: python

    >>> data = pandas.DataFrame(cbsodata.get_data('82070ENG'))
    >>> data.head()


.. code:: python

    >>> tables = pandas.DataFrame(cbsodata.get_table_list())
    >>> tables.head()

This will put use a list of values for all variables in one flat dataframe. The
structure of the statline data is lost.

StatLineTable
~~~~~~~~~~~~~

Starting from *cbsodata* version 1.3, we also have to ability to get a
selection of variables belonging to one question. Also, the units and dimensions can
now easily be retrieved. This is done by using the new *StatLineTable* class


Let's start with showing how to import the data from a table:

.. code:: python

    >>> from cbsodata.utils import StatLineTable
    >>> stat_line = StatLineTable(table_id="84410NED")

This loads the statline data from the survey 'ICT-usage of companies for varying
company size class'. The StatLine table can be found here:  OpenDATAICT_

A typical statline table is organised into 'modules' (questions belonging to one topic),
'submodules', and questions. One question can again contain several options. We can inspect
the structure of the survey as follows:

.. code:: python

    >>> stat_line.show_module_table(max_rows=18)

This will print the first 18 rows of the questionnaire structure::

    +------+------------+----------------------------------------+
    |   ID |   ParentID | Title                                  |
    |------+------------+----------------------------------------|
    |    1 |            | Personeel en ICT                       |
    |    4 |          1 | ICT-specialisten                       |
    |    9 |          1 | ICT-beveiliging/bescherming data       |
    |   13 |            | Toegang en gebruik internet            |
    |   14 |         13 | Bedrijven met website                  |
    |   16 |         14 | Website bevat                          |
    |   23 |            | Cloud-diensten                         |
    |   25 |         23 | Type cloud-diensten                    |
    |   33 |         25 | Type server                            |
    |   36 |            | Big-data-analyse                       |
    |   38 |         36 | Bronnen big data voor analyse          |
    |   43 |         36 | Wie analyseerde big data               |
    |   46 |            | ICT-veiligheid                         |
    |   47 |         46 | Gebruikte ICT-veiligheidsmaatregelen   |
    |   60 |         46 | Optreden van ICT veiligheidsincidenten |
    |   65 |         46 | Oorzaken van ICT veiligheidsincidenten |
    |   72 |         46 | Kosten ICT-veiligheidsincidenten       |
    |   79 |         46 | Uitvoeren updates (security patching)  |
    +------+------------+----------------------------------------+

This table contains ICT-usage of company for varying company size class. In case you want
to inspect which size classes are availeble you can do

.. code:: python

    >>> stat_line.show_selection()

This gives the following output::

    Index(['2 of meer werkzame personen', '2 tot 250 werkzame personen',
           '2 werkzame personen', '3 tot 5 werkzame personen',
           '5 tot 10 werkzame personen', '10 tot 20 werkzame personen',
           '20 tot 50 werkzame personen', '50 tot 100 werkzame personen',
           '100 tot 250 werkzame personen', '250 tot 500 werkzame personen',
           '500 of meer werkzame personen'],
          dtype='object', name='Bedrijfsgrootte')

Selecting only the *2* and *3-5* size class  can be done as

.. code:: python

    >>> stat_line.selection = ['2 werkzame personen', '3 tot 5 werkzame personen']
    >>> stat_line.apply_selection = True

We are now ready to retrieve all the data belonging to the question
'Gebruikte ICT-veiligheidsmaatregelen' for the two size classes selected. Let's
get the data::

.. code:: python

    >>> question_df = stat_line.get_question_df(47)
    >>> question_df = stat_line.prepare_data_frame(question_df)

The pandas data *question_df* now looks like this::

    +------------------------------------------+-----------------------+-----------------------------+
    | Title                                    |   2 werkzame personen |   3 tot 5 werkzame personen |
    |------------------------------------------+-----------------------+-----------------------------|
    | Antivirussoftware                        |                    82 |                          86 |
    | Beleid voor sterke wachtwoorden          |                    56 |                          60 |
    | Authenticatie via soft of hardware-token |                    24 |                          29 |
    | Encryptie voor het opslaan van data      |                    19 |                          24 |
    | Encryptie voor het versturen van data    |                    20 |                          25 |
    | Gegevens op andere fysieke locatie       |                    57 |                          66 |
    | Network access control                   |                    22 |                          34 |
    | VPN bij internetgebruik buiten het eigen |                    19 |                          28 |
    | Logbestanden voor analyse incidenten     |                    20 |                          27 |
    | Methodes voor beoordelen ITC-veiligheid  |                    14 |                          21 |
    | Risicoanalyses                           |                    15 |                          21 |
    | Andere maatregelen                       |                     9 |                          13 |
    +------------------------------------------+-----------------------+-----------------------------+


You can plot it with the normal pandas plotting method. The whole series of commands
to make the plot looks like this:

.. plot:: ../examples/plot_bars.py
    :include-source:


.. _OpenDATAICT:
    https://opendata.cbs.nl/statline/#/CBS/nl/dataset/84410NED/table?ts=1560412027927


Command Line Interface
----------------------

This library ships with a Command Line Interface (CLI).

.. code:: bash

    > cbsodata -h
    usage: cbsodata [-h] [--version] [subcommand]

    CBS Open Data: Command Line Interface

    positional arguments:
      subcommand  the subcommand (one of 'data', 'info', 'list')

    optional arguments:
      -h, --help  show this help message and exit
      --version   show the package version

Download data:

.. code:: bash

    > cbsodata data 82010NED

Retrieve table information:

.. code:: bash

    > cbsodata info 82010NED

Retrieve a list with all tables:

.. code:: bash

    > cbsodata list


Export data
~~~~~~~~~~~

Use the flag ``-o`` to load data to a file (JSON lines).

.. code:: bash

    > cbsodata data 82010NED -o table_82010NED.jl
