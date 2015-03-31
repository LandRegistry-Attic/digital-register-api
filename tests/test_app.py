from service.server import app, get_property_address
from collections import namedtuple
import unittest
import json

import mock
import requests
import responses

register_fields = ['title_number', 'register_data', 'geometry_data']
FakeTitleRegisterData = namedtuple('TitleRegisterData', register_fields)
DN1000_title = FakeTitleRegisterData('DN1000', "data", "geometry")
DN1001_title = FakeTitleRegisterData('DN1001', "data", "geometry")
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


class ViewTitleTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    # 404 status code when the database query does not return anything
    @mock.patch('service.server.get_title_register', return_value=None)
    def test_get_invalid_title_path_404(self, mock_data):
        response = self.app.get('/titles/invalid-ref')
        assert response.status_code == 404

    # 200 status code when a record is found by the database query
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_valid_title_path(self, mock_data):
        response = self.app.get('/titles/DN1000')
        assert response.status_code == 200

    # The title number returned from the database query is returned in the JSON
    # response
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_correct_title_number(self, mock_data):
        response = self.app.get('/titles/DN1000')
        assert '"title_number": "DN1000"' in response.data.decode()

    # The data and geometry JSON blobs returned from the database query
    # are returned in the JSON response
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_correct_register_data(self, mock_data):
        response = self.app.get('/titles/DN1000')
        page_content = response.data.decode()
        assert '"data": "data"' in page_content
        assert '"geometry_data": "geometry"' in page_content

    # 200 with empty result when the database query does not return anything
    @mock.patch('service.server.get_property_address', return_value=no_elastic_search_hits)
    def test_get_invalid_property_path_empty_result(self, mock_data):
        response = self.app.get('/title_search_postcode/invalid-postcode')
        assert response.status_code == 200
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        assert titles == []

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_hit)
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_valid_property_path(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        assert response.status_code == 200

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_hit)
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_single_uprn_title_match(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        assert titles[0]['title_number'] == 'DN1000'

    @mock.patch('service.server.get_property_address', return_value=single_elastic_search_hit)
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_title_data_with_uprn_match(self, mock_data, mock_title):
        response = self.app.get('/title_search_postcode/PL9_8TB')
        response_json = json.loads(response.data.decode())
        titles = response_json['titles']
        assert titles[0]['data'] == 'data'
