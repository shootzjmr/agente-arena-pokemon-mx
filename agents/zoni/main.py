"""
PLACEHOLDER - Agente de zoni

Este es un agente random. Reemplazar con la estrategia
real cuando el experto defina el mazo y la estrategia.

Para usar:
1. Editar scripts/build_deck.py con la decklist
2. Correr: python3 scripts/build_deck.py
3. Mover el deck.csv generado a este directorio
4. Reemplazar la función agent() con la lógica real
"""

import os
import random
import sys

try:
    from cg.api import to_observation_class
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False
    print(f"[{zoni}] WARNING: engine cg/ no encontrado.", file=sys.stderr)


def load_deck():
    deck_file = os.path.join(os.path.dirname(__file__), "deck.csv")
    if not os.path.exists(deck_file):
        # Deck random de respaldo
        return [random.randint(1, 1300) for _ in range(60)]
    with open(deck_file) as f:
        return [int(x) for x in f.read().strip().split("\n")[:60]]


my_deck = load_deck()


def agent(obs_dict):
    if not HAS_ENGINE:
        return my_deck
    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return my_deck
    n = len(obs.select.option)
    if n == 0:
        return []
    k = min(obs.select.maxCount, n)
    return random.sample(list(range(n)), k)
