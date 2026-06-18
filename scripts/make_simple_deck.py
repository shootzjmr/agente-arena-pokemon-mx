"""Ultra-minimal deck for sanity-testing the engine.

4x Pikachu (basic) + 56x Basic Lightning Energy.
No abilities, no evolution, no items, no supporters — pure basics.
"""

from collections import Counter
import sys
sys.path.insert(0, '.')

from cg.api import all_card_data

cards = all_card_data()
by_id = {c.cardId: c for c in cards}

# Find Pikachu (basic lightning)
pikachu_ids = [c.cardId for c in cards
               if c.basic and c.energyType == 4 and 'Pikachu' in c.name][:1]
basic_lightning = next(c.cardId for c in cards
                       if c.cardType == 5 and c.energyType == 4)
if not pikachu_ids:
    # Fallback: any basic lightning pokemon
    pikachu_ids = [c.cardId for c in cards
                   if c.basic and c.energyType == 4][:1]

deck = pikachu_ids * 4 + [basic_lightning] * 56
print(f'Deck: 4x #{pikachu_ids[0]} ({by_id[pikachu_ids[0]].name}) + 56x #{basic_lightning} ({by_id[basic_lightning].name})')
print(f'Deck length: {len(deck)}')

with open('simple_deck.csv', 'w') as f:
    for cid in deck:
        f.write(f'{cid}\n')
print('Saved to simple_deck.csv')
