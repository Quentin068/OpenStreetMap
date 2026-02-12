"""
    Fichier : app.py
    Lancer avec : python app.py
"""
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from config import FPS, EMIT_EVERY, DISPLAY_EVERY_N_CARS, PORT, DEFAULT_CARS
import graph_loader
from simulation import SimulationState

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')

# Chargement
G, routes_lines, bounds, feux_config, feux_display_nodes, nodes_data = graph_loader.load_graph_data()
sim_state = SimulationState(G, nodes_data)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def on_connect():
    emit('init_data', {'bounds': bounds, 'roads': routes_lines})

@socketio.on('add_roadwork')
def on_work(data):
    try:
        n = graph_loader.find_nearest_node(G, data['x'], data['y'])
        for u, v, k in G.out_edges(n, keys=True):
            G[u][v][k]['blocked'] = True

        node_geo = G.nodes[n]
        sim_state.roadworks.append([node_geo['x'], node_geo['y']])
    except: pass

@socketio.on('toggle_ai')
def on_ai(data):
    sim_state.ai_active = bool(data.get('active', False))

def run_simulation():
    sim_state.running = True
    while sim_state.running:
        start_time = time.time()

        # IA Update
        sim_state.update_ai(feux_config)

        positions = []
        blocked = 0

        # Mouvement des voitures
        for v in sim_state.flotte:
            res = v.avancer(sim_state.frame, feux_config)

            # On récupère la position pour l'affichage
            coords = v.get_info()
            if coords: positions.append(coords)

            if res == 2: sim_state.stats_trips += 1
            elif res == 0: blocked += 1

        cong = (blocked / len(sim_state.flotte) * 100) if sim_state.flotte else 0

        # Envoi au client (Throttling pour perf)
        if sim_state.frame % EMIT_EVERY == 0:

            # Feux (sous-ensemble si nécessaire)
            lights = []
            for n in feux_display_nodes:
                cfg = feux_config[n]
                is_green = (((sim_state.frame + cfg['offset']) % cfg['cycle']) < (cfg['cycle'] / 2))
                lights.append({
                    'x': G.nodes[n]['x'],
                    'y': G.nodes[n]['y'],
                    'color': '#00ff00' if is_green else '#ff0000'
                })

            # Décimation des voitures (si configuré, par défaut 1 pour Chalon)
            display_cars = positions[::DISPLAY_EVERY_N_CARS]

            socketio.emit('update', {
                'cars': display_cars,
                'lights': lights,
                'roadworks': sim_state.roadworks,
                'stats': {
                    'trips': sim_state.stats_trips,
                    'congestion': cong,
                    'avg_cycle': sim_state.avg_cycle
                }
            })

        sim_state.frame += 1

        # Gestion FPS
        elapsed = time.time() - start_time
        wait = max(0, (1/FPS) - elapsed)
        time.sleep(wait)

@socketio.on('start_sim')
def start(data):
    if not sim_state.running:
        nb = int(data.get('nb', DEFAULT_CARS))
        sim_state.reset(nb, feux_config)
        sim_state.running = True
        threading.Thread(target=run_simulation).start()

@socketio.on('stop_sim')
def stop():
    sim_state.running = False

if __name__ == '__main__':
    print(f"Server running on http://127.0.0.1:{PORT}")
    socketio.run(app, debug=True, host='0.0.0.0', port=PORT)