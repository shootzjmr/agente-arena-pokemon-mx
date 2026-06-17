"""
Test rápido: corre 1 batalla entre 2 agentes y muestra el resultado.

USO:
    python3 test_battle.py
    python3 test_battle.py --agent1 agents/mega_lucario --agent2 agents/zoni
"""

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

REPO_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_DIR))


def load_agent(agent_path: Path):
    agent_path = Path(agent_path)
    main_py = agent_path / "main.py"
    if not main_py.exists():
        raise FileNotFoundError(f"No main.py en {agent_path}")

    old_cwd = os.getcwd()
    os.chdir(agent_path)
    try:
        spec = importlib.util.spec_from_file_location(f"agent_{agent_path.name}", main_py)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        os.chdir(old_cwd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent1", default="agents/mega_lucario")
    parser.add_argument("--agent2", default="agents/template")
    parser.add_argument("--max-turns", type=int, default=2000)
    args = parser.parse_args()

    a1 = load_agent(args.agent1)
    a2 = load_agent(args.agent2)

    try:
        from cg.game import battle_start, battle_select, battle_finish
        from cg.api import to_observation_class
    except ImportError:
        print("ERROR: engine cg/ no encontrado. Bajá el dataset de Kaggle.")
        return 1

    print(f"⚔️  {Path(args.agent1).name} vs {Path(args.agent2).name}")
    print(f"   Deck1: {a1.my_deck[:5]}...")
    print(f"   Deck2: {a2.my_deck[:5]}...")

    obs, sd = battle_start(a1.my_deck, a2.my_deck)
    if obs is None:
        print(f"ERROR: battle_start fallo, error_player={sd.errorPlayer}")
        return 1

    t0 = time.time()
    turn = 0
    error = None
    try:
        while turn < args.max_turns:
            your_index = obs.get("current", {}).get("yourIndex", 0)
            agent = a1 if your_index == 0 else a2

            try:
                actions = agent.agent(obs)
            except Exception as e:
                error = f"agent error: {e}"
                break

            try:
                obs = battle_select(actions)
            except Exception as e:
                error = f"battle_select error: {type(e).__name__}"
                break

            turn += 1
            if isinstance(obs, dict) and obs.get("winner") is not None:
                w = obs["winner"]
                winner = Path(args.agent1).name if w == 0 else Path(args.agent2).name
                elapsed = time.time() - t0
                print(f"\n🏆 {winner} gana en {turn} turnos ({elapsed:.1f}s)")
                battle_finish()
                return 0
    finally:
        try:
            battle_finish()
        except:
            pass

    elapsed = time.time() - t0
    print(f"\n⏱️  {turn} turnos jugados ({elapsed:.1f}s) sin winner")
    if error:
        print(f"   Error: {error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
