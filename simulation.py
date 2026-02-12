"""
    Fichier : simulation.py
    Rôle : Moteur physique avec interpolation de mouvement.
"""
import networkx as nx
import random
import numpy as np
from config import FPS


class Vehicule:
    def __init__(self, graph, nodes_data):
        self.graph = graph
        self.nodes_data = nodes_data  # Liste optimisée pour pick random
        self.is_police = (random.random() < 0.02)

        # État sur l'arête (interpolation)
        self.current_edge = None  # (u, v, k)
        self.on_edge = False
        self.edge_len = 0.0
        self.edge_pos = 0.0
        self.edge_u = None
        self.edge_v = None

        self.reset()

    def _free_current_edge(self):
        if self.current_edge:
            ou, ov, ok = self.current_edge
            try:
                ed = self.graph[ou][ov][ok]
                ed['vehicules_presents'] = max(0, ed['vehicules_presents'] - 1)
            except:
                pass
            self.current_edge = None

    def reset(self):
        self._free_current_edge()
        self.on_edge = False
        self.edge_pos = 0.0
        self.patience = 0

        try:
            # Choix rapide via la liste pré-chargée
            start = random.choice(self.nodes_data)[0]
            end = random.choice(self.nodes_data)[0]
            self.path = nx.shortest_path(self.graph, start, end, weight='travel_time')
            self.pos_idx = 0
        except:
            self.path = []
            self.pos_idx = 0

    def _pick_best_edge(self, u, v):
        # Choisir la meilleure clé (route) entre deux noeuds
        keys = self.graph[u][v]
        return min(keys, key=lambda k: keys[k].get('travel_time', float('inf')))

    def get_info(self):
        if not self.path: return None

        # INTERPOLATION VISUELLE
        if self.on_edge and self.edge_len > 0:
            ux, uy = self.graph.nodes[self.edge_u]['x'], self.graph.nodes[self.edge_u]['y']
            vx, vy = self.graph.nodes[self.edge_v]['x'], self.graph.nodes[self.edge_v]['y']
            t = min(1.0, max(0.0, self.edge_pos / self.edge_len))

            # Formule lerp (Linear Interpolation)
            cur_x = ux + (vx - ux) * t
            cur_y = uy + (vy - uy) * t
            return (cur_x, cur_y, 1 if self.is_police else 0)

        # Fallback si sur un noeud
        n = self.graph.nodes[self.path[self.pos_idx]]
        return (n['x'], n['y'], 1 if self.is_police else 0)

    def avancer(self, frame, feux_config):
        if not self.path or self.pos_idx >= len(self.path) - 1:
            self.reset()
            return 2

        dt = 1.0 / FPS

        # --- CAS 1 : SUR UNE ROUTE (Entre deux noeuds) ---
        if self.on_edge:
            ou, ov, ok = self.current_edge
            ed = self.graph[ou][ov][ok]

            # Calcul vitesse (m/s)
            travel_time = max(0.1, float(ed.get('travel_time', 1.0)))
            speed = self.edge_len / travel_time

            self.edge_pos += speed * dt

            # Arrivée au bout de la route
            if self.edge_pos >= self.edge_len:
                self._free_current_edge()
                self.on_edge = False
                self.pos_idx += 1
                return 1  # Avance d'un noeud
            return 1  # En mouvement

        # --- CAS 2 : A UN INTERSECTION (Choix prochaine route) ---
        u, v = self.path[self.pos_idx], self.path[self.pos_idx + 1]

        try:
            best_k = self._pick_best_edge(u, v)
            edge = self.graph[u][v][best_k]
        except:
            self.reset()
            return 0

        # Vérif Travaux
        if edge.get('blocked', False):
            self.reset()
            return 0

        # Vérif Feu Rouge
        if u in feux_config and not self.is_police:
            cfg = feux_config[u]
            is_green = (((frame + cfg['offset']) % cfg['cycle']) < (cfg['cycle'] / 2))
            if not is_green:
                cfg['congestion_score'] += 1
                return 0  # Stop

        # Vérif Capacité
        if edge['vehicules_presents'] < edge['capacite'] or self.is_police:
            edge['vehicules_presents'] += 1
            self.current_edge = (u, v, best_k)

            # Setup Interpolation
            self.on_edge = True
            self.edge_u, self.edge_v, self.edge_k = u, v, best_k
            self.edge_len = float(edge.get('length', 1.0))
            self.edge_pos = 0.0
            self.patience = 0
            return 1

        # Bloqué (Bouchon)
        self.patience += 1
        if u in feux_config: feux_config[u]['congestion_score'] += 0.5
        if self.patience > 100: self.reset()
        return 0


class SimulationState:
    def __init__(self, graph, nodes_data):
        self.graph = graph
        self.nodes_data = nodes_data
        self.running = False
        self.flotte = []
        self.frame = 0
        self.roadworks = []
        self.ai_active = False
        self.stats_trips = 0
        self.avg_cycle = 40

    def reset(self, nb_voitures, feux_config):
        self.frame = 0
        self.stats_trips = 0
        self.roadworks = []
        self.ai_active = False
        self.avg_cycle = 40

        # Reset Map
        for u, v, k, d in self.graph.edges(data=True, keys=True):
            d['blocked'] = False
            d['vehicules_presents'] = 0

        for n in feux_config:
            feux_config[n]['cycle'] = 40
            feux_config[n]['congestion_score'] = 0

        # Init flotte
        print(f">>> CRÉATION DE {nb_voitures} VÉHICULES...")
        self.flotte = [Vehicule(self.graph, self.nodes_data) for _ in range(int(nb_voitures))]

    def update_ai(self, feux_config):
        if not self.ai_active or self.frame % 100 != 0: return

        cycles = []
        for n, cfg in feux_config.items():
            score = cfg['congestion_score']
            if score > 20:
                cfg['cycle'] = min(120, cfg['cycle'] + 10)
            elif score < 5:
                cfg['cycle'] = max(20, cfg['cycle'] - 5)

            cfg['congestion_score'] = 0
            cycles.append(cfg['cycle'])

        if cycles: self.avg_cycle = np.mean(cycles)
