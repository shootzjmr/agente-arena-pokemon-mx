"""
TEMPLATE AVANZADO - Agente Plan-First con heurística real.

Wrapper de la heurística `pokemon_tcg_agent/heuristic_v2.py` con
fallback al comportamiento del template original cuando:
- No se puede importar la heurística (no estamos en vast.ai)
- No hay engine disponible
- Hay un bug en la heurística (la capturamos y caemos a safe-random)

CÓMO USARLO:
1. Copiá esta carpeta a agents/TU_HANDLE/
2. Reemplazá deck.csv con tu mazo (o el que viene por defecto)
3. (Opcional) Reemplazá la heurística por tu propia estrategia

NOTA: Este template NO usa la heurística real por defecto porque
necesita acceso al engine cg/ y a la heurística que vive en
pokemon-tcg-agent/. La activa cuando los encuentra disponibles.
"""

import os
import sys
import random
from collections import defaultdict

# ============================================================
# INTENTAR IMPORTAR LA HEURÍSTICA REAL
# ============================================================
# La heurística vive en /workspace/pokemon-tcg-agent/agent/heuristic.py
# (en la instance de Vast.ai). En otros lados, cae al placeholder.
HEURISTIC_AVAILABLE = False
try:
    sys.path.insert(0, "/workspace/pokemon-tcg-agent")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from agent.heuristic import plan_first_action as _heuristic_fn
    HEURISTIC_AVAILABLE = True
    print(f"[{__name__}] Heurística real cargada.", file=sys.stderr)
except (ImportError, ModuleNotFoundError):
    print(f"[{__name__}] Heurística no disponible, usando placeholder.", file=sys.stderr)

# ============================================================
# INTENTAR IMPORTAR LA API DEL ENGINE
# ============================================================
try:
    from cg.api import (
        AreaType, CardType, EnergyType, Observation,
        SelectContext, OptionType, Card, Pokemon,
        all_card_data, to_observation_class
    )
    HAS_ENGINE = True
except (ImportError, ModuleNotFoundError):
    HAS_ENGINE = False
    print(f"[{__name__}] WARNING: engine cg/ no encontrado.", file=sys.stderr)


# ============================================================
# CARGAR MAZO
# ============================================================
def load_deck() -> list[int]:
    file_path = os.path.join(os.path.dirname(__file__), "deck.csv")
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/deck.csv"
    if not os.path.exists(file_path):
        # Fallback: deck random (NO recomendado, será descalificado)
        print(f"[{__name__}] WARNING: no encontré deck.csv, usando random.", file=sys.stderr)
        return [random.randint(1, 1300) for _ in range(60)]
    with open(file_path, "r") as f:
        lines = [l for l in f.read().strip().split("\n") if l.strip()][:60]
    return [int(x) for x in lines]


my_deck = load_deck()


# ============================================================
# CARGAR METADATA DE CARTAS
# ============================================================
card_table: dict = {}
try:
    all_card = all_card_data()
    card_table = {c.cardId: c for c in all_card}
    print(f"[{__name__}] Cargadas {len(card_table)} cartas.", file=sys.stderr)
except Exception as e:
    print(f"[{__name__}] WARNING: no pude cargar card_table: {e}", file=sys.stderr)


# ============================================================
# HELPERS
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


def get_my_index(obs) -> int:
    return obs.current.yourIndex


def get_opponent_index(obs) -> int:
    return 1 - get_my_index(obs)


# ============================================================
# CONTEXTO (para que la heurística tome decisiones informadas)
# ============================================================
class GameContext:
    """Snapshot ligero del estado del juego que consume la heurística."""

    def __init__(self, obs):
        self.obs = obs
        self.my_idx = get_my_index(obs)
        self.opp_idx = get_opponent_index(obs)
        self.turn = obs.current.turnCount
        self.my_active = obs.current.players[self.my_idx].active
        self.my_bench = obs.current.players[self.my_idx].bench
        self.my_hand = obs.current.players[self.my_idx].hand
        self.my_prizes = obs.current.players[self.my_idx].prizeCount
        self.opp_active = obs.current.players[self.opp_idx].active
        self.opp_bench = obs.current.players[self.opp_idx].bench
        self.opp_prizes = obs.current.players[self.opp_idx].prizeCount
        self.deck_left = obs.current.players[self.my_idx].deckCardsLeft


