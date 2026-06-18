# 📋 Template del Agente

Este template es el wrapper para todos los agentes del proyecto.

## 🎯 Características

1. **Heurística plan-first** (cuando está disponible): evalúa roles del deck antes de decidir
2. **Fallback robusto**: si la heurística no carga (no estás en Vast.ai), usa lógica mejorada con scoring
3. **Validación defensiva**: filtra acciones inválidas, maneja duplicados y `minCount`/`maxCount`
4. **Sin crashes**: cualquier error cae a safe-random en lugar de tirar IndexError

## 🚀 Uso

```bash
# 1. Copiá el template a tu agente
cp -r agents/template agents/mi_agente
cp decks/mi_deck.csv agents/mi_agente/deck.csv

# 2. Modificá la estrategia (opcional)
# Editá la función plan_first_strategy() en main.py

# 3. Listo, corré la arena
python3 arena/run_arena.py --games 10
```

## 🔌 Activar la heurística real

El template **auto-detecta** la heurística real. Solo funciona en Vast.ai:

```python
# En vast.ai, la heurística vive en /workspace/pokemon-tcg-agent/agent/heuristic.py
# El template intenta importarla automáticamente:
sys.path.insert(0, "/workspace/pokemon-tcg-agent")
from agent.heuristic import plan_first_action as _heuristic_fn
```

En otros ambientes (Kaggle, local) cae al fallback con scoring.

## 🎨 Personalizar la estrategia

Modificá la función `plan_first_strategy(obs, ctx)` en `main.py`:

```python
def plan_first_strategy(obs, ctx):
    # Tu lógica acá. ctx tiene:
    # - ctx.my_idx, ctx.opp_idx
    # - ctx.turn
    # - ctx.my_active, ctx.my_bench, ctx.my_hand, ctx.my_prizes
    # - ctx.opp_active, ctx.opp_bench, ctx.opp_prizes
    # - ctx.deck_left
    
    # Devolvé una lista de índices a las opciones en obs.select.option
    ...
```

## ⚠️ Gotchas del engine

1. **`obs.select.option`** puede tener items donde `card` es `None` (opciones abstractas, ej: "pasá turno")
2. **`maxCount=0`** significa "sin límite" en algunas versiones del engine
3. **Acciones inválidas → IndexError irrecuperable** (ver `docs/edge_cases.md`)
4. **Si tu estrategia devuelve `[]` y el engine pide respuesta**, el template rellena con safe-random

## 🧪 Testing

```bash
# Smoke test (sin engine, devuelve deck)
python3 main.py

# Test de validación
python3 -c "
from main import _validate_actions
class S:
    option = [None]*5; minCount=1; maxCount=2
print(_validate_actions([1,1,99,0], S()))
"
```

## 📊 Performance

| Escenario | Comportamiento |
|-----------|----------------|
| Con heurística + engine | Plan-first con roles del deck |
| Sin heurística + engine | Scoring por tipo de carta |
| Sin engine | Devuelve deck (game init) |
| Engine + error | Safe-random con validación |