#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort, jsonify
import requests
import json
from sqlalchemy import Table, Column, String, create_engine
import pg8000

from service.models import TitleRegisterData

def get_title_register(title_ref):
    return TitleRegisterData.query.get(title_ref)

@app.route('/titles/<title_ref>', methods=['GET'])
def get_title(title_ref):
    data = get_title_register(title_ref)
    if data:
        result = {
          "data": data.register_data,
          "title_number": data.title_number,
          "geometry_data": data.geometry_data,
        }
        return jsonify(result)
    else:
        #Title not found
        abort(404)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
