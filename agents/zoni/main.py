"""Generic CABT agent — ZeroM v5 heuristic + v2-smart improvements, deck-configurable.

Strategy (ZeroM-style):
  - Play attackers early (20000 pts)
  - Play setup cards (supporters/items/stadiums) (10000 pts)
  - Play energy (5000 pts)
  - Use abilities (500), evolve (9000), attack (1000 + base damage)
  - Pass / end turn otherwise

Improvements over ZeroM v5 (the "v2-smart" version):
  1. Attack selection by real base damage — uses a hardcoded damage lookup
     for our attackers (avoids calling all_attack() at runtime, which may
     not be available on the Kaggle sandbox).
  2. Rush mode — when opponent prizes <= 2, boost attacker/energy/attack
     priority by +5000. When <= 4 prizes, +1500. If we're behind, -1500.
  3. HP-aware retreat — only retreat when active is in danger of being KO'd
     (HP < half of opponent's active HP) or during rush mode.

The agent loads its deck from deck.csv in cwd (Kaggle convention) and decides
which cards count as ATTACKER / SETUP / ENERGY based on the deck name.

Usage:
  DECK_NAME=zonideck python main.py
  DECK_NAME=zerom    python main.py
"""

import os
import random
import sys
from collections import defaultdict

# In Kaggle, cg.api is on the python path automatically. Locally we add the
# sample_submission directory (set via CABT_SAMPLE_SUBMISSION_DIR) so the
# import below resolves. This is a no-op in Kaggle sandbox.
if "cg" not in sys.modules:
    _SAMPLE = os.environ.get("CABT_SAMPLE_SUBMISSION_DIR", "/kaggle_simulations/agent")
    if _SAMPLE and _SAMPLE not in sys.path:
        sys.path.insert(0, _SAMPLE)

from cg.api import (
    AreaType, CardType, EnergyType, Observation,
    SelectContext, OptionType, Card, Pokemon,
    all_card_data, to_observation_class,
)


# ============================================================
# DECK
# ============================================================
def read_deck_csv() -> list[int]:
    """Read deck.csv. Always returns exactly 60 card IDs."""
    file_path = "deck.csv"
    if not os.path.exists(file_path):
        file_path = "/kaggle_simulations/agent/" + file_path
    with open(file_path, "r") as file:
        csv = file.read().split("\n")
    deck = []
    for i in range(60):
        deck.append(int(csv[i]))
    return deck


my_deck = read_deck_csv()


# ============================================================
# CARD TABLE
# ============================================================
all_card = all_card_data()
card_table = {c.cardId: c for c in all_card}

# Hardcoded damage table for our attackers.
# Format: {attack_id: base_damage}. Anything not in this table defaults to
# the legacy constant-1000 score, so unknown attacks still work.
_ATTACK_DAMAGE = {
    # Zonideck attackers
    1089: 40,    # Mega Latias ex - Strafe
    1090: 300,   # Mega Latias ex - Illusory Impulse
    29: 140,     # Iron Thorns ex
    95: 0,       # Iron Crown ex - Twin Shotels (utility, hits 2 pokemon)
    436: 60,     # Miraidon ex - Repulsion Bolt
    437: 220,    # Miraidon ex - Cyber Drive
    105: 40,     # Miraidon - attack 1
    106: 160,    # Miraidon - attack 2
    1396: 170,   # Iron Boulder
    # Zerom attackers
    307: 30,     # Koraidon
    308: 110,    # Koraidon
    71: 0,       # Raging Bolt ex - attack 1 (utility)
    72: 0,       # Raging Bolt ex - attack 2
    226: 0,      # Raging Bolt - attack 1
    227: 130,    # Raging Bolt - attack 2
    183: 0,      # Fezandipiti ex
    243: 200,    # Latias ex
    120: 30,     # Teal Mask Ogerpon ex - Mountain Stroll
    1092: 200,   # Mega Kangaskhan ex - Rapid-Fire Combo (avg ~200)
    89: 180,     # Iron Leaves ex - Prism Edge
    1546: 60,    # Meowth ex
    371: 20,     # Lillie's Clefairy ex
    1408: 50,    # Koraidon ex
    1409: 200,   # Koraidon ex
}


