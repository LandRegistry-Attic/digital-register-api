import faulthandler
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from service import logging_config

from config import CONFIG_DICT

# This causes the traceback to be written to the fault log file in case of serious faults
fault_log_file = open(CONFIG_DICT['FAULT_LOG_FILE_PATH'], 'a')
faulthandler.enable(file=fault_log_file)

app = Flask(__name__)
app.config.update(CONFIG_DICT)

db = SQLAlchemy(app)
logging_config.setup_logging()
