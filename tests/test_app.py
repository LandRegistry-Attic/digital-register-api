from service.server import app
from collections import namedtuple
import unittest
import json

import mock
import requests
import responses

TitleRegisterData = namedtuple('TitleRegisterData',
  ['title_number', 'register_data', 'geometry_data']
)
DN1000_title = TitleRegisterData('DN1000', "data", "geometry")

class ViewTitleTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    @mock.patch('service.server.get_title_register', return_value=None)
    def test_get_invalid_title_path_404(self, mock_data):
        response = self.app.get('/titles/invalid-ref')
        assert response.status_code == 404

    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_valid_title_path(self, mock_data):
        response = self.app.get('/titles/DN1000')
        assert response.status_code == 200

    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_correct_title_number(self, mock_data):
        response = self.app.get('/titles/DN1000')
        self.assertTrue(str('"title_number": "DN1000"') in str(response.data))

    @mock.patch('service.server.get_title_register', return_value=DN1000_title)
    def test_get_correct_register_data(self, mock_data):
        response = self.app.get('/titles/DN1000')
        self.assertTrue(str('"data": "data"') in str(response.data))
        self.assertTrue(str('"geometry_data": "geometry"') in str(response.data))
