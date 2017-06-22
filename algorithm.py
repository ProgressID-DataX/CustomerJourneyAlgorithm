import pandas as pd
import numpy as np
import networkx as nx
import sys

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


def journey(email):
    pass
