from service.server import app
from collections import namedtuple
import unittest
import json

import mock
import requests
import responses

register_fields = ['title_number', 'register_data', 'geometry_data']
FakeTitleRegisterData = namedtuple('TitleRegisterData', register_fields)
DN1000_title = FakeTitleRegisterData('DN1000', "data", "geometry")


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
        self.assertTrue(str('"title_number": "DN1000"') in str(response.data))

    # The data and geometry JSON blobs returned from the database query
    # are returned in the JSON response
    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_correct_register_data(self, mock_data):
        response = self.app.get('/titles/DN1000')
        page_content = str(response.data)
        self.assertTrue(str('"data": "data"') in page_content)
        self.assertTrue(str('"geometry_data": "geometry"') in page_content)
