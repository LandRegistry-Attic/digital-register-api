from elasticsearch import Elasticsearch  # type: ignore
from elasticsearch_dsl import Search     # type: ignore

from service import app


def get_properties_for_postcode(postcode, page_size, page_number):
    search = _create_search(_get_postcode_search_doc_type())
    query = search.filter('term', postcode=postcode).sort(
        {'house_number_or_first_number': {'missing': '_last'}},
        {'address_string': {'missing': '_last'}}
    )
    start_index, end_index = _get_start_and_end_indexes(page_number, page_size)
    return query[start_index:end_index].execute().hits


def get_properties_for_address(address, page_size, page_number):
    search = _create_search(_get_address_search_doc_type())
    query = search.query('match', address_string=address.lower())
    start_index, end_index = _get_start_and_end_indexes(page_number, page_size)
    return query[start_index:end_index].execute().hits


def get_info():
    return Elasticsearch([_get_elasticsearch_endpoint_url()]).info()


def _create_search(doc_type):
    client = Elasticsearch([_get_elasticsearch_endpoint_url()])
    search = Search(using=client, index=_get_index_name(), doc_type=doc_type)
    search = search[0:_get_max_number_search_results()]
    return search


def _get_start_and_end_indexes(page_number, page_size):
    start_index = page_number * page_size
    end_index = start_index + page_size
    return start_index, end_index


def _get_index_name():
    return app.config['ELASTICSEARCH_INDEX_NAME']


def _get_max_number_search_results():
    return app.config['MAX_NUMBER_SEARCH_RESULTS']


def _get_page_size():
    return app.config['SEARCH_RESULTS_PER_PAGE']


def _get_elasticsearch_endpoint_url():
    return app.config['ELASTICSEARCH_ENDPOINT_URI']


def _get_postcode_search_doc_type():
    return app.config['POSTCODE_SEARCH_DOC_TYPE']


def _get_address_search_doc_type():
    return app.config['ADDRESS_SEARCH_DOC_TYPE']
