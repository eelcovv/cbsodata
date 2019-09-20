import os
import shutil

import requests

from cbsodata import cbsodata3 as opendata

# testing deps
import pytest


datasets = [
    '82010NED',
    '80884ENG'
]

datasets_derden = [
    '47003NED',
    '47005NED'
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
    info = opendata.get_info(table_id)

    assert isinstance(info, dict)


@pytest.mark.parametrize("table_id", datasets)
def test_download(table_id):

    opendata.download_data(table_id)


@pytest.mark.parametrize("table_id", ['00000AAA'])
def test_http_error(table_id):

    try:
        opendata.get_data(table_id)
    except requests.HTTPError:
        assert True
    else:
        assert False


def test_http_error_table_list():

    try:
        opendata.get_table_list(catalog_url='test.cbs.nl')
    except requests.ConnectionError:
        assert True
    else:
        assert False


@pytest.mark.parametrize("table_id", datasets)
def test_http_https_download(table_id):

    opendata.options['use_https'] = True
    opendata.download_data(table_id)
    opendata.options['use_https'] = False
    opendata.download_data(table_id)
    opendata.options['use_https'] = True


@pytest.mark.parametrize("table_id", datasets)
def test_download_and_store(table_id):

    opendata.download_data(
        table_id,
        dir=os.path.join(TEST_ENV, table_id)
    )

    assert os.path.exists(
        os.path.join(TEST_ENV, table_id, 'TableInfos.json')
    )


@pytest.mark.parametrize("table_id", datasets)
def test_get_data(table_id):

    opendata.get_data(table_id)


@pytest.mark.parametrize("table_id", datasets)
def test_info_values(table_id):

    info = opendata.get_info(table_id)

    # Check response is dict (not a list)
    assert isinstance(info, dict)

    # Check required keys are available
    assert 'Description' in info.keys()
    assert 'ID' in info.keys()
    assert 'Identifier' in info.keys()


def test_table_list():

    assert len(opendata.get_table_list()) > 100


def test_filters():

    default_sel_filt = opendata.get_info('82070ENG')['DefaultSelection']
    filters_and_selections = default_sel_filt.split("&")

    for fs in filters_and_selections:
        if fs.startswith('$filter='):
            filt = fs[8:]

    opendata.get_data('82070ENG', filters=filt)


def test_select():

    default_sel_filt = opendata.get_info('82070ENG')['DefaultSelection']
    filters_and_selections = default_sel_filt.split("&")

    for fs in filters_and_selections:
        if fs.startswith('$select='):
            select = fs[8:]

    opendata.get_data('82070ENG', select=select)


def test_select_list():

    default_sel_filt = opendata.get_info('82070ENG')['DefaultSelection']
    filters_and_selections = default_sel_filt.split("&")

    for fs in filters_and_selections:
        if fs.startswith('$select='):
            select = fs[8:]

    opendata.get_data('82070ENG', select=select.split(', '))


def test_select_subset():

    default_sel_filt = opendata.get_info('82070ENG')['DefaultSelection']
    filters_and_selections = default_sel_filt.split("&")

    for fs in filters_and_selections:
        if fs.startswith('$select='):
            select = fs[8:]

    select_list = select.split(', ')
    opendata.get_data('82070ENG', select=select_list[0:2])


def test_select_n_cols():

    default_sel_filt = opendata.get_info('82070ENG')['DefaultSelection']
    filters_and_selections = default_sel_filt.split("&")

    for fs in filters_and_selections:
        if fs.startswith('$select='):
            select = fs[8:]

    select_list = select.split(', ')
    data = opendata.get_data('82070ENG', select=select_list[0:2])

    assert len(data[0].keys()) == 2
    assert len(data[5].keys()) == 2
    assert len(data[10].keys()) == 2


@pytest.mark.parametrize("table_id", datasets_derden)
def test_get_table_list_derden(table_id):

    # option 1
    print("global")
    opendata.options.catalog_url = 'dataderden.cbs.nl'
    data_option1 = opendata.get_table_list()
    opendata.options.catalog_url = 'opendata.cbs.nl'

    # option 2
    print("context")
    with opendata.catalog('dataderden.cbs.nl'):
        data_option2 = opendata.get_table_list()

    # option 3
    print("argument")
    data_option3 = opendata.get_table_list(
        catalog_url='dataderden.cbs.nl'
    )

    assert len(data_option1[0].keys()) > 0

    for key in data_option1[0].keys():

        assert data_option1[0][key] == \
            data_option2[0][key] == data_option3[0][key]


@pytest.mark.parametrize("table_id", datasets_derden)
def test_get_data_derden(table_id):

    # option 1
    print("global")
    opendata.options.catalog_url = 'dataderden.cbs.nl'
    data_option1 = opendata.get_data(table_id)
    opendata.options.catalog_url = 'opendata.cbs.nl'

    # option 2
    print("context")
    with opendata.catalog('dataderden.cbs.nl'):
        data_option2 = opendata.get_data(table_id)

    # option 3
    print("argument")
    data_option3 = opendata.get_data(
        table_id,
        catalog_url='dataderden.cbs.nl'
    )

    assert len(data_option1[0].keys()) > 0

    for key in data_option1[0].keys():

        assert data_option1[0][key] == \
            data_option2[0][key] == data_option3[0][key]