# ============================================================
# DECK-SPECIFIC HEURISTIC
# ============================================================
DECK_SPECS = {
    "zonideck": {
        # Pokemon (attackers) — Future engine
        "attackers": [
            ("Mega Latias ex", 754),
            ("Iron Crown ex", 80),
            ("Miraidon ex", 313),
            ("Iron Thorns ex", 37),
            ("Miraidon", 87),
            ("Iron Boulder", 971),
        ],
        # Trainers + stadiums
        "setup": [
            ("Crispin", 1198),
            ("Boss's Orders", 1182),
            ("Ciphermaniac's Codebreaking", 1188),
            ("Judge", 1213),
            ("Ultra Ball", 1121),
            ("Pokégear 3.0", 1122),
            ("Night Stretcher", 1097),
            ("Energy Retrieval", 1118),
            ("Switch", 1123),
            ("Mega Signal", 1145),
            ("Wondrous Patch", 1146),
            ("Tera Orb", 1127),
            ("Unfair Stamp", 1080),
            ("Area Zero Underdepths", 1250),
        ],
        # Basic energies (zone needs L, P primarily)
        "energy": [
            ("Lightning", 4),
            ("Psychic", 5),
            ("Fighting", 6),
            ("Fire", 2),
            ("Water", 3),
        ],
    },
    "zerom": {
        # Pokemon attackers — Raging Bolt / Koraidon / Miraidon / Latias core
        "attackers": [
            ("Koraidon", 226),
            ("Koraidon ex", 979),
            ("Raging Bolt ex", 63),
            ("Raging Bolt", 171),
            ("Fezandipiti ex", 140),
            ("Latias ex", 184),
            ("Teal Mask Ogerpon ex", 96),
            ("Mega Kangaskhan ex", 756),
            ("Iron Leaves ex", 75),
            ("Meowth ex", 1071),
            ("Lillie's Clefairy ex", 272),
        ],
        # Trainers + stadiums
        "setup": [
            ("Crispin", 1198),
            ("Tera Orb", 1127),
            ("Unfair Stamp", 1080),
            ("Energy Retrieval", 1118),
            ("Pokégear 3.0", 1122),
            ("Night Stretcher", 1097),
            ("Judge", 1213),
            ("Jamming Tower", 1246),
            ("Boss's Orders", 1182),
            ("Area Zero Underdepths", 1250),
            ("Bug Catching Set", 1094),
            ("Lillie's Determination", 1227),
            ("Ultra Ball", 1121),
            ("Energy Switch", 1116),
        ],
        "energy": [
            ("Lightning", 4),
            ("Fighting", 6),
            ("Psychic", 5),
            ("Grass", 1),
            ("Fire", 2),
        ],
    },
}


def _build_id_sets():
    name = os.environ.get("DECK_NAME", "zonideck").lower()
    if name not in DECK_SPECS:
        raise ValueError(f"Unknown DECK_NAME={name!r}; pick from {list(DECK_SPECS)}")
    spec = DECK_SPECS[name]
    return (
        {cid for _, cid in spec["attackers"]},
        {cid for _, cid in spec["setup"]},
        {cid for _, cid in spec["energy"]},
        name,
    )


ATTACKER_IDS, SETUP_IDS, ENERGY_IDS, DECK_NAME = _build_id_sets()


# ============================================================
# HELPERS
# ============================================================
def get_card(obs, area, index, player_index):
    try:
        ps = obs.current.players[player_index]
        if area == AreaType.HAND:
            return ps.hand[index] if 0 <= index < len(ps.hand) else None
        if area == AreaType.ACTIVE:
            return ps.active[index] if 0 <= index < len(ps.active) else None
        if area == AreaType.BENCH:
            return ps.bench[index] if 0 <= index < len(ps.bench) else None
        if area == AreaType.DISCARD:
            return ps.discard[index] if 0 <= index < len(ps.discard) else None
    except Exception:
        return None
    return None


