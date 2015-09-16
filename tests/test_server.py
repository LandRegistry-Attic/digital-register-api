from datetime import datetime
from collections import namedtuple
import json
from elasticsearch_dsl.utils import AttrList
import mock

from service import app
from service.server import db_access, es_access

FakeTitleRegisterData = namedtuple(
    'TitleRegisterData',
    ['title_number', 'register_data', 'geometry_data', 'official_copy_data']
)

FakeElasticsearchAddressHit = namedtuple(
    'Hit',
    ['title_number', 'address_string', 'entry_datetime']
)

FakeElasticsearchPostcodeHit = namedtuple(
    'Hit',
    ['title_number', 'postcode', 'house_number_or_first_number', 'address_string', 'entry_datetime']
)

TEST_EXCEPTION = Exception('Test exception')


def _get_page_size():
    return app.config['SEARCH_RESULTS_PER_PAGE']


def _get_es_postcode_results(*title_numbers, total=None):
    result = AttrList([_get_es_postcode_result(i) for i in title_numbers])
    result.total = len(title_numbers) if total is None else total

    return result


def _get_empty_es_result(total=None):
    result = AttrList([])
    result.total = total if total else 0
    return result


def _get_es_address_results(*title_numbers, total=None):
    result = AttrList([_get_es_address_result(i) for i in title_numbers])
    result.total = len(title_numbers) if total is None else total

    return result


def _get_es_postcode_result(number):
    return FakeElasticsearchPostcodeHit(
        title_number=str(number),
        postcode='SW11 2DR',
        house_number_or_first_number=number,
        address_string='address string {}'.format(number),
        entry_datetime=datetime(2015, 8, 12, 12, 34, 56),
    )


def _get_es_address_result(number):
    return FakeElasticsearchAddressHit(
        title_number=str(number),
        address_string='address string {}'.format(number),
        entry_datetime=datetime(2015, 8, 12, 12, 34, 56),
    )


def _get_titles(*title_numbers):
    return [_get_sample_title(i) for i in title_numbers]


def _get_sample_title(number):
    return FakeTitleRegisterData(
        str(number),
        {'register': 'data {}'.format(number)},
        {'geometry': 'geodata {}'.format(number)},
        {'sub_registers': [{'A': 'register A {}'.format(number)}]},
    )


class TestHealthCheck:

    def setup_method(self, method):
        self.app = app.test_client()

    @mock.patch.object(db_access, 'get_title_register', return_value=None)
    @mock.patch.object(es_access, 'get_info', return_value={'status': 200})
    def test_health_check_returns_200_response_when_data_stores_respond_properly(
            self, mock_get_info, mock_get_user):

        response = self.app.get('/health')
        assert response.status_code == 200
        assert response.data.decode() == '{"status": "ok"}'

    @mock.patch.object(db_access, 'get_title_register', side_effect=Exception('Test PG exception'))
    @mock.patch.object(es_access, 'get_info', return_value={'status': 200})
    def test_health_check_returns_500_response_when_db_access_fails(self, mock_get_info, mock_get_user):
        response = self.app.get('/health')

        assert response.status_code == 500
        json_response = json.loads(response.data.decode())
        assert json_response == {
            'status': 'error',
            'errors': ['Problem talking to PostgreSQL: Test PG exception'],
        }

    @mock.patch.object(db_access, 'get_title_register', return_value=None)
    @mock.patch.object(es_access, 'get_info', side_effect=Exception('Test ES exception'))
    def test_health_check_returns_500_response_when_es_access_fails(self, mock_get_info, mock_get_user):
        response = self.app.get('/health')

        assert response.status_code == 500
        json_response = json.loads(response.data.decode())
        assert json_response == {
            'status': 'error',
            'errors': ['Problem talking to elasticsearch: Test ES exception'],
        }

    @mock.patch.object(db_access, 'get_title_register', side_effect=Exception('Test PG exception'))
    @mock.patch.object(es_access, 'get_info', side_effect=Exception('Test ES exception'))
    def test_health_check_returns_500_response_with_multiple_errors_when_both_data_stores_fail(
            self, mock_get_info, mock_get_user):

        response = self.app.get('/health')

        assert response.status_code == 500
        json_response = json.loads(response.data.decode())
        assert json_response == {
            'status': 'error',
            'errors': [
                'Problem talking to elasticsearch: Test ES exception',
                'Problem talking to PostgreSQL: Test PG exception',
            ],
        }


