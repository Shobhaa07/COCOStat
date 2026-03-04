# Complete corrected code for cocostat_app (1).py

import json
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)

# Sample data
coconut_locations = [
    {'location': 'Hawaii', 'lamda': 19.8968, 'phi': -155.5828},
    {'location': 'Thailand', 'lamda': 15.8700, 'phi': 100.9925},
    {'location': 'India', 'lamda': 20.5937, 'phi': 78.9629}
]  # Properly closed list

@app.route('/coconuts', methods=['GET'])
def get_coconuts():
    return jsonify(coconut_locations)

@app.route('/coconut', methods=['POST'])
def add_coconut():
    new_coconut = request.json
    coconut_locations.append(new_coconut)
    return jsonify(coconut_locations), 201

if __name__ == '__main__':
    app.run(debug=True)