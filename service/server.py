#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort, jsonify
import requests
import json
from sqlalchemy import Table, Column, String, MetaData, create_engine, Integer
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import select, or_
import pg8000

from service.models import TitleRegisterData
from service import app

def get_title_register(title_ref):
    return TitleRegisterData.query.get(title_ref)

@app.route('/titles/<title_ref>', methods=['GET'])
def get_title(title_ref):
    if title_ref == 'invalid-ref':
        abort(404)
    elif title_ref == 'DN1000':
        data = get_title_register(title_ref)
        result = {
          "data": data.register_data,
          "title_number": data.title_number,
          "geometry_data": data.geometry_data,
        }
        return jsonify(result)
    elif title_ref == 'DT160760':
        json_file = open('service/DT160760.json', 'r')
        sample_json = json_file.read()
        data = json.loads(sample_json)
        return jsonify(data.title_number)
    else:
        return jsonify(
            {
                "number": "DT122047",
                "last_changed": "2014-05-22 15:39:52",
                "address": "5 Granary Avenue Poundbury Dorchester DT1 4YY",
                "geometry": {
                    "index": {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [
                                      368002.61,
                                      78944.65
                                    ],
                                    [
                                      368002.58,
                                      78948.25
                                    ],
                                    [
                                      367991.851,
                                      78948.443
                                    ],
                                    [
                                      367991.75,
                                      78942.85
                                    ],
                                    [
                                      367991.73,
                                      78942.1
                                    ],
                                    [
                                      367998.35,
                                      78941.95
                                    ],
                                    [
                                      368002.638,
                                      78941.901
                                    ],
                                    [
                                      368002.61,
                                      78944.65
                                    ]
                                ]
                            ]
                        },
                        "properties": {
                            "graphic_type": "Bordered Polygon",
                            "feature_id": 4019,
                            "colour": 1,
                            "width": 0,
                            "render_attributes": {
                                "border_colour": 1,
                                "border_width": 0,
                                "exterior_edge_colour": 1,
                                "exterior_edge_thickness": 2.0,
                                "fill_colour": 25,
                                "fill_style": 9,
                                "render_level": "0"
                            }
                        },
                        "crs": {
                            "type": "name",
                            "properties": {
                                "name": "urn:ogc:def:crs:EPSG::27700"
                            }
                        }
                    }
                },
                "coordinates": {
                    "latitude": 45,
                    "longitude": 45,
                },
                "proprietors": [
                    {
                        "name": "Raymond Frank Easton",
                        "address": "5 Granary Avenue Poundbury Dorchester DT1 4YY"
                    },
                    {
                        "name": "Carol Easton",
                        "address": "5 Granary Avenue Poundbury Dorchester DT1 4YY"
                    }
                ],
                "lenders": [
                    {
                        "name": "Santander"
                    }
                ],
                "tenure_type": "Leasehold"
            }
        )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