class TestGetTitle:

    def setup_method(self, method):
        self.app = app.test_client()

    @mock.patch.object(db_access, 'get_title_register', return_value=None)
    def test_get_title_calls_db_access_to_get_title(self, mock_get_title_register):
        title_number = 'title123'
        self.app.get('/titles/{}'.format(title_number))

        mock_get_title_register.assert_called_once_with(title_number)

    @mock.patch.object(db_access, 'get_title_register', return_value=None)
    def test_get_title_returns_404_response_when_db_access_returns_none(self, mock_get_title_register):
        response = self.app.get('/titles/title123')
        assert response.status_code == 404
        assert '"error": "Title not found"' in response.data.decode()

    @mock.patch.object(db_access, 'get_title_register', side_effect=TEST_EXCEPTION)
    def test_get_title_returns_generic_error_response_when_db_access_fails(self, mock_get_title_register):
        response = self.app.get('/titles/title123')
        assert response.status_code == 500
        json_body = json.loads(response.data.decode())
        assert json_body == {'error': 'Internal server error'}

    def test_get_title_returns_200_response_with_title_from_db_access(self):
        title_number = 'title123'
        register_data = {'register': 'data'}
        geometry_data = {'geometry': 'data'}
        sub_registers = {'sub_registers': [{'A': 'register A'}]}

        title = FakeTitleRegisterData(title_number, register_data, geometry_data, sub_registers)

        with mock.patch('service.server.db_access.get_title_register', return_value=title):
            response = self.app.get('/titles/{}'.format(title_number))
            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert json_body == {
                'title_number': title_number,
                'data': register_data,
                'geometry_data': geometry_data,
            }


class TestGetOfficialCopy:

    def setup_method(self, method):
        self.app = app.test_client()

    @mock.patch.object(db_access, 'get_official_copy_data', return_value=None)
    def test_get_official_copy_calls_db_access_to_get_the_copy(self, mock_get_official_copy_data):
        title_number = 'title123'
        self.app.get('/titles/{}/official-copy'.format(title_number))
        mock_get_official_copy_data.assert_called_once_with(title_number)

    @mock.patch.object(db_access, 'get_official_copy_data', return_value=None)
    def test_get_official_copy_returns_404_response_when_db_access_returns_none(self, mock_get_official_copy_data):
        title_number = 'title123'
        response = self.app.get('/titles/{}/official-copy'.format(title_number))

        assert response.status_code == 404

        json_body = json.loads(response.data.decode())
        assert json_body == {'error': 'Title not found'}

    @mock.patch.object(db_access, 'get_official_copy_data', side_effect=TEST_EXCEPTION)
    def test_get_official_copy_returns_generic_error_response_when_db_access_fails(self, mock_get_official_copy_data):
        response = self.app.get('/titles/title123/official-copy')
        assert response.status_code == 500
        json_body = json.loads(response.data.decode())
        assert json_body == {'error': 'Internal server error'}

    def test_get_official_copy_returns_200_response_with_copy_from_db_access(self):
        title_number = 'title123'
        sub_registers = [{'A': 'register A'}, {'B': 'register B'}]

        title = FakeTitleRegisterData(
            title_number, {'register': 'data'}, {'geometry': 'data'}, {'sub_registers': sub_registers}
        )

        with mock.patch('service.server.db_access.get_official_copy_data', return_value=title):
            response = self.app.get('/titles/{}/official-copy'.format(title_number))
            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert json_body == {
                'official_copy_data': {
                    'sub_registers': sub_registers,
                    'title_number': title_number,
                }
            }


