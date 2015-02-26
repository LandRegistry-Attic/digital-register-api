import os

CONFIG_DICT = {
    'DEBUG': False,
    'SQLALCHEMY_DATABASE_URI': os.environ['POSTGRES_REGISTER_DATABASE_URI'],
}

settings = os.environ.get('SETTINGS')

if settings == 'dev':
    CONFIG_DICT['DEBUG'] = True
elif settings == 'test':
    CONFIG_DICT['DEBUG'] = True
    CONFIG_DICT['TESTING'] = True
