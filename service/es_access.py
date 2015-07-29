from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from service import app

ELASTICSEARCH_ENDPOINT = app.config['ELASTIC_SEARCH_ENDPOINT']
MAX_NUMBER_SEARCH_RESULTS = app.config['MAX_NUMBER_SEARCH_RESULTS']
SEARCH_RESULTS_PER_PAGE = app.config['SEARCH_RESULTS_PER_PAGE']


def _get_start_and_end_indexes(page_number):
    start_index = page_number * SEARCH_RESULTS_PER_PAGE
    end_index = start_index + SEARCH_RESULTS_PER_PAGE
    return start_index, end_index


# TODO: write integration tests for this module
def get_properties_for_postcode(postcode, page_number):
    search = create_search('property_by_postcode_3')
    query = search.filter('term', postcode=postcode).sort(
        {'house_number_or_first_number': {'missing': '_last'}},
        {'address_string': {'missing': '_last'}}
    )
    start_index, end_index = _get_start_and_end_indexes(page_number)
    return query[start_index:end_index].execute().hits


def get_properties_for_address(address, page_number):
    search = create_search('property_by_address')
    query = search.query('match', address_string=address.lower())
    start_index, end_index = _get_start_and_end_indexes(page_number)
    return query[start_index:end_index].execute().hits


def create_search(doc_type):
    client = Elasticsearch([ELASTICSEARCH_ENDPOINT])
    search = Search(using=client, index='landregistry', doc_type=doc_type)
    search = search[0:MAX_NUMBER_SEARCH_RESULTS]
    return search


def get_info():
    return Elasticsearch([ELASTICSEARCH_ENDPOINT]).info()