class TestGetPropertiesForPostcode:

    def setup_method(self, method):
        self.app = app.test_client()

    @mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': 321})
    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_empty_es_result())
    def test_get_properties_for_postcode_calls_es_access_with_page_number_and_normalised_postcode(
            self, mock_get_properties):

        postcode = '  Sw1 1_2 dR '
        normalised_postcode = 'SW112DR'
        page_number = 123

        self.app.get('/title_search_postcode/{}?page={}'.format(postcode, page_number))

        mock_get_properties.assert_called_once_with(normalised_postcode, 321, page_number)

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_empty_es_result())
    def test_get_properties_for_postcode_calls_es_access_with_default_page_number_when_not_provided(
            self, mock_get_properties):

        postcode = 'SW112DR'
        self.app.get('/title_search_postcode/{}'.format(postcode))

        mock_get_properties.assert_called_once_with(postcode, _get_page_size(), 0)

    @mock.patch.object(es_access, 'get_properties_for_postcode', side_effect=TEST_EXCEPTION)
    def test_get_properties_for_postcode_returns_generic_error_response_when_fails(self, mock_get_properties):
        response = self.app.get('/title_search_postcode/SW112DR')

        assert response.status_code == 500

        json_body = json.loads(response.data.decode())
        assert json_body == {'error': 'Internal server error'}

    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_postcode_calls_db_access_with_data_from_elasticsearch(
            self, mock_get_registers):

        with mock.patch('service.server.es_access.get_properties_for_postcode') as mock_get_properties:
            mock_get_properties.return_value = _get_es_postcode_results(1, 2, 3, 4)
            self.app.get('/title_search_postcode/SW112DR')

        mock_get_registers.assert_called_once_with(['1', '2', '3', '4'])

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(1, 2))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1, 2))
    def test_get_properties_for_postcode_returns_response_in_correct_format(
            self, mock_get_registers, mock_get_properties):

        response = self.app.get('/title_search_postcode/SW112DR')
        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {
            'number_pages': 1,
            'number_results': 2,
            'page_number': 0,
            'titles': [
                {'data': {'register': 'data 1'}, 'title_number': '1'},
                {'data': {'register': 'data 2'}, 'title_number': '2'}
            ]
        }

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(3, 1, 2))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1, 2, 3))
    def test_get_properties_for_postcode_returns_titles_in_order_given_by_es_access(
            self, mock_get_registers, mock_get_properties):

            response = self.app.get('/title_search_postcode/SW112DR')

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'titles' in json_body
            assert json_body['titles'] == [
                {'data': {'register': 'data 3'}, 'title_number': '3'},
                {'data': {'register': 'data 1'}, 'title_number': '1'},
                {'data': {'register': 'data 2'}, 'title_number': '2'},
            ]

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(1, 2, total=4))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1, 2))
    def test_get_properties_for_postcode_response_contains_right_number_of_pages_when_last_page_full(
            self, mock_get_registers, mock_get_properties):

        page_size = 2

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_postcode/SW112DR?page=1')

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body['number_pages'] == 2

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(1, total=4))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_postcode_response_contains_right_number_of_pages_when_last_page_not_full(
            self, mock_get_registers, mock_get_properties):

        page_size = 2

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_postcode/SW112DR?page=1')

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body['number_pages'] == 2

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(1, total=200))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_postcode_response_contains_requested_page_number_when_present(
            self, mock_get_properties, mock_get_registers):

        requested_page_number = 12

        response = self.app.get('/title_search_postcode/SW112DR?page={}'.format(requested_page_number))

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert 'page_number' in json_body
        assert json_body['page_number'] == requested_page_number

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(total=10))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_postcode_returns_requested_page_number_when_it_does_not_exist(
            self, mock_get_registers, mock_get_properties):

        requested_page_number = 3
        page_size = 5

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_postcode/SW112DR?page={}'.format(requested_page_number))

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body == {
                'number_pages': 2,
                'number_results': 10,
                'page_number': requested_page_number,
                'titles': []
            }

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_empty_es_result())
    def test_get_properties_for_postcode_returns_right_response_when_no_results_from_es(self, mock_get_properties):
        response = self.app.get('/title_search_postcode/SW112DR')

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {'number_pages': 0, 'number_results': 0, 'page_number': 0, 'titles': []}

    @mock.patch.object(es_access, 'get_properties_for_postcode', return_value=_get_es_postcode_results(1, total=1))
    @mock.patch.object(db_access, 'get_title_registers', return_value=[])
    def test_get_properties_for_postcode_returns_right_response_when_no_results_from_pg(
            self, mock_get_registers, mock_get_properties):

        response = self.app.get('/title_search_postcode/SW112DR')

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {'number_pages': 1, 'number_results': 1, 'page_number': 0, 'titles': []}


