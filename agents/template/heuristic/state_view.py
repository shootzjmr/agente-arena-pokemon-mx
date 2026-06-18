"""Read-only helpers for inspecting an Observation / State.

The native SDK returns enums as raw ints (the dataclass loader doesn't convert
them). This module centralises enum lookups and provides ergonomic helpers so
the heuristic doesn't have to spell out the int codes everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cg.api import (
    AreaType,
    CardType,
    EnergyType,
    OptionType,
    SelectContext,
    SelectType,
    SpecialConditionType,
)

# Mirror the OptionType numeric codes from cg.api.OptionType.
OP_NUMBER = 0
OP_YES = 1
OP_NO = 2
OP_CARD = 3
OP_TOOL_CARD = 4
OP_ENERGY_CARD = 5
OP_ENERGY = 6
OP_PLAY = 7
OP_ATTACH = 8
OP_EVOLVE = 9
OP_ABILITY = 10
OP_DISCARD = 11
OP_RETREAT = 12
OP_ATTACK = 13
OP_END = 14
OP_SKILL = 15
OP_SPECIAL_CONDITION = 16

CTX_MAIN = 0
CTX_SETUP_ACTIVE_POKEMON = 1
CTX_SETUP_BENCH_POKEMON = 2
CTX_SWITCH = 3
CTX_TO_ACTIVE = 4
CTX_TO_BENCH = 5
CTX_TO_FIELD = 6
CTX_TO_HAND = 7
CTX_DISCARD = 8
CTX_TO_DECK = 9
CTX_TO_DECK_BOTTOM = 10
CTX_TO_PRIZE = 11
CTX_NOT_MOVE = 12
CTX_DAMAGE_COUNTER = 13
CTX_DAMAGE_COUNTER_ANY = 14
CTX_DAMAGE = 15
CTX_REMOVE_DAMAGE_COUNTER = 16
CTX_HEAL = 17
CTX_EVOLVES_FROM = 18
CTX_EVOLVES_TO = 19
CTX_DEVOLVE = 20
CTX_ATTACH_FROM = 21
CTX_ATTACH_TO = 22
CTX_DETACH_FROM = 23
CTX_LOOK = 24
CTX_EFFECT_TARGET = 25
CTX_DISCARD_ENERGY_CARD = 26
CTX_DISCARD_TOOL_CARD = 27
CTX_SWITCH_ENERGY_CARD = 28
CTX_DISCARD_CARD_OR_ATTACHED_CARD = 29
CTX_DISCARD_ENERGY = 30
CTX_TO_HAND_ENERGY = 31
CTX_TO_DECK_ENERGY = 32
CTX_SWITCH_ENERGY = 33
CTX_SKILL_ORDER = 34
CTX_ATTACK = 35
CTX_DISABLE_ATTACK = 36
CTX_EVOLVE = 37
CTX_DRAW_COUNT = 38
CTX_DAMAGE_COUNTER_COUNT = 39
CTX_REMOVE_DAMAGE_COUNTER_COUNT = 40
CTX_IS_FIRST = 41
CTX_MULLIGAN = 42
CTX_ACTIVATE = 43
CTX_FIRST_EFFECT = 44
CTX_MORE_DEVOLVE = 45
CTX_COIN_HEAD = 46
CTX_AFFECT_SPECIAL_CONDITION = 47
CTX_RECOVER_SPECIAL_CONDITION = 48

EN_COLORLESS, EN_GRASS, EN_FIRE, EN_WATER, EN_LIGHTNING = 0, 1, 2, 3, 4
EN_PSYCHIC, EN_FIGHTING, EN_DARKNESS, EN_METAL, EN_DRAGON = 5, 6, 7, 8, 9
EN_RAINBOW, EN_TEAM_ROCKET = 10, 11

ENERGY_NAMES = {
    EN_COLORLESS: "Colorless", EN_GRASS: "Grass", EN_FIRE: "Fire",
    EN_WATER: "Water", EN_LIGHTNING: "Lightning", EN_PSYCHIC: "Psychic",
    EN_FIGHTING: "Fighting", EN_DARKNESS: "Darkness", EN_METAL: "Metal",
    EN_DRAGON: "Dragon", EN_RAINBOW: "Rainbow", EN_TEAM_ROCKET: "TeamRocket",
}

CT_BASIC = 0  # POKEMON
CT_ITEM = 1
CT_TOOL = 2
CT_SUPPORTER = 3
CT_STADIUM = 4
CT_BASIC_ENERGY = 5
CT_SPECIAL_ENERGY = 6


def op_type(opt: Any) -> int:
    """Option type as int (the SDK hands them back as raw ints)."""
    t = opt.type
    return int(t) if not isinstance(t, int) else t


def ctx_of(select: Any) -> int:
    c = select.context
    return int(c) if not isinstance(c, int) else c


def type_of(select: Any) -> int:
    t = select.type
    return int(t) if not isinstance(t, int) else t


def enemy_idx(your_idx: int) -> int:
    return 1 - your_idx


def player(state: Any, idx: int):
    return state.players[idx]


def me(state: Any):
    return state.players[state.yourIndex]


def opp(state: Any):
    return state.players[1 - state.yourIndex]


def active_pokemon(state: Any, idx: int):
    """Return the active Pokemon or None."""
    pl = state.players[idx]
    if pl.active and len(pl.active) > 0 and pl.active[0] is not None:
        return pl.active[0]
    return None


def bench_pokemon(state: Any, idx: int):
    return [p for p in state.players[idx].bench if p is not None]


def opp_active(state: Any):
    return active_pokemon(state, 1 - state.yourIndex)


def my_active(state: Any):
    return active_pokemon(state, state.yourIndex)


def prizes_remaining(state: Any, idx: int) -> int:
    """How many prize cards still unrevealed for player idx."""
    return sum(1 for p in state.players[idx].prize if p is not None)


def total_prizes(state: Any, idx: int) -> int:
    return len(state.players[idx].prize)


def opp_hand_count(state: Any) -> int:
    return opp(state).handCount


def my_hand_count(state: Any) -> int:
    return me(state).handCount


def effective_hp(pokemon: Any) -> int:
    """HP remaining (the SDK exposes hp directly)."""
    return pokemon.hp


def has_status(pokemon_state: Any) -> bool:
    return any([pokemon_state.poisoned, pokemon_state.burned,
                pokemon_state.asleep, pokemon_state.paralyzed,
                pokemon_state.confused])


def describe(opt: Any) -> str:
    """Pretty-print an Option for logging."""
    t = op_type(opt)
    if t == OP_PLAY:
        return f"PLAY(idx={opt.index},cardId={opt.cardId},serial={opt.serial})"
    if t == OP_ATTACH:
        return (f"ATTACH(from={opt.area}/{opt.index} -> "
                f"to={opt.inPlayArea}/{opt.inPlayIndex})")
    if t == OP_EVOLVE:
        return (f"EVOLVE({opt.area}/{opt.index} on {opt.inPlayArea}/{opt.inPlayIndex})")
    if t == OP_ABILITY:
        return f"ABILITY(area={opt.area}/idx={opt.index})"
    if t == OP_DISCARD:
        return f"DISCARD(area={opt.area}/idx={opt.index})"
    if t == OP_RETREAT:
        return f"RETREAT(to={opt.inPlayIndex})"
    if t == OP_ATTACK:
        return f"ATTACK(id={opt.attackId})"
    if t == OP_END:
        return "END"
    if t == OP_CARD:
        return f"CARD(area={opt.area}/idx={opt.index}/pi={opt.playerIndex})"
    if t == OP_ENERGY_CARD:
        return f"ENERGY_CARD(area={opt.area}/idx={opt.index}/ei={opt.energyIndex})"
    if t == OP_TOOL_CARD:
        return f"TOOL_CARD(area={opt.area}/idx={opt.index}/ti={opt.toolIndex})"
    if t == OP_ENERGY:
        return f"ENERGY(area={opt.area}/idx={opt.index}/ei={opt.energyIndex}/count={opt.count})"
    if t == OP_NUMBER:
        return f"NUMBER({opt.number})"
    if t == OP_YES:
        return "YES"
    if t == OP_NO:
        return "NO"
    if t == OP_SKILL:
        return f"SKILL(cardId={opt.cardId}/serial={opt.serial})"
    if t == OP_SPECIAL_CONDITION:
        return f"SPECIAL_CONDITION({opt.specialConditionType})"
    return f"OP({t})"
