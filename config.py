import os

user = os.environ['POSTGRES_USER']
password = os.environ['POSTGRES_PASSWORD']
host = os.environ['POSTGRES_HOST']
port = os.environ['POSTGRES_PORT']
database = os.environ['POSTGRES_DB']
db_uri_template = 'postgresql+pg8000://{0}:{1}@{2}:{3}/{4}'
sql_alchemy_uri = db_uri_template.format(user, password, host, port, database)
logging_config_file_path = os.environ['LOGGING_CONFIG_FILE_PATH']

CONFIG_DICT = {
    'DEBUG': False,
    'LOGGING': True,
    'SQLALCHEMY_DATABASE_URI': sql_alchemy_uri,
    'LOGGING_CONFIG_FILE_PATH': logging_config_file_path,
    'ELASTIC_SEARCH_ENDPOINT': os.environ['ELASTIC_SEARCH_ENDPOINT'],
}

settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    CONFIG_DICT['LOGGING'] = False
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['TESTING'] = True
