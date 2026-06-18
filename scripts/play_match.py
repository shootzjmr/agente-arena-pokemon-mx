"""Crash-resilient local match runner.

Plays N matches between two agents and reports win rates. The native engine
sometimes hits bad states (e.g. empty MAIN options after a TO_HAND prompt).
We treat a crashed match as a no-result game and continue; useful for
benchmarking under realistic conditions.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cg.game import battle_start, battle_select, battle_finish
from agent.heuristic import choose_action


def _read_deck(path: str) -> list[int]:
    with open(path) as fh:
        return [int(line.strip()) for line in fh if line.strip()]


def _validate_pick(pick, sel, rng):
    opts = sel.get("option", [])
    if not opts:
        return pick  # pass through to caller (engine edge case)
    mn, mx = sel.get("minCount", 0), sel.get("maxCount", 1)
    if mx <= 0:
        mx = max(mn, 1)
    pick = [i for i in pick if 0 <= i < len(opts)]
    pick = list(dict.fromkeys(pick))
    if len(pick) < mn:
        pool = [i for i in range(len(opts)) if i not in pick]
        rng.shuffle(pool)
        pick = pick + pool[:mn - len(pick)]
    if len(pick) > mx:
        pick = pick[:mx]
    if not pick:
        pick = [rng.randrange(len(opts))]
    return pick


def _safe_pick(sel, rng):
    opts = sel.get("option", [])
    if not opts:
        return [0]
    mx = min(max(sel.get("maxCount", 1), 1), len(opts))
    return rng.sample(range(len(opts)), mx)


def _play_one(agent0, agent1, deck0, deck1, seed: int, max_steps: int = 4000):
    rng = random.Random(seed)
    try:
        obs, start = battle_start(deck0, deck1)
    except Exception as e:
        return -1, f"start:{e}", 0
    if obs is None:
        return -1, "no_obs", 0

    agents = [agent0, agent1]
    step = 0
    while step < max_steps:
        step += 1
        sel = obs.get("select")
        if sel is None:
            cur = obs.get("current") or {}
            return cur.get("result", -1), "ended", step
        try:
            cur = obs.get("current") or {}
            # If the game has already ended (result != -1) but engine still hands us
            # a select with 0 options, treat as ended.
            if cur.get("result", -1) != -1:
                return cur.get("result", -1), "ended_post_result", step
            your_idx = cur.get("yourIndex", 0)
            pick = agents[your_idx](obs)
            if not pick:
                # Agent signals "no valid move" — re-check whether the game ended.
                cur2 = obs.get("current") or {}
                if cur2.get("result", -1) != -1:
                    return cur2.get("result", -1), "ended_post_result", step
                try:
                    battle_finish()
                except Exception:
                    pass
                return -1, "agent_give_up", step
            pick = _validate_pick(pick, sel, rng)
        except Exception:
            pick = _safe_pick(sel, rng)
        try:
            obs = battle_select(pick)
        except Exception:
            try:
                battle_finish()
            except Exception:
                pass
            return -1, "crashed", step
    try:
        battle_finish()
    except Exception:
        pass
    return -1, "timeout", step


def play_many(n: int, deck_path: str, agent0=None, agent1=None,
              verbose: bool = False, seed_base: int = 0):
    deck = _read_deck(deck_path)
    agent0 = agent0 or choose_action
    agent1 = agent1 or choose_action
    results = {"a0_win": 0, "a1_win": 0, "draw": 0, "crash": 0, "timeout": 0,
               "no_obs": 0, "start_err": 0, "agent_give_up": 0, "ended_post_result": 0}
    t0 = time.time()
    for g in range(n):
        # Alternate sides to neutralize any first-player bias.
        swap = g % 2
        a0, a1 = (agent0, agent1) if swap == 0 else (agent1, agent0)
        seed = seed_base + g
        result, reason, steps = _play_one(a0, a1, deck, deck, seed)
        result_for_a0 = result if swap == 0 else (1 - result if result in (0, 1) else result)
        if result_for_a0 == 0:
            results["a0_win"] += 1
        elif result_for_a0 == 1:
            results["a1_win"] += 1
        elif result_for_a0 == 2:
            results["draw"] += 1
        elif reason == "agent_give_up":
            results["agent_give_up"] += 1
        elif reason == "ended_post_result":
            results["ended_post_result"] += 1
        elif reason == "crashed":
            results["crash"] += 1
        elif reason == "timeout":
            results["timeout"] += 1
        elif reason == "no_obs":
            results["no_obs"] += 1
        else:
            results["start_err"] += 1
        if verbose and (g + 1) % max(1, n // 5) == 0:
            elapsed = time.time() - t0
            rate = (g + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{g+1}/{n}] {results} ({rate:.1f} games/s)")
    elapsed = time.time() - t0
    print(f"\nResults over {n} games ({elapsed:.1f}s, {n/elapsed:.1f} games/s):")
    for k, v in results.items():
        print(f"  {k:>10}: {v}")
    decided = results["a0_win"] + results["a1_win"] + results["draw"]
    if decided > 0:
        print(f"  a0 win%  (decided only): {100*results['a0_win']/decided:.1f}%")
        print(f"  a1 win%  (decided only): {100*results['a1_win']/decided:.1f}%")
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--deck", default=os.path.join(_HERE, "deck.csv"))
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    play_many(args.n, args.deck, verbose=args.verbose, seed_base=args.seed)


if __name__ == "__main__":
    main()