def _opponent_index(my_idx):
    return 1 - my_idx


def _prizes_remaining(obs, target_idx):
    try:
        return len(obs.current.players[target_idx].prize or [])
    except Exception:
        return 6


def _active_hp(obs, target_idx):
    try:
        active = obs.current.players[target_idx].active
        if not active:
            return (None, None)
        a = active[0]
        return (getattr(a, "hp", None), getattr(a, "maxHp", None))
    except Exception:
        return (None, None)


def _score_option(opt, obs, my_idx):
    score = 0
    otype = getattr(opt, "type", None)
    opp_idx = _opponent_index(my_idx)

    opp_prizes = _prizes_remaining(obs, opp_idx)
    my_prizes = _prizes_remaining(obs, my_idx)
    rush_bonus = 0
    if opp_prizes <= 2:
        rush_bonus = 5000
    elif opp_prizes <= 4:
        rush_bonus = 1500
    if my_prizes <= 2:
        rush_bonus -= 1500

    try:
        if otype == OptionType.PLAY:
            card = get_card(obs, AreaType.HAND, opt.index, my_idx)
            if card is not None:
                cid = getattr(card, "id", None)
                if cid in ATTACKER_IDS:
                    score += 20000 + rush_bonus
                elif cid in SETUP_IDS:
                    score += 10000
                elif cid in ENERGY_IDS:
                    score += 5000 + rush_bonus
                else:
                    score += 1
        elif otype == OptionType.NUMBER:
            n = getattr(opt, "number", 0)
            if opp_prizes <= 2:
                score += n * 200
            else:
                score += n * 100
        elif otype == OptionType.YES:
            score = 1
        elif otype == OptionType.CARD:
            card = get_card(obs, opt.area, opt.index, opt.playerIndex)
            if card is not None:
                cid = getattr(card, "id", None)
                if cid in ATTACKER_IDS:
                    score += 50 + rush_bonus // 10
                elif cid in SETUP_IDS:
                    score += 30
                elif cid in ENERGY_IDS:
                    score += 10 + rush_bonus // 20
        elif otype == OptionType.ATTACK:
            aid = getattr(opt, "attackId", None)
            dmg = _ATTACK_DAMAGE.get(aid, 0)
            if dmg and dmg > 0:
                score = 1000 + dmg
            else:
                # Unknown attack (utility, draw, switch, etc.) — fallback
                score = 1000
            score += rush_bonus // 2
        elif otype == OptionType.ABILITY:
            score = 500
        elif otype == OptionType.EVOLVE:
            score = 9000 + rush_bonus // 2
        elif otype == OptionType.RETREAT:
            my_hp, my_max = _active_hp(obs, my_idx)
            opp_hp, opp_max = _active_hp(obs, opp_idx)
            in_danger = (my_hp is not None and opp_hp is not None
                         and my_max and my_max > 0 and my_hp * 2 < opp_hp)
            if in_danger or opp_prizes <= 2:
                score = 1000
            else:
                score = 50
        elif otype == OptionType.ATTACH:
            score = 800
    except Exception:
        score = 0
    return score


# ============================================================
# AGENT
# ============================================================
def agent(obs_dict: dict) -> list[int]:
    obs: Observation = to_observation_class(obs_dict)
    if obs.select is None:
        # Initial selection: return the deck.
        return my_deck

    sel = obs.select
    opts = sel.option
    n = len(opts)
    if n == 0:
        return []

    my_idx = obs.current.yourIndex
    scores = [_score_option(o, obs, my_idx) for o in opts]
    order = sorted(range(n), key=lambda i: -scores[i])

    if sel.maxCount > 0:
        k = min(sel.maxCount, n)
    else:
        k = n
    return order[:k]


if __name__ == "__main__":
    print(f"Agent ready: deck={DECK_NAME}, n_cards={len(my_deck)}, table={len(card_table)}")
