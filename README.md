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
│   │   ├── main.py
│   │   ├── heuristic/
│   │   └── README.md
│   ├── terabox/               ← Agente experimental
│   ├── mega_lucario/          ← Agente oficial Kaggle
│   ├── zoni/                  ← 🏆 Zonideck v2-smart (Future Engine)
│   │   ├── main.py            (v2-smart: attack-by-damage + rush + HP retreat)
│   │   ├── deck.csv           (60 cards: Mega Latias ex + Iron Crown ex + Miraidon ex + ...)
│   │   ├── main-iteracion-anterior.py      (ZeroM v5 baseline, backup)
│   │   └── deck-iteracion-anterior.csv     (deck original antes del switch)
│   ├── ztich_na/
│   ├── zero_mexico/           ← 🏆 ZeroM v2-smart (with corrected ex IDs)
│   │   ├── main.py            (v2-smart: same heuristic as zoni)
│   │   ├── deck.csv           (60 cards: Koraidon, Raging Bolt ex, Teal Mask Ogerpon ex, ...)
│   │   ├── main-iteracion-anterior.py      (ZeroM v5 baseline, backup)
│   │   └── deck-iteracion-anterior.csv     (deck with non-ex IDs 95/27, fixed in v2)
│   └── ...
├── cg/                        ← CABT engine (api.py + libcg.so + game.py + sim.py + utils.py)
├── decks/                     ← 10 decks del meta (60 cartas cada uno)
├── arena/                     ← Arena runner + matchup results
├── docs/                      ← Documentación operacional
├── scripts/
│   ├── package_submission.py  ← Builds Kaggle tarball (includes cg/ submodule)
│   ├── bench_agents.py        ← Local A/B benchmark for two main.py agents
│   ├── bench_matchup.py
│   ├── play_match.py
│   └── ...
└── artifacts/                 ← Submission tarballs (gitignored)
```

## 🎯 Resultados recientes (junio 2026)

### Heurística v2-smart — primer score 600.0

Tras detectar que la heurística ZeroM v5 original puntuaba todos los `OptionType.ATTACK` con constante 1000 (eligiendo siempre el primer ataque disponible sin mirar el daño), iteramos sobre la heurística:

| Mejora | Qué cambia | Por qué |
|---|---|---|
| **Attack-by-real-damage** | Hardcoded `_ATTACK_DAMAGE` lookup sobre los IDs de ataque de nuestras cartas | En vez de elegir Strafe (40 dmg) sobre Mega Latias ex, ahora elige Illusory Impulse (300 dmg) cuando ambos están disponibles |
| **Rush mode** | +5000 al score de attackers/ataques/energía cuando `opp_prizes <= 2`; +1500 si `<= 4`; -1500 si nosotros vamos atrás | En endgame, prioriza cerrar antes que setupear |
| **HP-aware retreat** | Solo retira si `my_hp * 2 < opp_hp` o si estamos en rush mode | Antes retiraba en cualquier momento con score constante 100 |

**Implementación:** `_score_option()` en `agents/zoni/main.py` (idéntica en `agents/zero_mexico/main.py`). La heurística se activa via `DECK_NAME` env var (`zonideck` o `zerom`) que el main.py lee al import.

### Score Kaggle (leaderboard pública)

| Submission | Score | Ref | Fecha |
|---|---|---|---|
| **Zonideck v2-smart** | **600.0** | 53825905 | 2026-06-19 |
| **ZeroM v2-smart** | **600.0** | 53825907 | 2026-06-19 |
| ZeroM v4 (anterior mejor) | 518.4 | 53816562 | 2026-06-18 |
| TeraBox v4 | 458.9 | 53816707 | 2026-06-18 |
| Zonideck v1 | 443.6 | 53819413 | 2026-06-18 |
| ZeroM v5 | 324.4 | 53817547 | 2026-06-18 |

### Local A/B benchmark (50 games, alternating first player)

Mismo deck, comparando ZeroM v5 vs v2-smart:

| Deck | v5 wins | v2-smart wins | Delta |
|---|---|---|---|
| zonideck | 22/50 (44%) | 28/50 (56%) | **+12 pp** |
| zero_mexico | 22/50 (44%) | 28/50 (56%) | **+12 pp** |

Head-to-head zonideck vs zerom (ambos con v2-smart): zonideck gana 32/50 (64%) vs 18/50 (36%) — consistente con la elección de meta que tenía el orquestador.

### Fix crítico para Kaggle

Los 4 submits iniciales fallaron con `SubmissionStatus.ERROR` porque el tarball **no incluía el submodule `cg/`**. Kaggle NO provee `cg/` automáticamente — sin él, `from cg.api import ...` falla con `ModuleNotFoundError` al cargar el agente. El fix fue incluir en el tarball:

```
main.py
deck.csv
cg/__init__.py
cg/api.py
cg/game.py
cg/libcg.so
cg/sim.py
cg/utils.py
```

`scripts/package_submission.py` lo hace automáticamente.

## 🎮 Estado actual

| Componente | Estado |
|---|---|
| Template con heurística real | ✅ Listo |
| 10 decks validados | ✅ Listos en `/decks/` |
| Heurística v2-smart | ✅ Implementada y validada en Kaggle (600.0) |
| Local benchmark harness | ✅ `scripts/bench_agents.py` |
| Package submission con cg/ | ✅ `scripts/package_submission.py` (revisado) |
| Simulaciones | ✅ 13 matchups × 500-1000 games |
| 3 placeholders expertos | ✅ Reemplazados con template |

## 🚀 Quickstart

```bash
# 1. Empaquetar un agente para submission a Kaggle
python3 scripts/package_submission.py --agent agents/zoni --out artifacts/zoni.tar.gz

