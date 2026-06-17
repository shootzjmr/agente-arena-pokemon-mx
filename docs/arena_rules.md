# 📋 Reglas de la Arena

Cómo se corre la arena y cómo se cuenta el puntaje.

## Formato

- **Todos vs todos**: cada agente juega contra todos los demás
- **N games por matchup**: configurable (default 10)
- **Quién va primero alterna**: en game 1 el A va primero, en game 2 el B, etc.
- **Max turnos por game**: 2000 (después se considera draw)

## Scoring

| Resultado | Puntos |
|---|---|
| Victoria | 1 punto |
| Draw | 0.5 puntos |
| Derrota | 0 puntos |
| Error (engine crash) | 0 puntos + se cuenta como derrota |

**Win rate** = victorias / (wins + losses + draws) × 100

**Puntaje** = promedio de win rate sobre todos los oponentes

## Cómo correr

```bash
# Desde /workspace/arena/agents/arena/ (en la instance de Vast.ai)
python3 run_arena.py --games 10

# Con output custom
python3 run_arena.py --games 50 --output results_v1.json

# Solo 2 agentes
python3 run_arena.py --agents agents/zoni agents/ztich_na --games 20
```

## Output

### Consola
Tabla con rank, agent, wins, losses, draws, win rate.

### JSON (`leaderboard.json`)
```json
{
  "timestamp": "2026-06-17T03:30:00",
  "games_per_matchup": 10,
  "elapsed_seconds": 120.5,
  "leaderboard": [
    {
      "agent": "mega_lucario",
      "wins": 5,
      "losses": 3,
      "draws": 2,
      "errors": 0,
      "total_games": 10,
      "win_rate": 50.0
    }
  ],
  "matchups": [
    {
      "matchup": "zoni_vs_mega_lucario",
      "games": 10,
      "errors": 1,
      "wins": {"zoni": 4, "mega_lucario": 5, "draw": 0},
      "avg_turns": 87.3
    }
  ]
}
```

## Frecuencia sugerida

- **Después de cambios grandes**: correr arena completa
- **Entre experiments**: 5-10 games por matchup está bien
- **Para validar**: 20-50 games por matchup

## Cosas a tener en cuenta

1. **Un agente con 100% win rate no es realista**. Si pasa, algo está mal.
2. **Diferencias < 5% no son significativas** con pocas games. Corré más games.
3. **Errores del engine afectan el ranking**. Si un agente crashea, se cuenta como derrota.

## Submission a Kaggle

Una vez que tengamos el mejor agente:

1. Empaquetar en `submission.tar.gz`:
   - `main.py`
   - `cg/` (engine)
   - `deck.csv`
2. Subir a Kaggle vía la UI o CLI
3. Esperar que Kaggle lo corra contra otros
4. Ver el leaderboard oficial

Más detalles en `docs/kaggle_submission.md` (pendiente).
