"""
Genera deck.csv a partir de una decklist (cantidad + ID + nombre).

USO:
    python3 build_deck.py
    # Editá la decklist abajo con tu mazo
"""

import os
from pathlib import Path

# ============================================================
# EDITÁ ESTA DECKLIST CON TU MAZO
# Formato: (card_id, cantidad, nombre)
# Total DEBE ser 60
# ============================================================
DECKLIST = [
    # (id, count, name)
    # Ejemplo:
    # (673, 2, "Makuhita"),
    # (674, 2, "Hariyama"),
    # ...
    # (6, 13, "Basic Fighting Energy"),
]

OUTPUT_PATH = Path(__file__).parent.parent / "decks" / "mi_mazo.csv"


def main():
    if not DECKLIST:
        print("ERROR: DECKLIST vacía. Editá este archivo y agregá tus cartas.")
        return 1

    total = sum(c[1] for c in DECKLIST)
    if total != 60:
        print(f"ERROR: total = {total}, debe ser 60")
        return 1

    # Verificar max 4 copias por carta (regla TCG)
    counts = {}
    for card_id, count, _ in DECKLIST:
        counts[card_id] = counts.get(card_id, 0) + count
    for card_id, count in counts.items():
        if count > 4:
            print(f"ERROR: carta {card_id} tiene {count} copias, máximo 4")
            return 1

    # Escribir deck.csv
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        for card_id, count, _ in DECKLIST:
            for _ in range(count):
                f.write(f"{card_id}\n")

    print(f"OK: {total} cartas guardadas en {OUTPUT_PATH}")
    print()
    print("Decklist:")
    for card_id, count, name in DECKLIST:
        print(f"  {count}x {name} (id={card_id})")
    return 0


if __name__ == "__main__":
    exit(main())
