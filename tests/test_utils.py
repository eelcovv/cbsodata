import os
import shutil
import logging
import pandas as pd
from pandas.testing import assert_frame_equal
import pickle
import string
import random

from cbsodata.utils import StatLineTable, dataframe_clip_strings

# testing deps
import pytest

logging.basicConfig(format='%(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger()

DATASETS = [
     '84410NED',
     '82010NED',
     '80884ENG'
    ]
DATASETS_DERDEN = [
    '47003NED',
    '47005NED'
]

DATA_DIR = 'data'  # this directory should be keps in the repository, it is used to validate
TEST_ENV = 'test_env'  # this directory is cleared after running
COMPRESSION = "zip"


def table_file_name(table_id, base_name="question_df", data_format=".pkl"):
    return os.path.join(DATA_DIR, "_".join([base_name, table_id])) + data_format


def write_data():
    """ Write test data frames which we can use to validate"""

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    for table_id in DATASETS:
        statline = StatLineTable(table_id=table_id, cache_dir_name=TEST_ENV,
                                 image_dir_name=TEST_ENV)
        question_df = statline.question_df

        file_name = table_file_name(table_id=table_id)
        logger.info("Writing test data frame {}".format(file_name))
        question_df.to_pickle(file_name, compression=COMPRESSION)

        file_name = table_file_name(table_id=table_id, base_name="question_info")
        question_info = statline.show_question_table()
        logger.info("Writing question table {}".format(file_name))
        with open(file_name, "wb") as fp:
            pickle.dump(question_info, fp)

        file_name = table_file_name(table_id=table_id, base_name="module_table")
        module_table = statline.show_module_table()
        logger.info("Writing modules table {}".format(file_name))
        with open(file_name, "wb") as fp:
            pickle.dump(module_table, fp)

        file_name = table_file_name(table_id=table_id, base_name="selection")
        selection = statline.show_selection()
        logger.info("Writing modules table {}".format(file_name))
        with open(file_name, "wb") as fp:
            pickle.dump(selection, fp)


def setup_module(module):
    print('\nsetup_module()')

    if not os.path.exists(TEST_ENV):
        os.makedirs(TEST_ENV)


def teardown_module(module):
    print('teardown_module()')

    shutil.rmtree(TEST_ENV)


# Tests


@pytest.mark.parametrize("table_id", DATASETS)
def test_question_df(table_id):
    # testing
    statline = StatLineTable(table_id=table_id, cache_dir_name=TEST_ENV, image_dir_name=TEST_ENV)
    question_df = statline.question_df

    file_name = table_file_name(table_id=table_id)
    question_df_expect = pd.read_pickle(file_name, compression=COMPRESSION)

    assert_frame_equal(question_df, question_df_expect)


@pytest.mark.parametrize("table_id", DATASETS)
def test_question_info(table_id):
    # testing
    statline = StatLineTable(table_id=table_id, cache_dir_name=TEST_ENV, image_dir_name=TEST_ENV)
    question_info = statline.show_question_table()

    file_name = table_file_name(table_id=table_id, base_name="question_info")
    with open(file_name, "rb") as fp:
        question_info_expect = pickle.load(fp)

    assert question_info == question_info_expect


@pytest.mark.parametrize("table_id", DATASETS)
def test_module_info(table_id):
    # testing
    statline = StatLineTable(table_id=table_id, cache_dir_name=TEST_ENV, image_dir_name=TEST_ENV)
    question_info = statline.show_module_table()

    file_name = table_file_name(table_id=table_id, base_name="module_table")
    with open(file_name, "rb") as fp:
        question_info_expect = pickle.load(fp)

    assert question_info == question_info_expect


@pytest.mark.parametrize("table_id", DATASETS)
def test_selection(table_id):
    # testing
    statline = StatLineTable(table_id=table_id, cache_dir_name=TEST_ENV, image_dir_name=TEST_ENV)
    selection = statline.show_selection()

    file_name = table_file_name(table_id=table_id, base_name="selection")
    with open(file_name, "rb") as fp:
        selection_expect = pickle.load(fp)

    assert selection == selection_expect


def test_clip_data_frame_strings():
    string_length = 10

    df_in = pd.DataFrame(index=range(5), columns=list(string.ascii_uppercase[:4]))

    random.seed(0)

    def random_name(size=32, chars=string.ascii_lowercase):
        return "".join(random.choice(chars) for _ in range(size))

    for col_name in df_in.columns:
        df_in[col_name] = [random_name(size=string_length) for _ in df_in.index]

    df_clipped = dataframe_clip_strings(df_in, max_width=5)

    df_expect = pd.DataFrame(index=range(5), columns=list(string.ascii_uppercase[:4]),
                             data=[["mynbi", "racxm", "zmksh", "sukgh"],
                                   ["plsgq", "tpkhx", "tvipc", "hlzfk"],
                                   ["tzirw", "hhzez", "bcwrv", "whbsu"],
                                   ["xcvkp", "qpdjr", "zhgvs", "dugts"],
                                   ["tugrp", "rgztr", "vuwzl", "btagf"]])

    assert_frame_equal(df_clipped, df_expect)


def main():
    write_data()


if __name__ == "__main__":
    main()
