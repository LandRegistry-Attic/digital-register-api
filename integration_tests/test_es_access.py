import elasticsearch
import mock
import pytest
import requests
from time import sleep
from config import CONFIG_DICT
from service import es_access

PROPERTY_BY_POSTCODE_DOC_TYPE = 'property_by_postcode_3'
PROPERTY_BY_ADDRESS_DOC_TYPE = 'property_by_address'


class TestEsAccess:

    def setup_method(self, method):
        self._ensure_empty_index()

    def test_get_properties_for_postcode_throws_exception_on_unsuccessful_attempt_to_talk_to_es(self):
        with mock.patch.dict(es_access.app.config, {'ELASTICSEARCH_ENDPOINT_URI': 'http://non-existing2342345.co.uk'}):
            with pytest.raises(Exception) as e:
                es_access.get_properties_for_postcode('XX000XX', 10, 0)

            assert type(e.value) == elasticsearch.exceptions.ConnectionError

    def test_get_properties_for_postcode_returns_properties_with_right_data(self):
        postcode = 'XX000XX'
        title_number = 'TITLE1001'
        address_string = 'address string'
        house_number = 123
        entry_datetime = '2015-09-09T12:34:56.123+00'

        self._create_property_for_postcode(postcode, title_number, address_string, house_number, entry_datetime)
        self._wait_for_elasticsearch()

        titles = es_access.get_properties_for_postcode(postcode, 10, 0)
        assert len(titles) == 1
        title = titles[0]
        assert title.postcode == postcode
        assert title.title_number == title_number
        assert title.address_string == address_string
        assert title.house_number_or_first_number == house_number
        assert title.entry_datetime == entry_datetime

    def test_get_properties_for_postcode_returns_properties_sorted_by_number_then_address(self):
        postcode = 'XX000XX'

        title_number_1, title_number_2, title_number_3 = 'TITLE1001', 'TITLE1002', 'TITLE1003'

        self._create_property_for_postcode(postcode, title_number_1, 'address b 1', house_number=2)
        self._create_property_for_postcode(postcode, title_number_2, 'address a 1', house_number=1)
        self._create_property_for_postcode(postcode, title_number_3, 'address b 1', house_number=1)

        self._wait_for_elasticsearch()
        titles = es_access.get_properties_for_postcode(postcode, 10, 0)

        assert self._get_title_numbers(titles) == [title_number_2, title_number_3, title_number_1]

    def test_get_properties_for_postcode_returns_empty_list_when_no_matches(self):
        properties = es_access.get_properties_for_postcode('XX000XX', 10, 0)
        assert properties == []

    def test_get_properties_for_postcode_does_not_return_addresses_from_different_postcodes(self):
        postcode_1 = 'XX000XX'
        postcode_2 = 'YY000YY'

        title_number_1 = 'TITLE1001'
        title_number_2 = 'TITLE1002'

        self._create_property_for_postcode(postcode_1, title_number_1, 'address a 1')
        self._create_property_for_postcode(postcode_2, title_number_2, 'address b 1')

        self._wait_for_elasticsearch()
        properties_for_postcode_1 = es_access.get_properties_for_postcode(postcode_1, 10, 0)
        assert self._get_title_numbers(properties_for_postcode_1) == [title_number_1]

        properties_for_postcode_2 = es_access.get_properties_for_postcode(postcode_2, 10, 0)
        assert self._get_title_numbers(properties_for_postcode_2) == [title_number_2]

    def test_get_properties_for_postcode_returns_the_right_page_of_records(self):
        postcode = 'XX000XX'

        for i in range(1, 6):
            self._create_property_for_postcode('XX000XX', 'TITLE{}'.format(i), 'address {}'.format(i), i)

        self._wait_for_elasticsearch()

        first_page = es_access.get_properties_for_postcode(postcode, 2, 0)
        assert self._get_title_numbers(first_page) == ['TITLE1', 'TITLE2']

        second_page = es_access.get_properties_for_postcode(postcode, 2, 1)
        assert self._get_title_numbers(second_page) == ['TITLE3', 'TITLE4']

        third_page = es_access.get_properties_for_postcode(postcode, 2, 2)
        assert self._get_title_numbers(third_page) == ['TITLE5']

    def test_get_properties_for_address_throws_exception_on_unsuccessful_attempt_to_talk_to_es(self):
        with mock.patch.dict(es_access.app.config, {'ELASTICSEARCH_ENDPOINT_URI': 'http://non-existing2342345.co.uk'}):
            with pytest.raises(Exception) as e:
                es_access.get_properties_for_address('XX000XX', 10, 0)

            assert type(e.value) == elasticsearch.exceptions.ConnectionError

    def test_get_properties_for_address_returns_properties_with_right_data(self):
        title_number = 'TITLE1001'
        address_string = 'address string'
        entry_datetime = '2015-09-09T12:34:56.123+00'

        self._create_property_for_address(title_number, address_string, entry_datetime)
        self._wait_for_elasticsearch()

        titles = es_access.get_properties_for_address(address_string, 10, 0)
        assert len(titles) == 1
        title = titles[0]
        assert title.title_number == title_number
        assert title.address_string == address_string
        assert title.entry_datetime == entry_datetime

    def test_get_properties_for_address_returns_properties_sorted_by_match_strength(self):
        title_number_1, title_number_2, title_number_3 = 'TITLE1001', 'TITLE1002', 'TITLE1003'

        self._create_property_for_address(title_number_1, 'almost same address')
        self._create_property_for_address(title_number_2, 'other address')
        self._create_property_for_address(title_number_3, 'same address')

        self._wait_for_elasticsearch()
        titles = es_access.get_properties_for_address('same address', 10, 0)

        assert self._get_title_numbers(titles) == [title_number_3, title_number_1, title_number_2]

    def test_get_properties_for_address_returns_empty_list_when_no_matches(self):
        titles = es_access.get_properties_for_address('non-existing address', 10, 0)
        assert titles == []

    def test_get_properties_for_address_returns_the_right_page_of_records(self):
        search_phrase = 'strongest match first'

        address_1 = 'match first'
        address_2 = 'weakest match'
        address_3 = 'strongest match first'

        title_number_1 = "MIDDLE"
        title_number_2 = "WEAKEST"
        title_number_3 = "STRONGEST"

        self._create_property_for_address(title_number_1, address_1)
        self._create_property_for_address(title_number_2, address_2)
        self._create_property_for_address(title_number_3, address_3)

        self._wait_for_elasticsearch()

        first_page = es_access.get_properties_for_address(search_phrase, page_size=2, page_number=0)
        assert self._get_title_numbers(first_page) == ['STRONGEST', 'MIDDLE']

        second_page = es_access.get_properties_for_address(search_phrase, page_size=2, page_number=1)
        assert self._get_title_numbers(second_page) == ['WEAKEST']

    def test_get_info_throws_exception_on_unsuccessful_attempt_to_talk_to_es(self):
        with mock.patch.dict(es_access.app.config, {'ELASTICSEARCH_ENDPOINT_URI': 'http://non-existing2342345.co.uk'}):
            with pytest.raises(Exception) as e:
                es_access.get_info()

            assert type(e.value) == elasticsearch.exceptions.ConnectionError

    def test_get_info_returns_cluster_info(self):
        result = es_access.get_info()
        assert result.get('status') == 200
        assert result.get('cluster_name') == 'elasticsearch'

    def _drop_index(self):
        requests.delete(self._get_index_uri())

    def _ensure_empty_index(self):
        self._drop_index()

        index = {
            'mappings': {
                PROPERTY_BY_POSTCODE_DOC_TYPE: {
                    'properties': {
                        'title_number': {'type': 'string', 'index': 'no'},
                        'postcode': {'type': 'string', 'index': 'not_analyzed'},
                        'house_number_or_first_number': {'type': 'integer', 'index': 'not_analyzed'},
                        'address_string': {'type': 'string', 'index': 'not_analyzed'},
                        'entry_datetime': {
                            'type': 'date',
                            'format': 'date_time',
                            'index': 'no'
                        },
                    }
                },
                PROPERTY_BY_ADDRESS_DOC_TYPE: {
                    'properties': {
                        'title_number': {'type': 'string', 'index': 'no'},
                        'address_string': {'type': 'string', 'index': 'analyzed'},
                        'entry_datetime': {'type': 'date', 'format': 'date_time', 'index': 'no'},
                    }
                }
            }
        }

        response = requests.put(self._get_index_uri(), json=index)
        assert response.status_code == 200

    def _create_property_for_postcode(
            self, postcode, title_number, address_string, house_number=1, entry_datetime='2015-09-09T12:34:56.123+00'):

        entry_json = {
            'title_number': title_number,
            'entry_datetime': entry_datetime,
            'postcode': postcode,
            'house_number_or_first_number': house_number,
            'address_string': address_string,
        }

        uri = '{}/{}/'.format(self._get_index_uri(), PROPERTY_BY_POSTCODE_DOC_TYPE)
        response = requests.post(uri, json=entry_json)
        assert response.status_code == 201

    def _create_property_for_address(
            self, title_number, address_string, entry_datetime='2015-09-09T12:34:56.123+00'):

        entry_json = {
            'title_number': title_number,
            'entry_datetime': entry_datetime,
            'address_string': address_string,
        }

        uri = '{}/{}/'.format(self._get_index_uri(), PROPERTY_BY_ADDRESS_DOC_TYPE)
        response = requests.post(uri, json=entry_json)
        assert response.status_code == 201

    def _get_title_numbers(self, search_results):
        return list(map(lambda result: result.title_number, search_results))

    def _get_index_uri(self):
        return self._get_elasticsearch_uri() + '/' + CONFIG_DICT['ELASTICSEARCH_INDEX_NAME']

    def _get_elasticsearch_uri(self):
        return CONFIG_DICT['ELASTICSEARCH_ENDPOINT_URI']

    def _wait_for_elasticsearch(self):
        sleep(1.5)
