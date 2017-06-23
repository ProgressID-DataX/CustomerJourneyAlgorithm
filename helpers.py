from datetime import datetime as dt

def invert_dict(d):
    return {v: k for k, v in d.iteritems()}

def prepare_customer_response(email, neighbors, journey_data, predictions, customer_details, max_similar_customers_count=10):
    def get_neighbor_details(neigh_email):
        # TODO: add customer details data
        return {'email': neigh_email,
                'emailId': journey_data[neigh_email]['id']}

    customer_response = {
        'details': {
            # TODO: add customer details data
            'email': email,
            'emailId': journey_data[email]['id']
        },
        'journey': [{'state': state, 'date': dt.strftime(date, '%Y-%m-%dT%H:%M:%SZ') if date else ''} for state, _, date in journey_data[email]['journey']],
        'predictions': [{'state': row[0],
                         'expectedDays': row[1]['expected_days'],
                         'probability': row[1]['probability']} for row in predictions.iterrows()],
        'similarCustomers': [get_neighbor_details(neigh_email) for neigh_email in neighbors[:max_similar_customers_count]]
    }

    return customer_response
