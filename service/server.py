#!/usr/bin/env python
from service import app
import os
from flask import Flask, abort
import requests

@app.route('/titles/<title_ref>', methods=['GET'])
def get_title(title_ref):
    if title_ref == 'invalid-ref':
        abort(404)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
