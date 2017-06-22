from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return "Possible endpoints:<br>/journey<br>/journey/[Lead ID]<br>/leads"

@app.route('/leads', methods=['GET'])
def get_leads():
    return 'leads'

@app.route('/journey', methods=['GET'])
def get_journey_graph():
    test_json = [
        {
            'id': 1,
            'title': u'Buy groceries',
            'description': u'Milk, Cheese, Pizza, Fruit, Tylenol',
            'done': False
        },
        {
            'id': 2,
            'title': u'Learn Python',
            'description': u'Need to find a good Python tutorial on the web',
            'done': False
        }
    ]
    return jsonify({'journey': test_json})

@app.route('/journey/<string:lead_id>', methods=['GET'])
def get_journey_lead(lead_id):
    return lead_id

if __name__ == '__main__':
    app.run(debug=True, host='192.168.144.23', port=8080)
