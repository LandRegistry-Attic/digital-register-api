import json
import mock
from datetime import datetime
from collections import namedtuple
from elasticsearch_dsl.utils import AttrList
from service import app
from service.server import db_access, es_access, api_client

FakeTitleRegisterData = namedtuple(
    'TitleRegisterData',
    ['title_number', 'register_data', 'geometry_data', 'official_copy_data']
)

FakeUprnMapping = namedtuple(
    'UprnMapping',
    ['uprn', 'lr_uprn'])

FakeElasticsearchAddressHit = namedtuple(
    'Hit',
    ['title_number', 'address_string', 'entry_datetime']
)

FakeElasticsearchPostcodeHit = namedtuple(
    'Hit',
    ['title_number', 'postcode', 'house_number_or_first_number', 'address_string', 'entry_datetime']
)

TEST_EXCEPTION = Exception('Test exception')

ES_RESULT = {
    "data": {
        "addresses": [
            {
                "building_name": "1 INGLEWOOD HOUSE",
                "building_number": "",
                "department_name": "",
                "dependent_locality": "",
                "dependent_thoroughfare_name": "",
                "double_dependent_locality": "",
                "entry_datetime": "2014-06-07T09:01:38+00",
                "joined_fields": "1 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA",
                "organisation_name": "",
                "post_town": "EXETER",
                "postcode": "EX1 1AA",
                "sub_building_name": "",
                "thoroughfare_name": "SIDWELL STREET",
                "uprn": "1234",
                "x_coordinate": 292772.0,
                "y_coordinate": 93294.0
            }]
    }
}


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


def _get_empty_api_client():
    return {'data': {'addresses': [], 'total': 0, 'page_number': 0, 'page_size': 20}}


def _get_one_result_from_api_client():
    return {'data': {'addresses': [
        {
            "building_name": "1 INGLEWOOD HOUSE",
            "building_number": "",
            "department_name": "",
            "dependent_locality": "",
            "dependent_thoroughfare_name": "",
            "double_dependent_locality": "",
            "entry_datetime": "2014-06-07T09:01:38+00",
            "joined_fields": "1 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA",
            "organisation_name": "",
            "post_town": "EXETER",
            "postcode": "EX1 1AA",
            "sub_building_name": "",
            "thoroughfare_name": "SIDWELL STREET",
            "uprn": "10023117067",
            "x_coordinate": 292772.0,
            "y_coordinate": 93294.0,
            "title_number": "EX100",
            "tenure": "freehold",
            "register_data": "blah"
        }], 'total': 1, 'page_number': 1, 'page_size': 20}}


def _get_two_results_from_api_client():
    return {'data': {'addresses': [
        {
            "building_name": "1 INGLEWOOD HOUSE",
            "building_number": "",
            "department_name": "",
            "dependent_locality": "",
            "dependent_thoroughfare_name": "",
            "double_dependent_locality": "",
            "entry_datetime": "2014-06-07T09:01:38+00",
            "joined_fields": "1 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA",
            "organisation_name": "",
            "post_town": "EXETER",
            "postcode": "EX1 1AA",
            "sub_building_name": "",
            "thoroughfare_name": "SIDWELL STREET",
            "uprn": "10023117067",
            "x_coordinate": 292772.0,
            "y_coordinate": 93294.0,
            "title_number": "EX100",
            "tenure": "freehold",
            "register_data": "blah"
        },
        {
            "building_name": "2 INGLEWOOD HOUSE",
            "building_number": "",
            "department_name": "",
            "dependent_locality": "",
            "dependent_thoroughfare_name": "",
            "double_dependent_locality": "",
            "entry_datetime": "2014-06-07T09:01:38+00",
            "joined_fields": "2 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA",
            "organisation_name": "",
            "post_town": "EXETER",
            "postcode": "EX1 1AA",
            "sub_building_name": "",
            "thoroughfare_name": "SIDWELL STREET",
            "uprn": "10023117067",
            "x_coordinate": 292772.0,
            "y_coordinate": 93294.0,
            "title_number": "EX101",
            "tenure": "freehold",
            "register_data": "blah"
        }], 'total': 2, 'page_number': 1, 'page_size': 20}}


def _get_api_client_response_when_es_finds_but_no_pg_result():
    return {'data': {'addresses': [], 'total': 1, 'page_number': 1, 'page_size': 20}}


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


