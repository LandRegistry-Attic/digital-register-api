from collections import namedtuple
import unittest
import json
import mock
from service import app
from service.server import paginated_address_records


register_fields = ['title_number', 'register_data', 'geometry_data', 'official_copy_data']
FakeTitleRegisterData = namedtuple('TitleRegisterData', register_fields)
DN1000_title = FakeTitleRegisterData('DN1000', "data", "geometry", {"official": "copy"})
DN1001_title = FakeTitleRegisterData('DN1001', "data", "geometry", {"official": "copy"})
two_titles = [DN1000_title, DN1001_title]

FakeElasticSearchHit = namedtuple('Hit', [
    'addressKey', 'buildingName', 'buildingNumber', 'businessName',
    'departmentName', 'dependentLocality', 'dependentThoroughfareName',
    'doubleDependentLocality', 'postCode', 'postTown',
    'subBuildingName', 'thoroughfareName', 'uprns', 'title_number'])

no_elastic_search_hits = []

single_elastic_search_hit = [
    FakeElasticSearchHit(
        'address key_', 'building name_', '34',
        'business name_', 'department name_', 'dependent locality_',
        'dependent thoroughfare name_', 'double dependent locality_',
        'PL9 8TB', 'Plymouth',
        'sub-building name_', 'Murhill Street', 'udprn_', 'DN1000'
    ),
]

twenty_one_elastic_search_hits = 21*single_elastic_search_hit


class ViewTitleTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    # 404 status code when the database query does not return anything
    @mock.patch('service.server.db_access.get_title_register', return_value=None)
    def test_get_invalid_title_path_404(self, mock_data):
        response = self.app.get('/titles/invalid-ref')
        assert response.status_code == 404
        assert '"error": "Title not found"' in response.data.decode()

    # 200 status code when a record is found by the database query
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_get_valid_title_path(self, mock_data):
        response = self.app.get('/titles/DN1000')
        assert response.status_code == 200

    # The title number returned from the database query is returned in the JSON
    # response
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_get_correct_title_number(self, mock_data):
        response = self.app.get('/titles/DN1000')
        assert '"title_number": "DN1000"' in response.data.decode()

    # The data and geometry JSON blobs returned from the database query
    # are returned in the JSON response
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_get_correct_register_data(self, mock_data):
        response = self.app.get('/titles/DN1000')
        page_content = response.data.decode()
        assert '"data": "data"' in page_content
        assert '"geometry_data": "geometry"' in page_content

    # 200 with empty result when the database query does not return anything
    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=no_elastic_search_hits)
    def test_get_invalid_property_path_empty_result(self, mock_data):
        response = self.app.get('/title_search_postcode/invalid-postcode')
        assert response.status_code == 200
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        assert titles == []
        assert page_number == 0
        assert number_pages == 0

    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=single_elastic_search_hit)
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_get_valid_property_path(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        assert response.status_code == 200

    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=single_elastic_search_hit)
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_get_single_uprn_title_match(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        assert titles[0]['title_number'] == 'DN1000'
        assert page_number == 1
        assert number_pages == 1

    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=single_elastic_search_hit)
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_get_title_data_with_uprn_match(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        assert titles[0]['data'] == 'data'
        assert page_number == 1
        assert number_pages == 1

    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=twenty_one_elastic_search_hits)
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_postcode_search_with_21_matches(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        number_results = response_json['number_results']
        assert titles[0]['data'] == 'data'
        assert len(titles) == 20
        assert page_number == 1
        assert number_pages == 2
        assert number_results == 21

    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=twenty_one_elastic_search_hits)
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_postcode_search_with_21_matches_page_2(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB?page=2')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        number_results = response_json['number_results']
        assert titles[0]['data'] == 'data'
        assert len(titles) == 1
        assert page_number == 2
        assert number_pages == 2
        assert number_results == 21

    @mock.patch('service.server.es_access.get_properties_for_postcode',
                return_value=twenty_one_elastic_search_hits)
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_postcode_search_with_21_matches_page_50(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB?page=50')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        number_results = response_json['number_results']
        assert titles[0]['data'] == 'data'
        assert len(titles) == 1
        assert page_number == 2
        assert number_pages == 2
        assert number_results == 21

    @mock.patch(
        'service.server.es_access.get_properties_for_address',
        return_value=twenty_one_elastic_search_hits
    )
    @mock.patch('service.server.db_access.get_title_register', return_value=DN1000_title)
    def test_address_search_with_21_matches_page_2(self, mock_data, mock_title):
        response = self.app.get('/title_search_address/PL9_8TB?page=2')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        page_number = response_json['page_number']
        number_pages = response_json['number_pages']
        number_results = response_json['number_results']
        assert titles[0]['data'] == 'data'
        assert len(titles) == 1
        assert page_number == 2
        assert number_pages == 2
        assert number_results == 21

    def test_pagination_with_deleted_records(self):
        address_records = [
            FakeTitleRegisterData(i, {'title_number': i}, {}, {}) for i in range(200)
        ]

        def fake_get_title_register(t):
            return FakeTitleRegisterData(t, {'title_number': t}, {}, {}) if t % 2 else None

        with mock.patch('service.server.db_access.get_title_register', fake_get_title_register):
            recs = paginated_address_records(address_records, 3)
        assert recs['page_number'] == 3
        assert recs['number_pages'] == 5
        assert recs['number_results'] == 100

    @mock.patch('service.server.db_access.get_title_register', return_value=None)
    @mock.patch('service.server.es_access.get_info', return_value={'status': 200})
    def test_health_returns_200_response_when_data_stores_respond_properly(
            self, mock_get_info, mock_get_user):

        response = self.app.get('/health')
        assert response.status_code == 200
        assert response.data.decode() == '{"status": "ok"}'

    @mock.patch('service.server.db_access.get_title_register',
                side_effect=Exception('Test PG exception'))
    @mock.patch('service.server.es_access.get_info', return_value={'status': 200})
    def test_health_returns_500_response_when_db_access_fails(self, mock_get_info, mock_get_user):
        response = self.app.get('/health')

        assert response.status_code == 500
        json_response = json.loads(response.data.decode())
        assert json_response == {
            'status': 'error',
            'errors': ['Problem talking to PostgreSQL: Test PG exception'],
        }

    @mock.patch('service.server.db_access.get_title_register', return_value=None)
    @mock.patch('service.server.es_access.get_info', side_effect=Exception('Test ES exception'))
    def test_health_returns_500_response_when_es_access_fails(self, mock_get_info, mock_get_user):
        response = self.app.get('/health')

        assert response.status_code == 500
        json_response = json.loads(response.data.decode())
        assert json_response == {
            'status': 'error',
            'errors': ['Problem talking to elasticsearch: Test ES exception'],
        }

    @mock.patch('service.server.db_access.get_title_register',
                side_effect=Exception('Test PG exception'))
    @mock.patch('service.server.es_access.get_info', side_effect=Exception('Test ES exception'))
    def test_health_returns_500_response_with_multiple_errors_when_both_data_stores_fail(
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

    @mock.patch('service.server.db_access.get_official_copy_data', return_value=DN1000_title)
    def test_get_official_copy_calls_db_access_for_data(self, mock_get_official_copy_data):
        title_number = 'DN1000'
        self.app.get('titles/{}/official-copy'.format(title_number))
        mock_get_official_copy_data.assert_called_once_with(title_number)

    @mock.patch('service.server.db_access.get_official_copy_data', return_value=None)
    def test_get_official_copy_returns_not_found_response_when_title_no_present(
            self, mock_get_official_copy_data):

        response = self.app.get('titles/non-existing-title-number/official-copy')
        assert response.status_code == 404
        assert response.data.decode() == '{"error": "Title not found"}'

    @mock.patch('service.server.db_access.get_official_copy_data', return_value=DN1000_title)
    def test_get_official_copy_returns_official_copy_data_when_present(
            self, mock_get_official_copy_data):

        response = self.app.get('titles/title-number/official-copy')

        assert response.status_code == 200
        response_json = json.loads(response.data.decode())

        expected_json = {
            'official_copy_data': DN1000_title.official_copy_data,
            'title_number': DN1000_title.title_number,
        }

        assert response_json == expected_json
