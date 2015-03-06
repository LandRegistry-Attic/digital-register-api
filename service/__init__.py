import logging
from logging import config
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import json

from config import CONFIG_DICT

def setup_logging(logging_config_file_path):
    try:
        with open(logging_config_file_path, 'rt') as file:
            config = json.load(file)
        logging.config.dictConfig(config)
    except IOError as e:
        raise(Exception('Failed to load logging configuration', e))

app = Flask(__name__)
app.config.update(CONFIG_DICT)

db = SQLAlchemy(app)
setup_logging(app.config['LOGGING_CONFIG_FILE_PATH'])
