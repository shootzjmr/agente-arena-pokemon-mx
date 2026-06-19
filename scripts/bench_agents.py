"""Local head-to-head benchmark between two agent main.py files.

Loads each agent's main.py in a subprocess-isolated context (separate cwd),
runs N matches alternating who goes first, and reports win rate per deck.

The two agents can be the same main.py (A/B same-deck heuristic diff) or
different main.py + deck.csv combos.

Usage:
    # Same deck, two heuristic versions (A/B cleanest signal)
    python scripts/bench_agents.py \
        --agent0 agents/zoni-iter-A \
        --agent1 agents/zoni-iter-B \
        --n 50

    # Different decks
    python scripts/bench_agents.py \
        --agent0 agents/zoni \
        --agent1 agents/zero_mexico \
        --n 50

Requires the cg/ submodule to be present (download from Kaggle competition
data first if not already at the repo root).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import statistics
import sys
import time
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
_CG_PATH = _HERE / "cg"

# Load cg.api and cg.game via importlib so we don't depend on the implicit
# `cwd` entry in sys.path (which Python omits when running a script with an
# absolute or relative path, breaking `import cg`).
import importlib.util as _il_util
_CG_INIT = _CG_PATH / "__init__.py"
_spec = _il_util.spec_from_file_location(
    "cg", _CG_INIT, submodule_search_locations=[str(_CG_PATH)]
)
_cg_mod = _il_util.module_from_spec(_spec)
sys.modules["cg"] = _cg_mod
_spec.loader.exec_module(_cg_mod)

from cg.game import battle_finish, battle_select, battle_start  # noqa: E402


def load_agent(agent_dir: Path, deck_name: str):
    """Load agent's main.py from a directory. deck_name is exported as
    DECK_NAME env var before import (main.py reads it at import time)."""
    if not agent_dir.is_dir():
        raise FileNotFoundError(f"Agent dir not found: {agent_dir}")
    main_py = (agent_dir / "main.py").resolve()
    if not main_py.exists():
        raise FileNotFoundError(f"{main_py} missing")

    # Set DECK_NAME before import so main.py's _build_id_sets() picks the right spec
    os.environ["DECK_NAME"] = deck_name
    saved_cwd = os.getcwd()
    os.chdir(agent_dir)
    try:
        spec = importlib.util.spec_from_file_location(
            f"agent_{agent_dir.name}", main_py
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load {main_py}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        if not hasattr(mod, "agent") or not hasattr(mod, "my_deck"):
            raise AttributeError(f"{main_py} missing agent() or my_deck")
        return mod.agent, list(mod.my_deck)
    finally:
        os.chdir(saved_cwd)


def play_one(deck0: list[int], deck1: list[int], agent0, agent1) -> tuple[int, int]:
    """Play one match. Returns (winner_idx, num_steps).
    winner_idx: 0 if deck0 won, 1 if deck1 won, -1 if draw, -2 on error."""
    obs, sd = battle_start(deck0, deck1)
    if obs is None or not sd.battlePtr:
        return -2, 0

    safety = 0
    while True:
        safety += 1
        if safety > 800:
            break
        cur = obs.get("current", {})
        sel = obs.get("select")
        result = cur.get("result", -1)
        if result >= 0 or sel is None:
            break

        your_idx = cur.get("yourIndex", -1)
        try:
            if your_idx == 0:
                action = agent0(obs)
            elif your_idx == 1:
                action = agent1(obs)
            else:
                break
            # Clamp to valid options
            opts = sel.get("option", [])
            mn = sel.get("minCount", 0)
            mx = sel.get("maxCount", 1) or max(mn, 1)
            if not isinstance(action, list):
                action = [action]
            action = [int(i) for i in action if 0 <= int(i) < len(opts)]
            action = list(dict.fromkeys(action))[:mx]
            while len(action) < mn and opts:
                for i in range(len(opts)):
                    if i not in action:
                        action.append(i)
                        if len(action) >= mn:
                            break
            if not action and opts:
                action = [0]
            obs = battle_select(action)
        except Exception:
            traceback.print_exc()
            break

    try:
        battle_finish()
    except Exception:
        pass

    final = obs.get("current", {}).get("result", -2) if obs else -2
    return (0 if final == 0 else (1 if final == 1 else (-1 if final == 2 else -2))), safety


def run_benchmark(agent0_dir: Path, agent1_dir: Path, n: int, deck0_name: str, deck1_name: str):
    """Run N matches, alternating who goes first. Returns summary dict."""
    print(f"Loading agent0 from {agent0_dir} (deck={deck0_name})...", file=sys.stderr)
    agent0, deck0 = load_agent(agent0_dir, deck0_name)
    print(f"  OK: deck has {len(deck0)} cards", file=sys.stderr)
    print(f"Loading agent1 from {agent1_dir} (deck={deck1_name})...", file=sys.stderr)
    agent1, deck1 = load_agent(agent1_dir, deck1_name)
    print(f"  OK: deck has {len(deck1)} cards", file=sys.stderr)

    results = []
    starts = time.time()
    for i in range(1, n + 1):
        # Alternate who is player 0
        if i % 2 == 1:
            d0, d1, a0, a1, label = deck0, deck1, agent0, agent1, "A0"
        else:
            d0, d1, a0, a1, label = deck1, deck0, agent1, agent0, "A1"

        winner, steps = play_one(d0, d1, a0, a1)
        results.append({
            "i": i,
            "label": label,
            "winner_idx": winner,
            "steps": steps,
            "agent0_was": "deck0" if i % 2 == 1 else "deck1",
        })
        if i % 10 == 0 or i == n:
            elapsed = time.time() - starts
            print(f"  match {i}/{n}: winner={winner}, steps={steps}, elapsed={elapsed:.1f}s", file=sys.stderr)

    # Tally
    wins0 = sum(1 for r in results if (r["winner_idx"] == 0 and r["agent0_was"] == "deck0") or (r["winner_idx"] == 1 and r["agent0_was"] == "deck1"))
    wins1 = sum(1 for r in results if (r["winner_idx"] == 1 and r["agent0_was"] == "deck0") or (r["winner_idx"] == 0 and r["agent0_was"] == "deck1"))
    draws = sum(1 for r in results if r["winner_idx"] == -1)
    errors = sum(1 for r in results if r["winner_idx"] == -2)

    return {
        "n": n,
        "agent0": str(agent0_dir),
        "agent1": str(agent1_dir),
        "deck0_name": deck0_name,
        "deck1_name": deck1_name,
        "agent0_wins": wins0,
        "agent1_wins": wins1,
        "draws": draws,
        "errors": errors,
        "win_rate0": wins0 / n if n else 0,
        "win_rate1": wins1 / n if n else 0,
        "avg_steps": statistics.mean(r["steps"] for r in results) if results else 0,
        "duration_s": round(time.time() - starts, 2),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("--agent0", required=True, type=Path)
    p.add_argument("--agent1", required=True, type=Path)
    p.add_argument("--deck-name0", default="zonideck", help="DECK_NAME passed to agent0's main.py at load")
    p.add_argument("--deck-name1", default="zerom")
    p.add_argument("--n", type=int, default=50)
    p.add_argument("--out", type=Path, default=None, help="Optional JSON file for full results")
    args = p.parse_args()

    summary = run_benchmark(args.agent0, args.agent1, args.n, args.deck_name0, args.deck_name1)
    print()
    print("=" * 60)
    print(f"Agent 0 ({Path(summary['agent0']).name}): {summary['agent0_wins']}/{summary['n']} ({summary['win_rate0']*100:.1f}%)")
    print(f"Agent 1 ({Path(summary['agent1']).name}): {summary['agent1_wins']}/{summary['n']} ({summary['win_rate1']*100:.1f}%)")
    print(f"Draws: {summary['draws']}, Errors: {summary['errors']}")
    print(f"Avg steps/match: {summary['avg_steps']:.1f}")
    print(f"Total time: {summary['duration_s']}s")
    print("=" * 60)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
