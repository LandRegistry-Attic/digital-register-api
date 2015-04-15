import faulthandler
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from service import logging_config

from config import CONFIG_DICT

# This causes the traceback to be written to stderr in case of faults
faulthandler.enable()

app = Flask(__name__)
app.config.update(CONFIG_DICT)

db = SQLAlchemy(app)
logging_config.setup_logging()
