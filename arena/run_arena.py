"""
Arena Runner: corre todos los agentes entre sí y genera leaderboard.

USO:
    python3 run_arena.py --games 10
    python3 run_arena.py --games 50 --output leaderboard.json
    python3 run_arena.py --agents agents/zoni agents/ztich_na --games 5

RESULTADO:
    - Imprime tabla de win rates en consola
    - Guarda resultados en leaderboard.json
    - Logs de cada match en matchups/YYYYMMDD_HHMMSS_AGENT1_vs_AGENT2.txt
"""

import argparse
import importlib.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


# ============================================================
# SETUP
# ============================================================
ARENA_DIR = Path(__file__).parent
REPO_DIR = ARENA_DIR.parent
AGENTS_DIR = REPO_DIR / "agents"
MATCHUPS_DIR = ARENA_DIR / "matchups"
MATCHUPS_DIR.mkdir(parents=True, exist_ok=True)

# Agregar paths de los agentes al PYTHONPATH
sys.path.insert(0, str(REPO_DIR))
sys.path.insert(0, str(AGENTS_DIR))


def load_agent(agent_path: Path):
    """Carga un agente desde su carpeta."""
    agent_path = Path(agent_path)
    main_py = agent_path / "main.py"

    if not main_py.exists():
        raise FileNotFoundError(f"No main.py en {agent_path}")

    # Cambiar al directorio del agente para que encuentre deck.csv
    old_cwd = os.getcwd()
    os.chdir(agent_path)

    try:
        spec = importlib.util.spec_from_file_location(
            f"agent_{agent_path.name}",
            main_py
        )
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)
        return agent_module
    finally:
        os.chdir(old_cwd)


def discover_agents() -> list[Path]:
    """Descubre todos los agentes en la carpeta agents/."""
    agents = []
    for item in sorted(AGENTS_DIR.iterdir()):
        if item.is_dir() and (item / "main.py").exists():
            agents.append(item)
    return agents


# ============================================================
# RUN SINGLE MATCH
# ============================================================
def run_match(agent1_path: Path, agent2_path: Path, max_turns: int = 2000) -> dict:
    """Corre 1 partida entre 2 agentes. Devuelve el resultado."""
    # Cargar agentes
    try:
        agent1 = load_agent(agent1_path)
    except Exception as e:
        return {"error": f"No pude cargar {agent1_path.name}: {e}"}
    try:
        agent2 = load_agent(agent2_path)
    except Exception as e:
        return {"error": f"No pude cargar {agent2_path.name}: {e}"}

    # Importar el engine
    try:
        from cg.game import battle_start, battle_select, battle_finish
        from cg.api import to_observation_class
    except ImportError as e:
        return {"error": f"Engine no disponible: {e}. Bajar dataset de Kaggle."}

    # Verificar decks
    if len(agent1.my_deck) != 60 or len(agent2.my_deck) != 60:
        return {"error": f"Deck invalido: {len(agent1.my_deck)} o {len(agent2.my_deck)} cartas"}

    # Iniciar batalla
    try:
        obs, start_data = battle_start(agent1.my_deck, agent2.my_deck)
        if obs is None:
            return {"error": f"BattleStart fallo: error_player={start_data.errorPlayer}"}
    except Exception as e:
        return {"error": f"battle_start: {e}"}

    # Loop
    turn = 0
    error = None
    try:
        while turn < max_turns:
            # Determinar de quién es el turno
            if isinstance(obs, dict):
                current = obs.get("current", {})
                your_index = current.get("yourIndex", 0)
            else:
                your_index = 0

            # Llamar al agente correcto
            try:
                if your_index == 0:
                    actions = agent1.agent(obs)
                else:
                    actions = agent2.agent(obs)
            except Exception as e:
                error = f"Agent error turn {turn}: {type(e).__name__}: {e}"
                break

            # Submitir acciones
            try:
                obs = battle_select(actions)
            except Exception as e:
                error = f"battle_select turn {turn}: {type(e).__name__}"
                break

            turn += 1

            # Check winner
            if isinstance(obs, dict) and obs.get("winner") is not None:
                winner_idx = obs["winner"]
                winner_name = agent1_path.name if winner_idx == 0 else agent2_path.name
                battle_finish()
                return {
                    "winner": winner_name,
                    "winner_idx": winner_idx,
                    "turns": turn,
                    "agent1": agent1_path.name,
                    "agent2": agent2_path.name,
                }
    finally:
        try:
            battle_finish()
        except:
            pass

    return {
        "winner": None,
        "turns": turn,
        "agent1": agent1_path.name,
        "agent2": agent2_path.name,
        "error": error or "max_turns reached",
    }


