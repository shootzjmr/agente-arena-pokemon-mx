"""Heuristic Pokemon TCG agent (rewritten to use option indices correctly).

Key correction: every pick must return INDICES INTO ``obs.select.option``,
not indices into ``me.hand`` or anything else. The options list is what the
engine accepts, and it can be filtered (e.g. SETUP_ACTIVE only contains
basics).
"""

from __future__ import annotations

import os
import sys
from typing import Any

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cg.api import to_observation_class
from agent.cards import get_card
from agent import state_view as sv


# ---------------------------------------------------------------------------
# Helpers to read option properties safely
# ---------------------------------------------------------------------------

def _opt_card_id(opt) -> int:
    """Best-effort card id attached to an option."""
    cid = opt.cardId
    if cid is not None and cid != 0:
        return int(cid)
    return 0


def _opt_in_play_area(opt) -> int:
    a = opt.inPlayArea
    return int(a) if a is not None else -1


def _opt_area(opt) -> int:
    a = opt.area
    return int(a) if a is not None else -1


def _clamp_pick(pick: list[int], n_opts: int, mn: int, mx: int) -> list[int]:
    pick = [i for i in pick if 0 <= i < n_opts]
    pick = list(dict.fromkeys(pick))
    if mx <= 0:
        mx = max(mn, 1)
    if len(pick) < mn:
        pad = [i for i in range(n_opts) if i not in pick]
        pick = pick + pad[:mn - len(pick)]
    if len(pick) > mx:
        pick = pick[:mx]
    if not pick and n_opts > 0:
        pick = [0]
    return pick


# ---------------------------------------------------------------------------
# Attack-damage lookup
# ---------------------------------------------------------------------------

def _attack_damage(active, attack_id: int) -> int:
    if active is None or active.id is None:
        return 0
    info = get_card(active.id)
    if not info:
        return 0
    for atk in info.attacks:
        if atk.attack_id == attack_id:
            return atk.damage
    return 0


def _can_pay_attack_cost(active, attack_id: int) -> bool:
    """Check if the active has enough energy to use ``attack_id``.

    Colorless cost (energy type 0) is paid by ANY energy, not just a literal
    colorless card. Special energies (non-basic) are treated as 1 energy unit
    that can fill any cost.
    """
    if active is None or active.id is None:
        return False
    info = get_card(active.id)
    if not info:
        return False
    target = None
    for atk in info.attacks:
        if atk.attack_id == attack_id:
            target = atk
            break
    if target is None:
        return False
    from collections import Counter
    avail = Counter()
    for e in (active.energies or []):
        avail[int(e)] += 1
    total_units = sum(avail.values())
    for req in target.energies:
        req = int(req)
        # RAINBOW (10) matches any
        if req == 10:
            if total_units > 0:
                total_units -= 1
                continue
            return False
        # COLORLESS (0): any energy pays for it
        if req == 0:
            if total_units > 0:
                total_units -= 1
                continue
            return False
        # Specific energy type
        if avail[req] > 0:
            avail[req] -= 1
            total_units -= 1
            continue
        return False
    return True


# ---------------------------------------------------------------------------
# Main-phase scoring
# ---------------------------------------------------------------------------

def _score_main_options(obs) -> list[float]:
    state = obs.current
    select = obs.select
    opts = select.option
    scores = [0.0] * len(opts)

    my_act = sv.my_active(state)
    opp_act = sv.opp_active(state)

    for i, opt in enumerate(opts):
        t = sv.op_type(opt)
        if t == sv.OP_ATTACK:
            aid = opt.attackId
            dmg = _attack_damage(my_act, aid) if my_act else 0
            payable = _can_pay_attack_cost(my_act, aid)
            if not payable:
                scores[i] = -1000  # can't use it
                continue
            if opp_act and dmg >= opp_act.hp:
                scores[i] = 1000 + dmg  # KO
            elif opp_act:
                # Slight preference for damage above opponent HP threshold
                scores[i] = 50 + dmg
            else:
                scores[i] = 25
        elif t == sv.OP_PLAY:
            scores[i] = _score_play(opt)
        elif t == sv.OP_ATTACH:
            scores[i] = _score_attach(opt)
        elif t == sv.OP_EVOLVE:
            scores[i] = _score_evolve(opt)
        elif t == sv.OP_ABILITY:
            scores[i] = 30
        elif t == sv.OP_DISCARD:
            scores[i] = 10
        elif t == sv.OP_RETREAT:
            scores[i] = _score_retreat(state)
        elif t == sv.OP_END:
            scores[i] = -10
        elif t == sv.OP_SKILL:
            scores[i] = 5
        else:
            scores[i] = 0
    return scores


