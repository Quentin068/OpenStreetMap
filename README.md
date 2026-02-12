# 🚦 Traffic Manager Ultimate - Smart City Simulation

**Traffic Manager Ultimate** est un simulateur de trafic routier en temps réel basé sur des données géographiques réelles (OpenStreetMap). Il intègre une **IA de type "Smart Grid"** capable de réguler dynamiquement les feux tricolores pour fluidifier la circulation.

Le projet est conçu pour être performant, capable de gérer des petites villes (**Chalon-sur-Saône**) comme des métropoles denses (**Paris Intra-muros**), grâce à une architecture modulaire et optimisée.

![Status](https://img.shields.io/badge/Status-Stable-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## ✨ Fonctionnalités Clés

* **🌍 Cartographie Réelle** : Utilise `OSMnx` pour télécharger et générer le graphe routier de n'importe quelle ville.
* **🧠 IA Smart Grid** : Algorithme adaptatif qui analyse la congestion aux intersections et ajuste la durée des feux en temps réel.
* **⚡ Haute Performance** : Moteur physique avec interpolation de mouvement, throttling réseau et décimation d'affichage pour supporter > 3000 véhicules.
* **🎨 UI "High Contrast"** : Interface web industrielle (Noir/Blanc/Néon) optimisée pour la lisibilité.
* **🚧 Interaction Live** :
    * **Zoom & Pan** fluide (souris).
    * **Clic Droit** pour créer des zones de travaux/accidents.
    * **Contrôle de densité** (curseur de population).
* **📊 Monitoring** : Graphiques en temps réel (Chart.js) montrant l'évolution des cycles de feux et de la congestion.

## 📂 Structure du Projet

L'architecture est modulaire pour faciliter la maintenance :

```text
/traffic_project
│
├── config.py           # ⚙️ Configuration (Ville, Couleurs, Performance)
├── graph_loader.py     # 🗺️ Chargement OSM & Calculs géométriques
├── simulation.py       # 🚗 Moteur physique & Logique IA
├── app.py              # 🚀 Serveur Flask & WebSocket
│
└── templates/
    └── index.html      # 🖥️ Frontend (Canvas + Chart.js)
```

## 🚀 Installation

### 1. Prérequis

* Python 3.8 ou supérieur.
* Un navigateur web moderne (Chrome, Firefox, Edge).

### 2. Installation des dépendances

Installez les bibliothèques nécessaires via pip :

```bash
pip install flask flask-socketio osmnx networkx numpy
```

### 3. Lancement

Exécutez le fichier principal :

```bash
python app.py
```

**Premier lancement** : Le téléchargement de la carte (surtout pour Paris) peut prendre 1 à 3 minutes. Ne fermez pas la console.

Une fois prêt, ouvrez votre navigateur sur : **http://127.0.0.1:5001**

## ⚙️ Configuration (Changer de Ville)

Pour basculer entre Chalon-sur-Saône et Paris, modifiez le fichier `config.py`.

### Pour Chalon-sur-Saône (Fluide et précis)

```python
PLACE_NAME = "Chalon-sur-Saône, France"
FPS = 60                   # Haute fluidité
EMIT_EVERY = 2             # Envoi fréquent
DISPLAY_EVERY_N_CARS = 1   # Afficher toutes les voitures
MAX_LIGHTS_SENT = 500
```

### Pour Paris (Optimisé pour la charge)

```python
PLACE_NAME = "Paris, France"
FPS = 30                   # Calculs plus lents pour économiser le CPU
EMIT_EVERY = 3             # Moins d'envois réseau
DISPLAY_EVERY_N_CARS = 2   # Affiche 1 voiture sur 2 pour ne pas saturer le navigateur
MAX_LIGHTS_SENT = 1500
```

**Note** : Si vous changez de ville, supprimez le dossier cache (s'il a été créé par osmnx) ou redémarrez simplement le script. Le premier chargement sera long.

## 🎮 Utilisation

### Contrôles de la Carte

* **Molette Souris** : Zoom Avant / Arrière (centré sur le curseur).
* **Clic Gauche + Glisser** : Déplacer la carte (Panoramique).
* **Clic Droit** : Créer un incident (Travaux) à l'endroit cliqué. Les voitures devront faire demi-tour.

### Tableau de Bord

* **Slider** : Ajustez le nombre de voitures (ex: 2000).
* **Bouton INITIALISER** : Génère la flotte et place les véhicules.
* **Bouton SMART GRID (IA)** : Active l'intelligence artificielle des feux.

## 🧠 Comment fonctionne l'IA ?

L'IA n'est pas un réseau de neurones ("Black Box"), mais un système de régulation par rétroaction (Feedback Loop) :

1. **Sensation** : Chaque feu possède un `congestion_score`. Si une voiture attend au feu rouge ou est bloquée dans un bouchon, ce score augmente.

2. **Décision** : Toutes les 100 frames, l'IA analyse le score :
   * Si le score est **élevé (> 20)** : Cela signifie qu'il y a trop d'attente. L'IA allonge la durée du cycle (jusqu'à 120s) pour laisser passer plus de monde lors de la phase verte.
   * Si le score est **faible (< 5)** : Le carrefour est vide. L'IA raccourcit le cycle (jusqu'à 20s) pour dynamiser le trafic.

3. **Action** : Le nouveau temps de cycle est appliqué immédiatement.

## 🛠️ Dépannage

### Erreur `KeyError: 'light_green'`

Assurez-vous que votre fichier `config.py` utilise bien les clés `light_green` et `light_red` dans le dictionnaire `COLORS`, et non `light_go` ou `light_stop`.

### Le navigateur rame (Lag)

* Si vous simulez Paris, réduisez le nombre de voitures.
* Dans `config.py`, augmentez `DISPLAY_EVERY_N_CARS` à 3 ou 4.

### Les voitures volent à travers les immeubles

C'est normal si vous changez brutalement le Zoom pendant une interpolation. Attendez quelques secondes, la simulation se recalera.
