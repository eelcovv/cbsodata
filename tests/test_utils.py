import os
import shutil

import requests

from cbsodata.utils import StatLineTable, dataframe_clip_strings

# testing deps
import pytest


datasets = [
    '84410NED'
]

datasets_derden = [
]

TEST_ENV = 'test_env'


def setup_module(module):
    print('\nsetup_module()')

    if not os.path.exists(TEST_ENV):
        os.makedirs(TEST_ENV)


def teardown_module(module):
    print('teardown_module()')

    shutil.rmtree(TEST_ENV)

# Tests


@pytest.mark.parametrize("table_id", datasets)
def test_info(table_id):

    # testing
    statline = StatLineTable(table_id=table_id)

    assert True