def _score_play(opt) -> float:
    cid = _opt_card_id(opt)
    info = get_card(cid)
    if info is None:
        return 20
    if info.is_pokemon:
        state_view = opt  # not used here; we keep generic scoring
        if info.stage2:
            return 70
        if info.stage1:
            return 60
        return 30
    if info.card_type == sv.CT_SUPPORTER:
        return 80
    if info.card_type == sv.CT_ITEM:
        return 40
    if info.card_type == sv.CT_TOOL:
        return 35
    if info.card_type == sv.CT_STADIUM:
        return 30
    return 20


def _score_attach(opt) -> float:
    in_play = _opt_in_play_area(opt)
    if in_play == 4:
        return 80
    if in_play == 5:
        return 50
    return 40


def _score_evolve(opt) -> float:
    in_play = _opt_in_play_area(opt)
    if in_play == 4:
        return 90
    if in_play == 5:
        return 60
    return 40


def _score_retreat(state) -> float:
    my_act = sv.my_active(state)
    opp_act = sv.opp_active(state)
    if my_act is None or opp_act is None or my_act.id is None or opp_act.id is None:
        return 0
    opp_info = get_card(opp_act.id)
    if not opp_info or not opp_info.attacks:
        return 0
    incoming = max(a.damage for a in opp_info.attacks)
    if incoming >= my_act.hp and my_act.hp < my_act.maxHp // 2:
        return 80
    return -5


# ---------------------------------------------------------------------------
# Per-context picks (return option indices)
# ---------------------------------------------------------------------------

def _pick_main(obs) -> list[int]:
    select = obs.select
    opts = select.option
    scores = _score_main_options(obs)
    mn, mx = select.minCount, select.maxCount
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    chosen = [i for i in ranked if scores[i] > 0][:mx]
    if len(chosen) < mn:
        chosen = ranked[:mx] if mx > 0 else ranked[:mn]
    return _clamp_pick(chosen, len(opts), mn, mx)


def _pick_count(obs) -> list[int]:
    select = obs.select
    mn, mx = select.minCount, select.maxCount
    opts = select.option
    items = []
    for i, opt in enumerate(opts):
        if sv.op_type(opt) == sv.OP_NUMBER:
            n = opt.number if opt.number is not None else 0
            items.append((n, i))
        else:
            items.append((0, i))
    items.sort(reverse=True)
    chosen = [i for _, i in items[:mx]]
    if len(chosen) < mn:
        chosen = [i for _, i in items[:mn]]
    return _clamp_pick(chosen, len(opts), mn, mx)


def _pick_yes_no(obs, want_yes: bool) -> list[int]:
    select = obs.select
    opts = select.option
    for i, opt in enumerate(opts):
        if sv.op_type(opt) == sv.OP_YES and want_yes:
            return [i]
        if sv.op_type(opt) == sv.OP_NO and not want_yes:
            return [i]
    return [0]


def _pick_setup_active(obs) -> list[int]:
    """Choose the option pointing at the highest-HP basic Pokemon."""
    select = obs.select
    opts = select.option
    best, best_score = 0, -1
    for i, opt in enumerate(opts):
        cid = _opt_card_id(opt)
        info = get_card(cid) if cid else None
        if not info or not info.is_pokemon or not info.basic:
            continue
        score = info.hp * 2 + (300 if info.ex else 0) + (400 if info.tera else 0)
        if score > best_score:
            best, best_score = i, score
    return [best]


def _pick_setup_bench(obs) -> list[int]:
    """Pick the first basic Pokemon option."""
    select = obs.select
    opts = select.option
    for i, opt in enumerate(opts):
        cid = _opt_card_id(opt)
        info = get_card(cid) if cid else None
        if info and info.is_pokemon and info.basic:
            return [i]
    return [0]


def _pick_evolve(obs) -> list[int]:
    select = obs.select
    opts = select.option
    best, best_score = 0, -1
    for i, opt in enumerate(opts):
        cid = _opt_card_id(opt)
        info = get_card(cid) if cid else None
        score = 0
        if info:
            score = info.hp + (500 if info.ex else 0) + (300 if info.tera else 0)
        if score > best_score:
            best, best_score = i, score
    return [best]


def _pick_attack(obs) -> list[int]:
    select = obs.select
    opts = select.option
    state = obs.current
    my_act = sv.my_active(state)
    opp_act = sv.opp_active(state)
    best, best_score = 0, -1
    for i, opt in enumerate(opts):
        if sv.op_type(opt) != sv.OP_ATTACK:
            continue
        info = get_card(my_act.id) if my_act and my_act.id else None
        if not info:
            continue
        for atk in info.attacks:
            if atk.attack_id == opt.attackId:
                d = atk.damage
                if opp_act and d >= opp_act.hp:
                    return [i]
                if d > best_score:
                    best, best_score = i, d
                break
    return [best]


