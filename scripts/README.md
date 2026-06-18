# 📜 Scripts

## `build_deck.py` (template)

Genera `deck.csv` desde una decklist en texto plano. Útil para crear nuevos decks.

```bash
python3 scripts/build_deck.py
```

## `test_battle.py` (template)

Corre una batalla simple entre 2 agentes para debugging rápido.

```bash
python3 scripts/test_battle.py agents/zoni agents/ztich_na
```

## `bench_matchup.py` (validado, 103 líneas)

**Script principal para benchmarks.** Corre N games entre dos decks y devuelve
win rate con intervalo de confianza. Más robusto que `run_arena.py` para validación
de un deck específico.

```bash
python3 scripts/bench_matchup.py \
    --deck_a decks/terabox.csv \
    --deck_b decks/lucario.csv \
    --games 1000 \
    --output arena/matchups/terabox_vs_lucario_n1000.json
```

**Output JSON:**
```json
{
  "agent_a": "terabox",
  "agent_b": "lucario",
  "games": 1000,
  "wins_a": 520,
  "wins_b": 460,
  "draws": 20,
  "win_rate_a": 0.530,
  "ci_95": [0.498, 0.562]
}
```

## `play_match.py` (validado)

Corre 1 sola batalla entre dos agentes con output detallado paso a paso. Útil
para debugging heurística.

```bash
python3 scripts/play_match.py \
    decks/terabox.csv \
    decks/lucario.csv \
    --turns 200
```

## `make_simple_deck.py` (utility)

Genera deck random para smoke tests.

```bash
python3 scripts/make_simple_deck.py > /tmp/random_deck.csv
```

## `package_submission.py` (validado)

Empaqueta un agente en formato de submission de Kaggle (tarball con `main.py` +
`deck.csv`).

```bash
python3 scripts/package_submission.py \
    --agent agents/terabox \
    --output terabox_submission.tar.gz
```