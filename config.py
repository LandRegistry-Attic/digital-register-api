import os
from typing import Dict, Union

user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']
host = os.environ['POSTGRES_HOST']
port = os.environ['POSTGRES_PORT']
database = os.environ['POSTGRES_DB']
max_number = int(os.environ['MAX_NUMBER_SEARCH_RESULTS'])
search_results = int(os.environ['SEARCH_RESULTS_PER_PAGE'])
db_uri_template = 'postgresql+pg8000://{0}:{1}@{2}:{3}/{4}'
sql_alchemy_uri = db_uri_template.format(user, password, host, port, database)
logging_config_file_path = os.environ['LOGGING_CONFIG_FILE_PATH']
fault_log_file_path = os.environ['FAULT_LOG_FILE_PATH']
elasticsearch_endpoint_uri = os.environ['ELASTICSEARCH_ENDPOINT_URI']
elasticsearch_index_name = os.environ['ELASTICSEARCH_INDEX_NAME']
postcode_search_doc_type = os.environ['POSTCODE_SEARCH_DOC_TYPE']
address_search_doc_type = os.environ['ADDRESS_SEARCH_DOC_TYPE']
address_search_api_url = os.environ['ADDRESS_SEARCH_API']

CONFIG_DICT = {
    'DEBUG': False,
    'LOGGING': True,
    'SQLALCHEMY_DATABASE_URI': sql_alchemy_uri,
    'LOGGING_CONFIG_FILE_PATH': logging_config_file_path,
    'FAULT_LOG_FILE_PATH': fault_log_file_path,
    'ELASTICSEARCH_ENDPOINT_URI': elasticsearch_endpoint_uri,
    'ELASTICSEARCH_INDEX_NAME': elasticsearch_index_name,
    'MAX_NUMBER_SEARCH_RESULTS': max_number,
    'SEARCH_RESULTS_PER_PAGE': search_results,
    'POSTCODE_SEARCH_DOC_TYPE': postcode_search_doc_type,
    'ADDRESS_SEARCH_DOC_TYPE': address_search_doc_type,
    'ADDRESS_SEARCH_API': address_search_api_url,
}  # type: Dict[str, Union[bool, str, int]]

settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    CONFIG_DICT['LOGGING'] = False
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['TESTING'] = True
    CONFIG_DICT['FAULT_LOG_FILE_PATH'] = '/dev/null'
