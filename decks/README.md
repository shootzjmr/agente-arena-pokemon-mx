# 🏆 Meta Decks — Kaggle Pokémon TCG Agent Arena

10 mazos testeados en simulaciones con `bench_matchup.py`.

## 📊 Ranking (N=1000 games contra meta de 5)

| Rank | Deck | Win% vs meta | N total | Notas |
|:----:|------|:---:|:---:|-------|
| 🥇 1 | **TeraBox** | 50.6% | 6100 | Mega Kangaskhan + Latias + Lillie Clefairy |
| 🥈 2 | HyperLatias | 49.5% | 6000 | Latias + Koraidon (counter) |
| 🥉 3 | FrostWall | 49.9% | 3000 | Abomasnow variant (copia taboutmhamed) |
| 4 | Mega Dragonite | 49.3% | 4000 | Dragon control |
| 5 | Lucario | 48.7% | 6100 | Agente oficial Kaggle |
| 6 | Raging Bolt | 48.5% | 4000 | Dragon aggro |
| 7 | Abomasnow | 48.0% | 6100 | Freeze archetype |
| 8 | Pikachu | 47.2% | 4000 | Lightning aggro |
| 9 | Iono | 46.8% | 6100 | Hand disruption |
| 10 | Dragapult | 46.5% | 6100 | Ghost control |

## 📁 Estructura de cada deck

```
decks/<nombre>.csv    # 60 líneas, una por carta (card_id entero)
```

## 🔬 Validación

Cada deck fue validado con `bench_matchup.py` corriendo 500-1000 games vs cada
oponente del meta. Resultados en `arena/matchups/<deck>_vs_<oponente>.json`.

## 🎯 Cómo probar

```bash
python3 scripts/bench_matchup.py \
    --deck_a decks/terabox.csv \
    --deck_b decks/lucario.csv \
    --games 100 \
    --output arena/matchups/terabox_vs_lucario.json
```