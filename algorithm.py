import pandas as pd
import numpy as np
import networkx as nx
import sys
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors


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


def compute_nearest_neighbor_model(sparse_feature_matrix, n_neighbors=2, metric='euclidean'):
    nn = NearestNeighbors(n_neighbors=n_neighbors,
                          algorithm='auto',
                          metric=metric,
                          n_jobs=-1).fit(sparse_feature_matrix)
    return nn


def get_nearest_neighbors(nn, query_emails, journey_data, sparse_feature_matrix, n_neighbors=2):
    email_ids = [journey_data[email]['id'] for email in query_emails]
    id_email_map = {v['id']: k for k, v in journey_data.iteritems()}
    neigbors = nn.kneighbors(sparse_feature_matrix[email_ids, :],
                             n_neighbors=n_neighbors,
                             return_distance=False)

    neighbors_dict = {}

    for i, email_id in enumerate(email_ids):
        email = id_email_map[email_id]
        email_neighbors = [id_email_map[neighbor_email_id] for neighbor_email_id in neigbors[i, :]]
        neighbors_dict[email] = email_neighbors

    return neighbors_dict

def journey(email):
    pass
