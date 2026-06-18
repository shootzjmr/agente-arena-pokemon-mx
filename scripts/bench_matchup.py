"""Benchmark heuristic with deck A vs heuristic with deck B."""
import sys, time, random, json, os
from collections import Counter
from cg.game import battle_start, battle_select, battle_finish
from agent.heuristic import choose_action as heuristic_choose


def load_deck(path):
    with open(path) as f:
        return [int(l.strip()) for l in f if l.strip()]


def validate_pick(pick, sel, rng):
    opts = sel.get("option", [])
    if not opts:
        return pick
    mn, mx = sel.get("minCount", 0), sel.get("maxCount", 1)
    if mx <= 0: mx = max(mn, 1)
    pick = [i for i in pick if 0 <= i < len(opts)]
    pick = list(dict.fromkeys(pick))
    if len(pick) < mn:
        pool = [i for i in range(len(opts)) if i not in pick]
        rng.shuffle(pool)
        pick += pool[:mn - len(pick)]
    if len(pick) > mx:
        pick = pick[:mx]
    if not pick:
        pick = [rng.randrange(len(opts))]
    return pick


def play_one(deck0, deck1, seed):
    rng = random.Random(seed)
    obs, _ = battle_start(deck0, deck1)
    if obs is None:
        return -1, 0
    swap = seed % 2
    a0, a1 = heuristic_choose, heuristic_choose
    agents = (a0, a1) if swap == 0 else (a1, a0)
    steps = 0
    while obs and obs.get('select') and steps < 600:
        steps += 1
        cur = obs.get('current') or {}
        if cur.get('result', -1) != -1:
            break
        sel = obs.get('select') or {}
        opts = sel.get('option', [])
        if not opts:
            break
        yi = cur.get('yourIndex', 0)
        try:
            pick = (agents[0] if yi == 0 else agents[1])(obs)
        except Exception:
            pick = []
        pick = validate_pick(pick, sel, rng)
        try:
            obs = battle_select(pick)
        except Exception:
            break
    cur = obs.get('current') if obs else {}
    res = cur.get('result', -1) if cur else -1
    try: battle_finish()
    except: pass
    if res in (0, 1) and swap == 1:
        res = 1 - res
    return res, steps


def run(deck0_path, deck1_path, n, seed_base=0):
    deck0 = load_deck(deck0_path)
    deck1 = load_deck(deck1_path)
    results = Counter()
    total_steps = 0
    t0 = time.time()
    for g in range(n):
        res, steps = play_one(deck0, deck1, seed_base + g)
        results[res] += 1
        if res in (0, 1):
            total_steps += steps
    elapsed = time.time() - t0
    decided = results[0] + results[1] + results[2]
    avg_steps = (total_steps / decided) if decided else 0
    return {
        'deck0': os.path.basename(os.path.dirname(deck0_path)),
        'deck1': os.path.basename(os.path.dirname(deck1_path)),
        'n': n,
        'elapsed_s': round(elapsed, 2),
        'games_per_s': round(n / elapsed, 1) if elapsed > 0 else 0,
        'a0_win': results[0],
        'a1_win': results[1],
        'draw': results[2],
        'err': results[-1] if -1 in results else 0,
        'a0_win_pct': round(100 * results[0] / decided, 2) if decided else 0,
        'avg_steps': round(avg_steps, 1),
    }


if __name__ == '__main__':
    deck0 = sys.argv[1]
    deck1 = sys.argv[2]
    n = int(sys.argv[3])
    out = run(deck0, deck1, n)
    print(json.dumps(out))
