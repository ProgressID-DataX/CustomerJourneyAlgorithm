from datetime import datetime as dt

def invert_dict(d):
    return {v: k for k, v in d.iteritems()}

def prepare_customer_response(email, neighbors, journey_data, predictions, customer_details, max_similar_customers_count=10):
    def get_customer_details(cust_email):
        details = {
            'email': cust_email,
            'emailId': journey_data[cust_email]['id']
        }
        if customer_details is None:
            details['firstName'] = 'Hidden'
            details['lastName'] = 'Hidden'
            details['country'] = 'Hidden'
        else:
            row = customer_details.loc[cust_email]
            details['firstName'] = row['First Name']
            details['lastName'] = row['Last Name']
            details['country'] = row['Country']

        return details

    customer_response = {
        'details': get_customer_details(email),
        'journey': [{'state': state, 'date': dt.strftime(date, '%Y-%m-%dT%H:%M:%SZ') if date else ''} for state, _, date in journey_data[email]['journey']],
        'predictions': [{'state': row[0],
                         'expectedDays': row[1]['expected_days'],
                         'probability': row[1]['probability']} for row in predictions.iterrows()],
        'similarCustomers': [get_customer_details(neigh_email) for neigh_email in neighbors[:max_similar_customers_count]]
    }

    return customer_response
