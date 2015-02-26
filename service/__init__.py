import os, logging
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import requests

from config import CONFIG_DICT


app = Flask(__name__)
app.config.update(CONFIG_DICT)

db = SQLAlchemy(app)
