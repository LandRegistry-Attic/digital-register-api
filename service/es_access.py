from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from service import app

ELASTICSEARCH_ENDPOINT = app.config['ELASTIC_SEARCH_ENDPOINT']
MAX_NUMBER_SEARCH_RESULTS = app.config['MAX_NUMBER_SEARCH_RESULTS']


# TODO: write integration tests for this module
def get_properties_for_postcode(postcode):
    search = create_search('property_by_postcode_3')
    query = search.filter('term', postcode=postcode).sort(
        {'house_number_or_first_number': {'missing': '_last'}},
        {'address_string': {'missing': '_last'}}
    )
    return query.execute().hits


def get_properties_for_address(address):
    search = create_search('property_by_address')
    query = search.query('match', address_string=address.lower())
    return query.execute().hits


def create_search(doc_type):
    client = Elasticsearch([ELASTICSEARCH_ENDPOINT])
    search = Search(using=client, index='landregistry', doc_type=doc_type)
    search = search[0:MAX_NUMBER_SEARCH_RESULTS]
    return search


def get_info():
    return Elasticsearch([ELASTICSEARCH_ENDPOINT]).info()
