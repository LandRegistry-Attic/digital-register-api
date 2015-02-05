from service.server import app
import unittest
import json

import mock
import unittest
import requests
import responses

class ViewTitleTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_get_invalid_title_path_404(self):
        response = self.app.get('/titles/invalid-ref')
        assert response.status_code == 404
