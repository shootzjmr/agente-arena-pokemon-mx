"""
Mega Lucario ex Agent - Reglas intermedias
Basado en el notebook oficial de Kaggle de @kiyotah
(https://www.kaggle.com/code/kiyotah/a-sample-rule-based-agent-mega-lucario-ex-deck)
65 votes en Kaggle al momento de fork.

ESTRATEGIA:
- Mega Lucario ex como atacante principal
- Hariyama y Solrock como atacantes secundarios
- Cambia estratégicamente entre los 3

Este archivo es un PLACEHOLDER. El main.py real (508 líneas con toda la
lógica rule-based) se baja del notebook de Kaggle cuando prendamos
la instance de Vast.ai. Ver docs/setup.md para instrucciones.

POR QUÉ PLACEHOLDER:
- El main.py real depende de la API del engine (cg/) que solo está en Kaggle
- Cuando bajemos el dataset, vamos a tener el main.py completo
- Mientras tanto, este placeholder permite que la estructura del repo esté OK
"""

import os
import sys
import random
from collections import defaultdict

# NOTA: Estos imports requieren el engine (cg/) que viene con el dataset de Kaggle
# Cuando bajes el dataset, vas a tener cg/api.py disponible
try:
    from cg.api import (
        AreaType, CardType, EnergyType, Observation,
        SelectContext, OptionType, Card, Pokemon,
        all_card_data, to_observation_class
    )
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False
    print(f"[{__name__}] WARNING: engine cg/ no encontrado. Bajar dataset de Kaggle.", file=sys.stderr)


# ============================================================
# CARGAR DECK
# ============================================================
def load_deck() -> list[int]:
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    with open(file_path, "r") as f:
        csv = f.read().split("\n")
    return [int(csv[i]) for i in range(60)]


my_deck = load_deck()

# Decklist hardcodeada (basada en el agente original)
Makuhita = 673  # x2
Hariyama = 674  # x2
Lunatone = 675  # x2
Solrock = 676  # x3
Riolu = 677  # x3
Mega_Lucario_ex = 678  # x4
Dusk_Ball = 1102  # x4
Switch = 1123  # x2
Premium_Power_Pro = 1141  # x4
Fighting_Gong = 1142  # x4
Poke_Pad = 1152  # x4
Hero_Cape = 1159  # x1
Boss_Orders = 1182  # x2
Carmine = 1192  # x4
Lillie_Determination = 1227  # x4
Gravity_Mountain = 1252  # x2
Basic_Fighting_Energy = 6  # x13


# ============================================================
# AGENT (placeholder, la lógica real está en el notebook)
# ============================================================
def agent(obs_dict: dict) -> list[int]:
    """
    Por ahora: random agent. La lógica real rule-based (508 líneas) está
    en el notebook de Kaggle y se baja con la instance de Vast.ai.

    Cuando esté el main.py real, reemplazá este agent() con esa lógica.
    """
    if not HAS_ENGINE:
        # Sin engine, devolver deck (modo setup)
        return my_deck

    obs = to_observation_class(obs_dict)
    if obs.select is None:
        return my_deck

    n = len(obs.select.option)
    if n == 0:
        return []
    k = min(obs.select.maxCount, n)
    return random.sample(list(range(n)), k)


# ============================================================
# INSTRUCCIONES PARA COMPLETAR
# ============================================================
"""
CÓMO OBTENER EL MAIN.PY REAL:

1. Prendé una instance de Vast.ai (ver docs/setup.md)
2. Conectate por SSH
3. Bajá el notebook:
   kaggle kernels pull kiyotah/a-sample-rule-based-agent-mega-lucario-ex-deck
4. Extraé la cell 2 (el código del agente):
   python3 -c "
   import json
   nb = json.load(open('a-sample-rule-based-agent-mega-lucario-ex-deck.ipynb'))
   code = ''.join(nb['cells'][2]['source'])
   open('main_real.py', 'w').write(code)
   "
5. Reemplazá este archivo con el main_real.py (sacale la primera línea %%writefile)
6. Subilo a GitHub

El main.py real tiene:
- AttackPlan class con attacker, target, attack_index, remain_hp, energy
- state global: plan, pre_turn, ability_used
- helpers: get_card(), prize_count(), pokemon_score()
- 30+ select contexts manejados con heurísticas expertas
- Manejo de mega evolution, switching, retreating
"""
