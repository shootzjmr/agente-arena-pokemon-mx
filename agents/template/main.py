"""
Template base para un agente del Agente Arena.

CÓMO USARLO:
1. Copiá esta carpeta a agents/TU_HANDLE/
2. Modificá la función agent() abajo con tu estrategia
3. Cambiá el deck.csv por tu mazo
4. Listo, ya podés correr la arena

IMPORTANTE: Tu agente debe respetar las reglas de TCG.
Si devuelve acciones inválidas, el engine tira IndexError.
"""

import os
import sys
import random
from collections import defaultdict

# Importar la API del engine de Kaggle
# El engine (cg/) tiene que estar en el mismo directorio o en PYTHONPATH
from cg.api import (
    AreaType, CardType, EnergyType, Observation,
    SelectContext, OptionType, Card, Pokemon,
    all_card_data, to_observation_class
)


# ============================================================
# CARGAR TU MAZO
# ============================================================
# Cambiá la ruta si tu deck.csv está en otro lado
def load_deck() -> list[int]:
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    if not os.path.exists(file_path):
        # Fallback: deck random
        return [random.randint(1, 1300) for _ in range(60)]
    with open(file_path, "r") as f:
        csv = f.read().split("\n")
    deck = []
    for i in range(60):
        deck.append(int(csv[i]))
    return deck


my_deck = load_deck()

# ============================================================
# CARGAR METADATA DE TODAS LAS CARTAS
# ============================================================
# Esto te da info de cada carta (HP, stage, ataques, etc.)
# Sin esto, tu agente no sabe qué carta es qué
try:
    all_card = all_card_data()
    card_table = {c.cardId: c for c in all_card}
    print(f"[{__name__}] Cargadas {len(card_table)} cartas", file=sys.stderr)
except Exception as e:
    card_table = {}
    print(f"[{__name__}] WARNING: no pude cargar card_table: {e}", file=sys.stderr)


# ============================================================
# HELPERS (funciones útiles que podés usar)
# ============================================================

def get_card(obs, area, index, player_index):
    """Obtiene una carta de una zona específica."""
    ps = obs.current.players[player_index]
    if area == AreaType.HAND:
        return ps.hand[index] if index < len(ps.hand) else None
    elif area == AreaType.ACTIVE:
        return ps.active[index] if index < len(ps.active) else None
    elif area == AreaType.BENCH:
        return ps.bench[index] if index < len(ps.bench) else None
    elif area == AreaType.DISCARD:
        return ps.discard[index] if index < len(ps.discard) else None
    return None


def get_my_index(obs):
    """Devuelve tu índice (0 o 1)."""
    return obs.current.yourIndex


def get_opponent_index(obs):
    """Devuelve el índice del oponente."""
    return 1 - get_my_index(obs)


# ============================================================
# AGENT: ACÁ VA TU ESTRATEGIA
# ============================================================

def agent(obs_dict: dict) -> list[int]:
    """
    Función principal del agente.

    Reglas:
    - Devolver una lista de índices de acciones
    - Cada índice debe estar en range(0, len(obs.select.option))
    - Longitud entre obs.select.minCount y obs.select.maxCount
    - Sin duplicados

    Returns:
        list[int]: Lista de índices de acciones a tomar
    """
    obs = to_observation_class(obs_dict)

    # En la selección inicial, devolver el mazo
    if obs.select is None:
        return my_deck

    # Si no hay opciones, devolver lista vacía
    if len(obs.select.option) == 0:
        return []

    # ========================================================
    # PLACEHOLDER: Por ahora, hacer random
    # Acá es donde vos (o tus amigos expertos) definen la estrategia
    # ========================================================
    n = len(obs.select.option)
    k = min(obs.select.maxCount, n)
    return random.sample(list(range(n)), k)


# ============================================================
# NO TOCAR (esto lo usa Kaggle)
# ============================================================
if __name__ == "__main__":
    # Test básico
    print("Deck:", my_deck[:5], "...")
    print("Card table size:", len(card_table))
