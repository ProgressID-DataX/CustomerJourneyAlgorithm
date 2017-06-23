from flask import Flask, jsonify, request, Response, abort
from networkx.readwrite import json_graph
import algorithm as algo
import data
import os
from IPython.display import display, HTML

config = {
    'journey_csv_file': 'data\\journey.csv',
    # 'journey_csv_file': 'data\\journey_big_test.csv',
    # 'journey_csv_file': 'data\\some_data_2.csv',
    'metric': 'euclidean',
    'sparse': True,
    'approximate': False,
    'n_neighbors': 100,
    'n_candidates': 200,
    'lookback_states_count': 1
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

    print 'Computing feature matrix...'
    internal_state['sparse_feature_matrix'] = algo.compute_feature_matrix(internal_state['journey_data'])

    print 'Computing nearest neighbor model...'
    internal_state['nn'] = algo.compute_nearest_neighbor_model(internal_state['sparse_feature_matrix'],
                                                               metric=config['metric'],
                                                               sparse=config['sparse'],
                                                               n_neighbors=config['n_neighbors'],
                                                               approximate=config['approximate'])

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
    lookback_states_count = int(request.args.get('lookback_states_count'))

    neighbors_dict = algo.get_nearest_neighbors(internal_state['nn'],
                                                [email],
                                                internal_state['journey_data'],
                                                internal_state['sparse_feature_matrix'],
                                                n_neighbors=config['n_neighbors'])

    predictions = algo.predict_future_states(email,
                                             neighbors_dict[email],
                                             internal_state['journey_data'],
                                             internal_state['states_map'],
                                             lookback_states_count=lookback_states_count if lookback_states_count else config['lookback_states_count'])

    neighbors_str = ['{}:{}'.format(neighbor_email, internal_state['journey_data'][neighbor_email]['journey']) for neighbor_email in neighbors_dict[email]]

    return str(internal_state['states_map']) + '<br>' + str(predictions.to_html()) + '<br>\n'.join([str(neighbors_dict), str(internal_state['journey_data'])])

if __name__ == '__main__':
    print 'Starting service...'
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        init()
    app.run(debug=True, host='192.168.144.23', port=5000)
