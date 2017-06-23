import pandas as pd
import numpy as np
import helpers
import sys


def load_journey_data(csv_file, verbose=1):
    if verbose:
        print 'Reading CSV file...'
    df = pd.read_csv(csv_file, encoding='utf8')
    if verbose:
        print 'Transforming CSV data...'
    df['Date'] = pd.to_datetime(df['Date'])
    states_map = {chr(ord('A') + i): state for i, state in enumerate(['Start'] + list(df['State'].unique()))}
    states_map_inv = helpers.invert_dict(states_map)
    journey_data = {}

    if verbose:
        total_emails = len(df['Email'].unique())

    for email_id, (email, group) in enumerate(df.sort_values('Date', ascending=True).groupby('Email')):
        if verbose:
            # print progress
            if not email_id % 1000:
                sys.stdout.write(u'\rProcessing customer ' + unicode(email_id) + u' of ' + unicode(total_emails))
                sys.stdout.flush()
        days = list((group['Date'].diff().fillna(0) / np.timedelta64(1, 'D')).astype(int)) + [0]
        states = ['A'] + [states_map_inv[state] for state in group['State']]
        dates = [None] + list(group['Date'])
        journey_data[email] = {'id': email_id, 'journey': zip(states, days, dates)}
    if verbose:
        print ''

    return journey_data, states_map

def load_customer_details_data(csv_file):
    df = pd.read_csv(csv_file, index_col='Email', encoding='utf-8')
    return df
