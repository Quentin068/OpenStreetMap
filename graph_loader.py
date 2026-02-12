"""
    Fichier : graph_loader.py
    Rôle : Chargement de la carte via OSMnx.
"""
import osmnx as ox
import networkx as nx
import random
from config import PLACE_NAME, MAX_LIGHTS_SENT

def load_graph_data():
    print(f">>> TÉLÉCHARGEMENT DE {PLACE_NAME}...")

    # simplify=True est important pour réduire le nombre de noeuds inutiles
    G = ox.graph_from_place(PLACE_NAME, network_type='drive', simplify=True)
    G = nx.MultiDiGraph(G)

    print(f">>> CARTE CHARGÉE : {len(G.nodes)} intersections.")

    # 1. Bounds
    nodes_data = list(G.nodes(data=True))
    xs = [d['x'] for n, d in nodes_data]
    ys = [d['y'] for n, d in nodes_data]
    bounds = [min(xs), max(xs), min(ys), max(ys)]

    # 2. Préparation des routes
    routes_lines = []
    for u, v, k, data in G.edges(data=True, keys=True):
        length = float(data.get("length", 1.0))

        # Vitesse simulée : ~50km/h en ville
        speed_mps = (50 / 3.6)
        data['travel_time'] = length / speed_mps

        # Capacité : 1 voiture tous les 7m
        data['capacite'] = max(1, int(length / 7))
        data['vehicules_presents'] = 0
        data['blocked'] = False

        ux, uy = G.nodes[u]['x'], G.nodes[u]['y']
        vx, vy = G.nodes[v]['x'], G.nodes[v]['y']
        routes_lines.append([[ux, uy], [vx, vy]])

    # 3. Feux
    feux_nodes = [n for n in G.nodes() if G.degree(n) > 3]
    feux_config = {
        n: {'cycle': 40, 'offset': random.randint(0, 40), 'congestion_score': 0}
        for n in feux_nodes
    }

    # Sélection des feux à afficher (si trop nombreux)
    if len(feux_nodes) > MAX_LIGHTS_SENT:
        feux_display_nodes = random.sample(feux_nodes, MAX_LIGHTS_SENT)
    else:
        feux_display_nodes = feux_nodes

    return G, routes_lines, bounds, feux_config, feux_display_nodes, nodes_data

def find_nearest_node(G, x, y):
    return ox.distance.nearest_nodes(G, x, y)