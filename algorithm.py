import pandas as pd
import numpy as np
import networkx as nx
import sys
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors, LSHForest


def build_graph(journey_data, states_map, verbose=1):
    G = nx.MultiDiGraph()

    for state_id, state_name in states_map.iteritems():
        G.add_node(state_id, {"name": state_name})

    if verbose:
        total_customers = len(journey_data)

    for customer_num, (email, data) in enumerate(journey_data.iteritems()):
        if verbose:
            # print progress
            if not customer_num % 1000:
                sys.stdout.write('\rProcessing customer ' + str(customer_num) + ' of ' + str(total_customers))
                sys.stdout.flush()

        for i in range(len(data['journey']) - 1):
            u, v = data['journey'][i][0], data['journey'][i + 1][0]
            if G.has_edge(u, v):
                G.edge[u][v][0]["customers"].add(email)
                G.edge[u][v][0]["days"].append(data['journey'][i][1])
            else:
                G.add_edge(u, v, customers=set([data['id']]), days=[data['journey'][i][1]])
    if verbose:
        print ''

    # count the unique customers for each edge and the average delay of transition in days
    for u, v in G.edges_iter():
        G.edge[u][v][0]["customers"] = len(G.edge[u][v][0]["customers"])
        G.edge[u][v][0]["days"] = int(np.mean(G.edge[u][v][0]["days"]))

    return G


def compute_feature_matrix(journey_data, verbose=1):
    subpath_id_map = {}

    buff = {'subpath_id': 0}

    def extract_subpath_kernel_features(path):
        features = set([])

        for i in range(len(path)):
            for j in range(2, len(path) - i + 1):
                subpath = path[i: i + j]
                if subpath not in subpath_id_map:
                    subpath_id_map[subpath] = buff['subpath_id']
                    buff['subpath_id'] += 1
                features.add(subpath_id_map[subpath])

        return features

    row_ind = []
    col_ind = []

    if verbose:
        total_customers = len(journey_data)

    for customer_num, (email, data) in enumerate(journey_data.iteritems()):
        if verbose:
            # print progress
            if not customer_num % 1000:
                sys.stdout.write('\rProcessing customer ' + str(customer_num) + ' of ' + str(total_customers))
                sys.stdout.flush()
        path = ''.join([state[0] for state in data['journey']])
        features = extract_subpath_kernel_features(path)
        row_ind += [data['id']] * len(features)
        col_ind += list(features)

    if verbose:
        print ''

    sparse_feature_matrix = csr_matrix(([1] * len(row_ind), (row_ind, col_ind)),
                                       shape=(len(journey_data), len(subpath_id_map)))

    return sparse_feature_matrix


def compute_nearest_neighbor_model(sparse_feature_matrix,
                                   n_neighbors=2,
                                   metric='euclidean',
                                   sparse=True,
                                   approximate=False,
                                   n_candidates=4):
    feature_matrix = sparse_feature_matrix if sparse else sparse_feature_matrix.todense()

    if approximate:
        nn = LSHForest(n_neighbors=n_neighbors,
                       n_candidates=n_candidates).fit(feature_matrix)
    else:
        nn = NearestNeighbors(n_neighbors=n_neighbors,
                              algorithm='auto',
                              metric=metric,
                              n_jobs=-1).fit(feature_matrix)

    return nn


def get_nearest_neighbors(nn, query_emails, journey_data, sparse_feature_matrix, n_neighbors=2):
    email_ids = [journey_data[email]['id'] for email in query_emails]
    id_email_map = {v['id']: k for k, v in journey_data.iteritems()}
    distances, neighbors = nn.kneighbors(sparse_feature_matrix[email_ids, :],
                             n_neighbors=n_neighbors,
                             return_distance=True)

    neighbors_dict = {}

    for i, email_id in enumerate(email_ids):
        email = id_email_map[email_id]
        # sort neighbors ascending by distance
        email_neighbors = [n for (d, n) in sorted(zip(distances[i], neighbors[i]))]
        email_neighbors = [id_email_map[neighbor_email_id] for neighbor_email_id in email_neighbors]
        neighbors_dict[email] = email_neighbors

    return neighbors_dict

def predict_future_states(email, neighbors, journey_data, lookback_states_count=1):
    lookback_states = ''.join([state for state, _, _ in journey_data[email]['journey']])[-lookback_states_count:]

    predict_states = []
    predict_days = []

    for neigh in neighbors:
        neigh_journey = journey_data[neigh]['journey']
        neigh_states = ''.join([state for state, _, _ in neigh_journey])
        neigh_lookback_states_last_pos = neigh_states.rfind(lookback_states)
        if neigh_lookback_states_last_pos != -1 and neigh_lookback_states_last_pos < len(neigh_states) - lookback_states_count:
            neigh_next_state = neigh_states[neigh_lookback_states_last_pos + lookback_states_count]
            neigh_next_state_days = neigh_journey[neigh_lookback_states_last_pos + lookback_states_count - 1][1]
            predict_states.append(neigh_next_state)
            predict_days.append(neigh_next_state_days)

    predict_raw_df = pd.DataFrame({'state': predict_states, 'days': predict_days})
    total_relevant_neighbors = len(predict_raw_df)
    predictions = predict_raw_df.groupby('state').agg([len, np.mean])
    predictions['probability'] = predictions['days', 'len'] / total_relevant_neighbors
    predictions['expected_days'] = predictions['days', 'mean']
    del predictions['days']

    # predictions.rename(index=states_map, inplace=True)
    predictions.columns = predictions.columns.droplevel(1)

    return predictions
