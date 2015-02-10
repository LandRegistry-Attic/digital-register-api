import os

class Config(object):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'postgresql+pg8000://postgres:password@172.16.42.43:5432/register_data'

class DevelopmentConfig(Config):
    DEBUG = True

class TestConfig(DevelopmentConfig):
    TESTING = True
