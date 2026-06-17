# 🐛 Edge Cases del Engine

Bugs y comportamiento raro que encontramos en `libcg.so` (el simulador de Kaggle).

## 1. `select.context=7 (TO_HAND)` con `options=0` y `minCount>0`

**Síntoma:**
```python
Turno X: ERROR
  context=7, type=0, options=0, min=2, max=2
IndexError
```

**Causa:** El engine pide elegir 2 cartas para devolver a la mano, pero la lista de opciones está vacía. Estado irrecuperable.

**Workaround actual:** Ninguno. El agente muere.

**Causa probable:** Bug del engine cuando:
- El mazo del rival tiene 0 cartas que cumplen el criterio de "to hand"
- O el efecto de la carta del rival es inconsistente

**Acción:** Reportar a Kaggle Discussions al host `shige` con:
- Deck que lo reproduce
- Turno donde pasa
- Stack trace

## 2. El agente random del sample_submission rompe a los 24-80 turnos

**Síntoma:** El `main.py` que viene de ejemplo (`return random.sample(...)`) tira `IndexError` consistentemente.

**Causa:** Mismo edge case 1, pero dispara más seguido porque random no respeta el estado.

**Workaround:** Usar el agente oficial de Mega Lucario (Kiyota), que llega a 134 turnos.

## 3. `visualize_data()` puede fallar después de un `IndexError`

**Síntoma:** Después de un `IndexError`, llamar a `visualize_data()` también falla.

**Causa:** El `battle_ptr` queda corrupto.

**Workaround:** Llamar a `battle_finish()` y no usar más el battle.

## 4. El engine no es 100% fiel al TCG oficial

**Diferencias conocidas (del post de shige en Kaggle):**

1. **Ataques con efecto imposible NO son elegibles** (TCG oficial: declarar y el efecto falla)
   - Ej: ataque que pone Pokémon del deck al Bench cuando no hay espacio
   - Ej: ataque que roba cartas cuando el deck tiene 0
   - Ej: ataque que afecta la mano rival cuando está vacía

2. **Mega Zygarde ex "Nullifying Zero"**: el orden de asignación de daño es fijo (izquierda a derecha). En TCG oficial podés elegir.

3. **KO simultáneo**: Si los 2 Pokémon se KOean al mismo tiempo, el orden de tomar prizes es diferente al TCG oficial. En esta competencia, el resultado es **DRAW** (no uno gana).

## 🛠️ Cómo debuggear

```python
# Ver el estado completo en el momento del error
import json
print(json.dumps(obs, indent=2)[:2000])
```

El `obs` tiene:
- `select`: el select actual (context, type, options, minCount, maxCount)
- `current`: estado del juego (turn, players, etc.)
- `logs`: log de acciones

## 📚 Referencias

- Post oficial: https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/discussion/708586
- Engine source: `libcg.so` (binario compilado, no hay source público)
- API: `cg/api.py` (documentación de las clases)
