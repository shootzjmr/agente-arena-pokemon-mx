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
├── README.md                  ← estás acá
├── .gitignore
├── agents/
│   ├── template/              ← main.py base para nuevos agentes
│   ├── zoni/                  ← tu agente
│   ├── ztich_na/              ← agente de Ztich_NA
│   ├── zero_mexico/           ← agente de Zero Mexico
│   └── mega_lucario/          ← agente oficial de Kaggle (referencia)
├── arena/
│   ├── run_arena.py           ← corre todos los agentes vs todos
│   ├── leaderboard.json       ← resultados acumulados
│   └── matchups/              ← logs de cada battle
├── decks/
│   ├── mega_lucario.csv
│   ├── iono.csv
│   └── ...
├── docs/
│   ├── estrategia.md          ← resumen de las estrategias
│   ├── edge_cases.md          ← bugs conocidos del engine
│   └── arena_rules.md         ← cómo se corre la arena
└── scripts/
    ├── build_deck.py          ← genera deck.csv desde decklist
    ├── test_battle.py         ← corre 1 batalla
    └── eval_agent.py          ← evalúa 1 agente contra varios
```

## 🚀 Setup (para vos, Zoni)

### 1. Clonar el repo

```bash
git clone https://github.com/shootzjmr/agente-arena-pokemon-mx.git
cd agente-arena-pokemon-mx
```

### 2. Prender instance Vast.ai

1. Andá a https://cloud.vast.ai/create/
2. Filtros recomendados:
   - GPU: RTX 4090
   - Disk: ≥ 50 GB
   - Reliability: ≥ 95%
   - Region: Francia / España
   - Sort: precio ascendente
3. Template: **PyTorch (Vast)**
4. SSH key: la que uses (en `~/.ssh/id_ed25519.pub` o similar)
5. Click RENT

### 3. Conectar a la instance

```bash
ssh -p PUERTO root@IP_PUBLICA
```

### 4. Setup del entorno (en la instance)

```bash
# Activar venv
source /venv/main/bin/activate

# Instalar kagglehub
pip install kagglehub stable-baselines3

# Configurar Kaggle API
mkdir -p ~/.kaggle
# Copiá tu kaggle.json (ver docs/seguridad.md)
nano ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
```

### 5. Bajar el dataset

```bash
# Crear carpeta
mkdir -p /workspace/arena
cd /workspace/arena

# Bajar competition
kaggle competitions download -c pokemon-tcg-ai-battle
unzip pokemon-tcg-ai-battle.zip
```

### 6. Copiar los agentes al /workspace

```bash
# Desde CT 101 (vuestro lado):
scp -P PUERTO -r /root/agente-arena-pokemon-mx/* root@IP_PUBLICA:/workspace/arena/
```

### 7. Correr la arena

```bash
cd /workspace/arena/arena
python3 run_arena.py --games 10
```

## 🤝 Cómo contribuir (expertos en Discord)

1. Entrá al canal `#estrategia-TU_MAZO` (ej: `#estrategia-dragapult`)
2. Describí tu mazo y estrategia en español
3. **Zoni** traduce tu idea a una spec
4. **Hobot** (yo) codea el agente
5. Se sube a `agents/TU_HANDLE/`
6. Se corre en la arena
7. Ves los resultados en `#arena-results`
8. Dás feedback: "atacó mal en turno 3, debería haber hecho X"
9. Iteramos

### Formato sugerido para describir tu mazo

```
MAZO: Dragapult ex
CARTAS CLAVE:
  - 4x Dragapult ex (ataque principal)
  - 4x Dreepy (evoluciona)
  - 4x Rare Candy (evolución rápida)
  - 2x Carmine (roba cartas)
  - ...

ESTRATEGIA:
  - Turno 1: benchear Dreepy
  - Turno 2: Rare Candy → Dragapult ex
  - Turno 3+: Phantom Dive (120 daño) o Draco Meteor (100 x2)

WIN CONDITION: pegar 1HKO antes que el rival

MATCHUPS PROBLEMA:
  - vs Lucario: evitar sus ataques de efecto
  - vs Iono: robar con Carmine primero
```

## 🔒 Seguridad

**NUNCA subir a este repo:**
- `kaggle.json` (credenciales)
- Tokens de Vast.ai
- SSH keys privadas
- `.env` con secretos

Ver `docs/seguridad.md` para detalles.

## 📊 Estado actual

- [x] Estructura del repo
- [x] Agente Mega Lucario (Kaggle oficial, 65 votes)
- [x] Arena runner
- [ ] Agente de Zoni
- [ ] Agente de Ztich_NA
- [ ] Agente de Zero Mexico
- [ ] Edge case TO_HAND options=0 resuelto
- [ ] Submission a Kaggle

## 📜 Licencia

Privado. Solo para el equipo.

---

**Deadline Kaggle:** 13 septiembre 2026
**Prize pool:** $240,000 USD (8 finalistas × $30,000)