class TestGetPropertiesForAddress:

    def setup_method(self, method):
        self.app = app.test_client()

    @mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': 321})
    @mock.patch.object(es_access, 'get_properties_for_address', return_value=[])
    def test_get_properties_for_address_calls_es_access_with_page_number_and_search_term(self, mock_get_properties):
        search_term = 'search term'
        page_number = 123

        self.app.get('/title_search_address/{}?page={}'.format(search_term, page_number))

        mock_get_properties.assert_called_once_with(search_term, 321, page_number)

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=[])
    def test_get_properties_for_address_calls_es_access_with_default_page_number_when_not_provided(
            self, mock_get_properties):

        search_term = 'searchterm'
        self.app.get('/title_search_address/{}'.format(search_term))

        mock_get_properties.assert_called_once_with(search_term, _get_page_size(), 0)

    @mock.patch.object(es_access, 'get_properties_for_address', side_effect=TEST_EXCEPTION)
    def test_get_properties_for_address_returns_generic_error_response_when_fails(self, mock_get_properties):
        response = self.app.get('/title_search_address/searchterm')

        assert response.status_code == 500

        json_body = json.loads(response.data.decode())
        assert json_body == {'error': 'Internal server error'}

    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_address_calls_db_access_with_data_from_elasticsearch(
            self, mock_get_registers):

        with mock.patch('service.server.es_access.get_properties_for_address') as mock_get_properties:
            mock_get_properties.return_value = _get_es_address_results(1, 2, 3, 4)
            self.app.get('/title_search_address/searchterm')

        mock_get_registers.assert_called_once_with(['1', '2', '3', '4'])

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(1, 2))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1, 2))
    def test_get_properties_for_address_returns_response_in_correct_format(
            self, mock_get_registers, mock_get_properties):

        response = self.app.get('/title_search_address/searchterm')
        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {
            'number_pages': 1,
            'number_results': 2,
            'page_number': 0,
            'titles': [
                {'data': {'register': 'data 1'}, 'title_number': '1'},
                {'data': {'register': 'data 2'}, 'title_number': '2'}
            ]
        }

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(3, 1, 2))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1, 2, 3))
    def test_get_properties_for_address_returns_titles_in_order_given_by_es_access(
            self, mock_get_registers, mock_get_properties):

        response = self.app.get('/title_search_address/searchterm')

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert 'titles' in json_body
        assert json_body['titles'] == [
            {'data': {'register': 'data 3'}, 'title_number': '3'},
            {'data': {'register': 'data 1'}, 'title_number': '1'},
            {'data': {'register': 'data 2'}, 'title_number': '2'},
        ]

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(1, 2, total=4))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1, 2))
    def test_get_properties_for_address_response_contains_right_number_of_pages_when_last_page_full(
            self, mock_get_registers, mock_get_properties):

        page_size = 2

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_address/searchterm?page=1')

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body['number_pages'] == 2

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(1, total=4))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_address_response_contains_right_number_of_pages_when_last_page_not_full(
            self, mock_get_registers, mock_get_properties):

        page_size = 2

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_address/searchterm?page=1')

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body['number_pages'] == 2

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(1, total=200))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_address_response_contains_requested_page_number_when_present(
            self, mock_get_properties, mock_get_registers):

        requested_page_number = 12

        response = self.app.get('/title_search_address/searchterm?page={}'.format(requested_page_number))

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert 'page_number' in json_body
        assert json_body['page_number'] == requested_page_number

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(total=10))
    @mock.patch.object(db_access, 'get_title_registers', return_value=_get_titles(1))
    def test_get_properties_for_address_returns_requested_page_number_when_it_does_not_exist(
            self, mock_get_registers, mock_get_properties):

        requested_page_number = 3
        page_size = 5

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_address/searchterm?page={}'.format(requested_page_number))

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body == {
                'number_pages': 2,
                'number_results': 10,
                'page_number': requested_page_number,
                'titles': []
            }

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_empty_es_result())
    def test_get_properties_for_address_returns_right_response_when_no_results_from_es(self, mock_get_properties):
        response = self.app.get('/title_search_address/searchterm')

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {'number_pages': 0, 'number_results': 0, 'page_number': 0, 'titles': []}

    @mock.patch.object(es_access, 'get_properties_for_address', return_value=_get_es_address_results(1, total=1))
    @mock.patch.object(db_access, 'get_title_registers', return_value=[])
    def test_get_properties_for_address_returns_right_response_when_no_results_from_pg(
            self, mock_get_registers, mock_get_properties):

        response = self.app.get('/title_search_address/searchterm')

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {'number_pages': 1, 'number_results': 1, 'page_number': 0, 'titles': []}