# 2. Benchmark local entre dos agentes (A/B heurístico)
python3 scripts/bench_agents.py \
    --agent0 agents/zoni \
    --agent1 agents/zero_mexico \
    --deck-name0 zonideck --deck-name1 zerom \
    --n 50

# 3. Validar un matchup con el harness viejo
python3 scripts/bench_matchup.py \
    --deck_a decks/terabox.csv \
    --deck_b decks/lucario.csv \
    --games 100

# 4. Correr arena completa
python3 arena/run_arena.py --games 50

# 5. Subir a Kaggle (requiere kaggle CLI + kaggle.json)
kaggle competitions submit -c pokemon-tcg-ai-battle \
    -f artifacts/zoni.tar.gz \
    -m "Zonideck v2-smart"
```

## 📚 Más info

- `agents/template/README.md` — Cómo usar el wrapper plan-first
- `decks/README.md` — Ranking y descripción de los 10 decks
- `scripts/README.md` — Qué hace cada script
- `docs/edge_cases.md` — Bugs conocidos del engine
- `docs/arena_rules.md` — Reglas de scoring
- `docs/estrategia.md` — Filosofía de los expertos

## 🛠️ Decisiones técnicas relevantes

- **`DECK_NAME` env var**: el `main.py` único de cada agente decide qué spec usar (zonideck vs zerom) leyendo esta var al import. Permite reusar la misma heurística en dos decks sin duplicar código.
- **Hardcoded damage table**: `_ATTACK_DAMAGE` dict con los 24 ataques de nuestros atacantes. Evita llamar `all_attack()` en runtime, que puede no estar disponible en el sandbox Kaggle. Si se agregan cartas nuevas, hay que actualizar este dict.
- **Path defaults portables**: el `main.py` resuelve `cg.api` desde el cwd del Kaggle sandbox (`/kaggle_simulations/agent`) sin paths absolutos del CT de desarrollo.
- **Bench harness con importlib**: `scripts/bench_agents.py` carga `cg/` via `importlib.util.spec_from_file_location` en vez de `sys.path.insert`, porque Python omite el cwd de sys.path cuando se corre un script por path relativo.