def _pick_skill_order(obs) -> list[int]:
    select = obs.select
    mx = min(select.maxCount, len(select.option))
    if mx <= 0:
        mx = 1
    return list(range(mx))


def _pick_special_condition(obs) -> list[int]:
    select = obs.select
    prefs = {0: 4, 1: 3, 3: 2, 2: 1, 4: 0}
    best, best_score = 0, -1
    for i, opt in enumerate(select.option):
        if sv.op_type(opt) != sv.OP_SPECIAL_CONDITION:
            continue
        sct = opt.specialConditionType
        sct_int = int(sct) if not isinstance(sct, int) else sct
        score = prefs.get(sct_int, 0)
        if score > best_score:
            best, best_score = i, score
    return [best]


def _pick_first_n(obs) -> list[int]:
    select = obs.select
    n = max(select.minCount, min(select.maxCount, len(select.option)))
    if n == 0:
        n = min(max(select.maxCount, 1), len(select.option)) or 1
    return list(range(n))


def _pick_card_high_hp(obs) -> list[int]:
    select = obs.select
    opts = select.option
    best, best_score = 0, -1
    for i, opt in enumerate(opts):
        cid = _opt_card_id(opt)
        info = get_card(cid) if cid else None
        score = (info.hp if info else 0) + (500 if info and info.ex else 0)
        if score > best_score:
            best, best_score = i, score
    return [best]


# ---------------------------------------------------------------------------
# Top-level dispatcher
# ---------------------------------------------------------------------------

def choose_action(obs_dict: dict) -> list[int]:
    obs = to_observation_class(obs_dict)
    select = obs.select
    if select is None:
        return []
    st = sv.type_of(select)
    ctx = sv.ctx_of(select)
    opts = select.option
    mn, mx = select.minCount, select.maxCount
    if not opts:
        # Engine edge case: select requires minCount >= 1 but options list is empty
        # (e.g. ctx=TO_HAND after some effects). Return [] to signal "give up" — the
        # caller will end the battle gracefully.
        if mx > 0 or mn > 0:
            return []
        return [0]

    if st == 8:  # COUNT
        return _pick_count(obs)
    if ctx == sv.CTX_IS_FIRST:
        return _pick_yes_no(obs, want_yes=True)
    if ctx == sv.CTX_MULLIGAN:
        me_pl = sv.me(obs.current)
        if me_pl.hand:
            for c in me_pl.hand:
                info = get_card(c.id)
                if info and info.is_pokemon and info.basic:
                    return _pick_yes_no(obs, want_yes=False)
        return _pick_yes_no(obs, want_yes=True)
    if ctx == sv.CTX_SETUP_ACTIVE_POKEMON:
        return _clamp_pick(_pick_setup_active(obs), len(opts), mn, mx)
    if ctx == sv.CTX_SETUP_BENCH_POKEMON:
        return _clamp_pick(_pick_setup_bench(obs), len(opts), mn, mx)
    if ctx == sv.CTX_COIN_HEAD:
        return _pick_yes_no(obs, want_yes=True)
    if ctx == sv.CTX_ACTIVATE:
        return _pick_yes_no(obs, want_yes=False)
    if ctx in (sv.CTX_FIRST_EFFECT, sv.CTX_MORE_DEVOLVE):
        return _pick_yes_no(obs, want_yes=False)
    if ctx == sv.CTX_MAIN:
        return _pick_main(obs)
    if ctx == sv.CTX_ATTACK:
        return _clamp_pick(_pick_attack(obs), len(opts), mn, mx)
    if ctx == sv.CTX_EVOLVE:
        return _clamp_pick(_pick_evolve(obs), len(opts), mn, mx)
    if ctx == sv.CTX_SKILL_ORDER:
        return _clamp_pick(_pick_skill_order(obs), len(opts), mn, mx)
    if ctx in (sv.CTX_AFFECT_SPECIAL_CONDITION, sv.CTX_RECOVER_SPECIAL_CONDITION):
        return _clamp_pick(_pick_special_condition(obs), len(opts), mn, mx)

    t0 = sv.op_type(opts[0])
    if t0 in (sv.OP_ENERGY, sv.OP_ENERGY_CARD):
        return _clamp_pick([0], len(opts), mn, mx)
    if t0 in (sv.OP_CARD, sv.OP_TOOL_CARD):
        return _clamp_pick(_pick_card_high_hp(obs), len(opts), mn, mx)
    return _clamp_pick(_pick_first_n(obs), len(opts), mn, mx)