def _get_sample_uprn():
    return FakeUprnMapping(
        uprn='1234',
        lr_uprn='1234'
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
    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_empty_api_client())
    def test_get_properties_for_postcode_calls_db_access_with_page_number_and_normalised_postcode(
            self, mock_get_properties):

        postcode = '  Sw11_ 2dR '
        normalised_postcode = 'SW11 2DR'
        page_number = 123

        self.app.get('/title_search_postcode/{}?page={}'.format(postcode, page_number))

        mock_get_properties.assert_called_once_with(normalised_postcode, page_number, 321)

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_empty_api_client())
    def test_get_properties_for_postcode_calls_es_access_with_default_page_number_when_not_provided(
            self, mock_get_properties):

        postcode = 'SW11 2DR'
        self.app.get('/title_search_postcode/{}'.format(postcode))

        mock_get_properties.assert_called_once_with(postcode, 0, _get_page_size())

    @mock.patch.object(api_client, 'get_titles_by_postcode', side_effect=TEST_EXCEPTION)
    def test_get_properties_for_postcode_returns_generic_error_response_when_fails(self, mock_get_properties):
        response = self.app.get('/title_search_postcode/SW112DR')

        assert response.status_code == 500

        json_body = json.loads(response.data.decode())
        assert json_body == {'error': 'Internal server error'}

    @mock.patch.object(db_access, 'get_mapped_lruprn', return_value=_get_titles(1))
    def test_get_properties_for_postcode_calls_db_access_with_uprn_from_elasticsearch(
            self, mock_get_registers):

        with mock.patch('service.server.api_client.get_titles_by_postcode') as mock_get_properties:
            mock_get_properties.return_value = ES_RESULT
            self.app.get('/title_search_postcode/SW11 2DR')

        mock_get_registers.assert_called_once_with('1234')

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_one_result_from_api_client())
    @mock.patch.object(db_access, 'get_mapped_lruprn', return_value=_get_sample_uprn())
    @mock.patch.object(db_access, 'get_title_number_and_register_data', return_value=_get_sample_title(1))
    def test_get_properties_for_postcode_returns_response_in_correct_format(
            self, mock_get_titles, mock_get_mapped_lruprn, get_title_and_register_data):

        response = self.app.get('/title_search_postcode/SW11%202DR')
        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {
            'number_pages': 1,
            'number_results': 1,
            'page_number': 0,
            'titles': [
                {'address': '1 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA', 'data': {'register': 'data 1'}, 'title_number': '1'}
            ]
        }

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_two_results_from_api_client())
    @mock.patch.object(db_access, 'get_mapped_lruprn', return_value=_get_sample_uprn())
    @mock.patch.object(db_access, 'get_title_number_and_register_data', return_value=_get_sample_title(1))
    def test_get_properties_for_postcode_returns_titles_in_order_given_by_api_client(
            self, mock_get_titles, mock_get_mapped_lruprn, get_title_and_register_data):

            response = self.app.get('/title_search_postcode/SW11%202DR')

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'titles' in json_body
            assert json_body['titles'] == [
                {'address': '1 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA', 'data': {'register': 'data 1'}, 'title_number': '1'},
                {'address': '2 INGLEWOOD HOUSE, SIDWELL STREET, EXETER, EX1 1AA', 'data': {'register': 'data 1'}, 'title_number': '1'}
            ]

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_two_results_from_api_client())
    @mock.patch.object(db_access, 'get_mapped_lruprn', return_value=_get_sample_uprn())
    @mock.patch.object(db_access, 'get_title_number_and_register_data', return_value=_get_sample_title(1))
    def test_get_properties_for_postcode_response_contains_requested_page_number_when_present(self,
                                                                                              mock_get_titles,
                                                                                              mock_get_mapped_lruprn,
                                                                                              get_title_and_register_data):

        requested_page_number = 12

        response = self.app.get('/title_search_postcode/SW11%202DR?page={}'.format(requested_page_number))

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert 'page_number' in json_body
        assert json_body['page_number'] == requested_page_number

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_api_client_response_when_es_finds_but_no_pg_result())
    def test_get_properties_for_postcode_returns_requested_page_number_when_it_does_not_exist(
            self, mock_get_titles):

        requested_page_number = 3
        page_size = 5

        with mock.patch.dict(app.config, {'SEARCH_RESULTS_PER_PAGE': page_size}):
            response = self.app.get('/title_search_postcode/SW11%202DR?page={}'.format(requested_page_number))

            assert response.status_code == 200
            json_body = json.loads(response.data.decode())
            assert 'page_number' in json_body
            assert json_body == {
                'number_pages': 1,
                'number_results': 1,
                'page_number': requested_page_number,
                'titles': []
            }

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_empty_api_client())
    def test_get_properties_for_postcode_returns_right_response_when_no_results_from_api_client(self, mock_get_properties):
        response = self.app.get('/title_search_postcode/SW11%202DR')

        assert response.status_code == 200
        json_body = json.loads(response.data.decode())
        assert json_body == {'number_pages': 0, 'number_results': 0, 'page_number': 0, 'titles': []}

    @mock.patch.object(api_client, 'get_titles_by_postcode', return_value=_get_api_client_response_when_es_finds_but_no_pg_result())
    @mock.patch.object(db_access, 'get_mapped_lruprn', return_value=None)
    def test_get_properties_for_postcode_returns_right_response_when_no_results_from_pg(
            self, mock_get_titles, mock_get_mapped_lruprn):

        response = self.app.get('/title_search_postcode/SW11%202DR')

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