# ============================================================
# ESTRATEGIA: HEURÍSTICA PLAN-FIRST
# ============================================================
def plan_first_strategy(obs, ctx: GameContext) -> list[int]:
    """
    Estrategia plan-first: evalúa roles y matchup antes de decidir.

    Filosofía (de la heurística real):
    1. PRIORITY: ¿Puedo ganar este turno? (lethal)
    2. SETUP: ¿Necesito preparar piezas para el próximo turno?
    3. PRESSURE: ¿Cuál es el mejor ataque?
    4. DEFEND: Si el rival amenaza lethal, defiendo
    5. PASS: Solo si nada más aplica

    NOTA: Esta versión es un stub que demuestra la API. La heurística
    real (heuristic.py) tiene la lógica completa con roles por deck.
    Para usarla, importá desde pokemon-tcg-agent/agent/heuristic.py.
    """
    select = obs.select
    options = select.option
    n = len(options)

    # Clasificar opciones por tipo
    cards_in_hand = set(c.cardId for c in ctx.my_hand)

    # Si la heurística real está disponible, usarla
    if HEURISTIC_AVAILABLE:
        try:
            return _heuristic_fn(obs, ctx)
        except Exception as e:
            print(f"[{__name__}] Heurística falló: {e}. Fallback.", file=sys.stderr)

    # === FALLBACK: lógica mejorada vs random ===
    # Preferir cartas básicas (seteo), energies, luego el resto
    def score_option(opt):
        opt_card = getattr(opt, 'card', None)
        if opt_card is None:
            return 0
        # Bonus por cartas de setup (Stadium, Ball, Switch)
        if opt_card.cardId in {131, 175,  # Ultra Ball, Dusk Ball
                                170, 133,  # Cyrano, Crispin
                                157, 145,  # Prime Catcher, Ciphermaniac
                                94}:       # Wondrous Patch
            return 10
        # Bonus por energies
        if hasattr(opt_card, 'energyType') and opt_card.energyType:
            return 5
        # Bonus por attackers principales
        return 1

    scored = [(i, score_option(opt)) for i, opt in enumerate(options)]
    scored.sort(key=lambda x: -x[1])

    k = min(select.maxCount, n) if select.maxCount > 0 else min(select.minCount, n)
    k = max(k, select.minCount)
    k = min(k, n)
    if k <= 0:
        return []
    return [i for i, _ in scored[:k]]


# ============================================================
# AGENTE PRINCIPAL
# ============================================================
def agent(obs_dict: dict) -> list[int]:
    """
    Función principal del agente.

    Pipeline:
    1. Si no hay engine, devolver el mazo (game init)
    2. Parsear observación
    3. Construir contexto
    4. Llamar a la heurística plan-first
    5. Validar la respuesta (cantidad, rango, sin duplicados)
    6. Fallback safe-random si todo falla
    """
    # === Game init: devolver mazo ===
    if not HAS_ENGINE:
        return my_deck

    try:
        obs = to_observation_class(obs_dict)
    except Exception as e:
        print(f"[{__name__}] ERROR parseando obs: {e}", file=sys.stderr)
        return my_deck

    # === Sin selección: devolver mazo ===
    if obs.select is None:
        return my_deck

    # === Sin opciones: nada que hacer ===
    if len(obs.select.option) == 0:
        return []

    # === Estrategia ===
    try:
        ctx = GameContext(obs)
        actions = plan_first_strategy(obs, ctx)
    except Exception as e:
        print(f"[{__name__}] ERROR en estrategia: {e}", file=sys.stderr)
        # Fallback a safe-random
        n = len(obs.select.option)
        k = min(obs.select.maxCount, n) if obs.select.maxCount > 0 else 1
        k = max(k, obs.select.minCount)
        k = min(k, n)
        actions = random.sample(list(range(n)), k) if k > 0 else []

    # === Validar ===
    actions = _validate_actions(actions, obs.select)

    # === Defensa final: nunca devolver inválido ===
    if not actions and obs.select.minCount == 0:
        return []
    if not actions:
        # Si el engine pide respuesta y no tenemos, devolver random
        n = len(obs.select.option)
        k = max(1, obs.select.minCount)
        k = min(k, n)
        return random.sample(list(range(n)), k) if k > 0 else []

    return actions


def _validate_actions(actions, select) -> list[int]:
    """Valida que las acciones estén en rango, sin duplicados, y en cantidad correcta."""
    if not actions:
        return []

    n = len(select.option)
    # Filtrar fuera de rango
    actions = [a for a in actions if 0 <= a < n]
    # Sin duplicados, preservando orden
    seen = set()
    unique = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    # Ajustar cantidad
    if select.maxCount > 0:
        unique = unique[:select.maxCount]
    # Asegurar minCount
    if len(unique) < select.minCount:
        # Rellenar con opciones restantes
        remaining = [i for i in range(n) if i not in seen]
        random.shuffle(remaining)
        needed = select.minCount - len(unique)
        unique.extend(remaining[:needed])
    return unique


# ============================================================
# NO TOCAR (esto lo usa Kaggle)
# ============================================================
if __name__ == "__main__":
    print("Deck:", my_deck[:5], "...")
    print("Card table size:", len(card_table))
    print("Engine:", HAS_ENGINE)
    print("Heuristic:", HEURISTIC_AVAILABLE)