# ============================================================
# RUN ARENA
# ============================================================
def run_arena(agent_paths: list, n_games: int = 10) -> dict:
    """Corre todos los agentes vs todos. n_games partidas por matchup."""
    results = {}
    matchups = []

    for i, a1 in enumerate(agent_paths):
        for a2 in agent_paths[i+1:]:
            matchup_key = f"{a1.name}_vs_{a2.name}"
            print(f"\n=== {matchup_key} ({n_games} games) ===")

            wins = {a1.name: 0, a2.name: 0, "draw": 0}
            errors = 0
            total_turns = []

            for game in range(n_games):
                # Alternar quién va primero
                if game % 2 == 0:
                    p1, p2 = a1, a2
                else:
                    p1, p2 = a2, a1

                result = run_match(p1, p2)

                if "error" in result:
                    errors += 1
                    print(f"  Game {game+1}: ERROR - {result['error']}")
                    continue

                winner = result.get("winner")
                turns = result.get("turns", 0)
                total_turns.append(turns)

                if winner is None:
                    wins["draw"] += 1
                    print(f"  Game {game+1}: DRAW ({turns} turns)")
                else:
                    # Determinar ganador normalizado al matchup_key
                    if winner == a1.name:
                        wins[a1.name] += 1
                    elif winner == a2.name:
                        wins[a2.name] += 1
                    print(f"  Game {game+1}: {winner} wins ({turns} turns)")

            # Guardar resultado del matchup
            matchup_result = {
                "matchup": matchup_key,
                "games": n_games,
                "errors": errors,
                "wins": wins,
                "avg_turns": sum(total_turns) / len(total_turns) if total_turns else 0,
            }
            matchups.append(matchup_result)
            results[matchup_key] = matchup_result

    return {"matchups": matchups, "agents": [a.name for a in agent_paths]}


# ============================================================
# LEADERBOARD
# ============================================================
def compute_leaderboard(arena_results: dict) -> list:
    """Calcula win rate total de cada agente."""
    agents = arena_results["agents"]
    stats = {a: {"wins": 0, "losses": 0, "draws": 0, "errors": 0} for a in agents}

    for m in arena_results["matchups"]:
        matchup = m["matchup"]
        a1, a2 = matchup.split("_vs_")
        wins = m["wins"]

        stats[a1]["wins"] += wins.get(a1, 0)
        stats[a1]["losses"] += wins.get(a2, 0)
        stats[a1]["draws"] += wins.get("draw", 0)
        stats[a1]["errors"] += m["errors"] // 2

        stats[a2]["wins"] += wins.get(a2, 0)
        stats[a2]["losses"] += wins.get(a1, 0)
        stats[a2]["draws"] += wins.get("draw", 0)
        stats[a2]["errors"] += m["errors"] // 2

    # Calcular win rate
    leaderboard = []
    for agent, s in stats.items():
        total = s["wins"] + s["losses"] + s["draws"]
        wr = s["wins"] / total * 100 if total > 0 else 0
        leaderboard.append({
            "agent": agent,
            "wins": s["wins"],
            "losses": s["losses"],
            "draws": s["draws"],
            "errors": s["errors"],
            "total_games": total,
            "win_rate": round(wr, 2),
        })

    leaderboard.sort(key=lambda x: x["win_rate"], reverse=True)
    return leaderboard


def print_leaderboard(leaderboard: list):
    """Imprime el leaderboard en formato tabla."""
    print("\n" + "=" * 70)
    print("🏆 LEADERBOARD 🏆")
    print("=" * 70)
    print(f"{'Rank':<5} {'Agent':<20} {'Wins':<6} {'Losses':<7} {'Draws':<6} {'WR%':<8}")
    print("-" * 70)

    for i, entry in enumerate(leaderboard):
        rank = f"#{i+1}"
        print(f"{rank:<5} {entry['agent']:<20} {entry['wins']:<6} "
              f"{entry['losses']:<7} {entry['draws']:<6} {entry['win_rate']:<8}")


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Arena runner para agentes Pokémon TCG")
    parser.add_argument("--games", type=int, default=10, help="Juegos por matchup (default: 10)")
    parser.add_argument("--agents", nargs="+", help="Agentes específicos (default: todos)")
    parser.add_argument("--output", default="leaderboard.json", help="Archivo de output (default: leaderboard.json)")
    parser.add_argument("--max-turns", type=int, default=2000, help="Max turnos por game (default: 2000)")
    args = parser.parse_args()

    print("🏆 Agente Arena Pokémon MX")
    print(f"   Games por matchup: {args.games}")
    print(f"   Max turns/game: {args.max_turns}")

    # Descubrir agentes
    if args.agents:
        agent_paths = [Path(a) for a in args.agents]
    else:
        agent_paths = discover_agents()

    if len(agent_paths) < 2:
        print(f"ERROR: Necesito al menos 2 agentes. Encontrados: {[a.name for a in agent_paths]}")
        return 1

    print(f"   Agentes: {[a.name for a in agent_paths]}")
    print()

    # Verificar engine
    try:
        import cg  # noqa
    except ImportError:
        print("=" * 70)
        print("⚠️  ERROR: Engine (cg/) no encontrado")
        print()
        print("Para correr la arena necesitás el dataset de Kaggle:")
        print("  1. Bajá el dataset: kaggle competitions download -c pokemon-tcg-ai-battle")
        print("  2. Descomprimilo en /workspace/arena/")
        print("  3. Asegurate que cg/ esté en PYTHONPATH")
        print("=" * 70)
        return 1

    # Correr arena
    t0 = time.time()
    results = run_arena(agent_paths, n_games=args.games)
    elapsed = time.time() - t0

    # Calcular leaderboard
    leaderboard = compute_leaderboard(results)

    # Imprimir
    print_leaderboard(leaderboard)
    print(f"\n⏱️  Tiempo total: {elapsed:.1f}s")
    print(f"📁 Resultados guardados en: {args.output}")

    # Guardar
    output_path = ARENA_DIR / args.output
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "games_per_matchup": args.games,
            "elapsed_seconds": round(elapsed, 2),
            "leaderboard": leaderboard,
            "matchups": results["matchups"],
        }, f, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
