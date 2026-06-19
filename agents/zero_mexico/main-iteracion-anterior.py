"""ZeroM agent v5 — ZeroM deck with correct Kaggle IDs.

ZeroM composition (CSV-driven, but with hardcoded ID sets for heuristic):
  Pokemon: Koraidon, Raging Bolt ex, Fezandipiti ex, Latias ex,
           Teal Mask Ogerpon, Mega Kangaskhan ex, Iron Leaves,
           Raging Bolt, Meowth ex, Lillie's Clefairy ex
  Trainers: Crispin, Boss's Orders, Lillie's Determination, Judge,
            Ultra Ball, Pokégear 3.0, Bug Catching Set, Night Stretcher,
            Energy Retrieval, Energy Switch, Tera Orb, Unfair Stamp,
            Area Zero Underdepths, Jamming Tower
  Energies: Basic G/L/P/F
"""

import os
import random
from collections import defaultdict

from cg.api import (
    AreaType, CardType, EnergyType, Observation,
    SelectContext, OptionType, Card, Pokemon,
    all_card_data, to_observation_class
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


# ============================================================
# DECKLIST — ZeroM (IDs from current Kaggle EN_Card_Data.csv)
# ============================================================
# Pokemon (attackers)
Koraidon = 226
Raging_Bolt_ex = 63
Fezandipiti_ex = 140
Latias_ex = 184
Teal_Mask_Ogerpon = 95
Mega_Kangaskhan_ex = 756
Iron_Leaves = 27
Raging_Bolt = 171
Meowth_ex = 1071
Lillies_Clefairy_ex = 272

# Supporters
Crispin = 1198
Boss_Orders = 1182
Lillies_Determination = 1227
Judge = 1213

# Items
Ultra_Ball = 1121
Pokegear_30 = 1122
Bug_Catching_Set = 1094
Night_Stretcher = 1097
Energy_Retrieval = 1118
Energy_Switch = 1116
Tera_Orb = 1127
Unfair_Stamp = 1080

# Stadiums
Area_Zero_Underdepths = 1250
Jamming_Tower = 1246

# Energies
Basic_Grass = 1
Basic_Lightning = 4
Basic_Psychic = 5
Basic_Fighting = 6

# Heuristic categories (ZeroM-specific)
ATTACKER_IDS = {
    Koraidon, Raging_Bolt_ex, Fezandipiti_ex, Latias_ex,
    Teal_Mask_Ogerpon, Mega_Kangaskhan_ex, Iron_Leaves,
    Raging_Bolt, Meowth_ex, Lillies_Clefairy_ex,
}

SETUP_IDS = {
    # Supporters
    Crispin, Boss_Orders, Lillies_Determination, Judge,
    # Items
    Ultra_Ball, Pokegear_30, Bug_Catching_Set, Night_Stretcher,
    Energy_Retrieval, Energy_Switch, Tera_Orb, Unfair_Stamp,
    # Stadiums
    Area_Zero_Underdepths, Jamming_Tower,
}

ENERGY_IDS = {Basic_Grass, Basic_Lightning, Basic_Psychic, Basic_Fighting}


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


def _score_option(opt, obs, my_idx):
    score = 0
    otype = getattr(opt, "type", None)
    try:
        if otype == OptionType.PLAY:
            card = get_card(obs, AreaType.HAND, opt.index, my_idx)
            if card is not None:
                cid = getattr(card, "id", None)
                if cid in ATTACKER_IDS:
                    score += 20000  # ZeroM: play attackers early
                elif cid in SETUP_IDS:
                    score += 10000  # trainers for setup
                elif cid in ENERGY_IDS:
                    score += 5000   # attach energy
                else:
                    score += 1
        elif otype == OptionType.NUMBER:
            score = getattr(opt, "number", 0) * 100
        elif otype == OptionType.YES:
            score = 1
        elif otype == OptionType.CARD:
            card = get_card(obs, opt.area, opt.index, opt.playerIndex)
            if card is not None:
                cid = getattr(card, "id", None)
                if cid in ATTACKER_IDS:
                    score += 50
                elif cid in SETUP_IDS:
                    score += 30
                elif cid in ENERGY_IDS:
                    score += 10
        elif otype == OptionType.ATTACK:
            score = 1000
        elif otype == OptionType.ABILITY:
            score = 500
        elif otype == OptionType.EVOLVE:
            score = 9000
        elif otype == OptionType.RETREAT:
            score = 100
        elif otype == OptionType.ATTACH:
            score = 800
    except Exception:
        score = 0
    return score


# ============================================================
# AGENT — minimal, no try/except (matches Kaggle's official pattern)
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
    print(f"ZeroM v5 ready. Deck={len(my_deck)} cards, table={len(card_table)}")