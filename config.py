"""
    Fichier : config.py
    Rôle : Configuration pour Chalon-sur-Saône.
"""

# --- Paramètres Géographiques ---
PLACE_NAME = "Chalon-sur-Saône, France"

# --- Paramètres de Performance ---
# Chalon est plus petite que Paris, on peut se permettre plus de fluidité
FPS = 60                   # Fluidité maximale
EMIT_EVERY = 2             # Envoi au client toutes les 2 frames (30 FPS perçus)
DISPLAY_EVERY_N_CARS = 1   # 1 = On affiche TOUTES les voitures (pas de décimation)
DEFAULT_CARS = 600         # Nombre de voitures par défaut
MAX_LIGHTS_SENT = 500      # Nombre max de feux affichés

# --- Serveur ---
PORT = 5001
DEBUG_MODE = True

# --- Palette High Contrast ---
COLORS = {
    'bg': '#1a1a1a',
    'road': '#ffffff',
    'car': '#ffffff',
    'light_green': '#00ff00',
    'light_red': '#ff0000',
    'work': '#ffff00'
}