# 🏆 Agente Arena Pokémon MX

Arena de agentes IA para **Pokémon TCG AI Battle Challenge** (Kaggle).

3 expertos en Pokémon TCG compiten con agentes IA que se corren en Vast.ai.

## 👥 Equipo

| Handle | Nombre | Rol |
|---|---|---|
| **Zoni** | Shootz JMR | Orquestador (dev, repo, Vast.ai) |
| **Ztich_NA** | - | Experto Pokémon TCG |
| **Zero Mexico** | - | Experto Pokémon TCG |
| **@Hobot** | - | AI Engineer (escribe el código) |

## 🎯 Objetivo

Construir **múltiples agentes** (uno por experto), hacerlos competir entre sí en una **arena local** para ver cuál gana más partidas, y eventualmente **subir el mejor a Kaggle** para ganar los **$240,000 USD** del primer lugar.

## 🏗️ Arquitectura

```
Expertos de Pokémon (chatean en Discord)
    ↓ (describen sus mazos y estrategias en español)
Orquestador "Zoni" (vos)
    ↓ (traducen las ideas a specs técnicas)
AI Engineer "Hobot" (yo)
    ↓ (escriben el código de los agentes)
Agentes en /agents/
    ↓ (corre todos vs todos)
Arena.run_arena.py
    ↓ (genera leaderboard)
Discord #arena-results
```

**Los expertos NO necesitan ver este repo.** Solo chatean en Discord.

## 📁 Estructura del repo

```
agente-arena-pokemon-mx/
├── README.md
├── agents/
│   ├── template/              ← Wrapper plan-first + heurística incluida
│   │   ├── main.py            (305 líneas: heurística + scoring + validación)
│   │   ├── heuristic/         ← Heurística real (heuristic.py, cards.py, state_view.py)
│   │   └── README.md
│   ├── terabox/               ← 🏆 Nuestro agente #1 (50.6% win rate)
│   ├── mega_lucario/          ← Agente oficial Kaggle
│   ├── zoni/                  ← (usa template, default Lucario)
│   ├── ztich_na/              ← (usa template, default Lucario)
│   └── zero_mexico/           ← (usa template, default Lucario)
├── decks/                     ← 10 decks del meta (60 cartas cada uno)
│   ├── abomasnow.csv
│   ├── dragapult.csv
│   ├── frostwall.csv
│   ├── hyperlatias.csv
│   ├── iono.csv
│   ├── lucario.csv
│   ├── mega_dragonite.csv
│   ├── mega_lucario.csv
│   ├── pikachu.csv
│   ├── raging_bolt.csv
│   └── terabox.csv            ← 🏆 #1 del meta
├── arena/
│   ├── run_arena.py           ← Corre todos vs todos (350 líneas)
│   └── matchups/              ← Resultados de simulaciones (N=500-1000)
├── docs/                      ← Documentación operacional
└── scripts/                   ← Tools (bench_matchup, play_match, package_submission)
```

## 🎮 Estado actual

| Componente | Estado |
|------------|--------|
| Template con heurística real | ✅ Listo (305 líneas, auto-detecta Vast.ai) |
| 10 decks validados | ✅ Listos en `/decks/` |
| Ranking del meta | ✅ 50.6% TeraBox, 49.5% HyperLatias, etc. |
| Simulaciones | ✅ 13 matchups × 500-1000 games |
| 3 placeholders expertos | ✅ Reemplazados con template |
| Mega Lucario Kaggle | ⚠️  Solo placeholder (main.py real está en el notebook) |

## 🚀 Quickstart

```bash
# 1. Validar un matchup
python3 scripts/bench_matchup.py \
    --deck_a decks/terabox.csv \
    --deck_b decks/lucario.csv \
    --games 100

# 2. Correr arena completa
python3 arena/run_arena.py --games 50

# 3. Empaquetar agente para submission
python3 scripts/package_submission.py \
    --agent agents/terabox \
    --output terabox_submission.tar.gz
```

## 📚 Más info

- `agents/template/README.md` — Cómo usar el wrapper plan-first
- `decks/README.md` — Ranking y descripción de los 10 decks
- `scripts/README.md` — Qué hace cada script
- `docs/edge_cases.md` — Bugs conocidos del engine
- `docs/arena_rules.md` — Reglas de scoring
- `docs/estrategia.md` — Filosofía de los expertos