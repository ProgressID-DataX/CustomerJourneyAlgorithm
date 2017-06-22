from flask import Flask, jsonify, request, Response, abort
from networkx.readwrite import json_graph
import algorithm as algo
import data
import os

config = {
    'journey_csv_file': 'data\\journey.csv'
}

app = Flask(__name__)

internal_state = {}

def init():
    print 'Loading journey data...'
    journey_data, states_map = data.load_journey_data(config['journey_csv_file'])
    internal_state['journey_data'] = journey_data
    internal_state['states_map'] = states_map
    print 'Building journey graph...'
    internal_state['journey_graph'] = algo.build_graph(journey_data, states_map)
    print 'Initialization ready!'

@app.before_request
def check_if_init():
    if 'journey_graph' not in internal_state:
        abort(403)

@app.after_request
def apply_caching(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.errorhandler(403)
def page_not_found(e):
    return 'There was a problem initializing the service.', 403

@app.route('/')
def index():
    return "Possible endpoints:<br>/journey<br>/journey/[Lead ID]<br>/leads"

@app.route('/leads', methods=['GET'])
def get_leads():
    return 'leads'

@app.route('/journey', methods=['GET'])
def get_journey_graph():
    journey_json = json_graph.node_link_data(internal_state['journey_graph'])
    return jsonify({'journey': journey_json})

@app.route('/journey/<string:email>', methods=['GET'])
def get_journey_lead(email):
    return open('data\journeyByEmail.json').read()

if __name__ == '__main__':
    print 'Starting service...'
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init()
    app.run(debug=True, host='192.168.144.23', port=5000)
