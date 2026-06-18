# 🏆 TeraBox Agent

**Rank:** #1 del meta con 50.6% win rate (N=6100 games vs 6 oponentes)

## Deck (60 cartas)

| Tipo | Cantidad | Cartas |
|------|:--------:|--------|
| Pokémon | 22 | 4 Mega Kangaskhan ex MEG 104, 4 Meowth ex POR 62, 4 Lillie's Clefairy ex JTG 56, 3 Latias ex SSP 76, 2 Wellspring Mask Ogerpon ex TWM 64, 2 Fezandipiti ex ASC 142, 1 Moltres PFL 14, 1 Chien-Pao SSP 56, 1 Koraidon ex ASC 121 |
| Trainer | 28 | 4 Crispin SCR 133, 3 Boss's Orders MEG 114, 2 Ciphermaniac's Codebreaking TEF 145, 1 Cyrano SSP 170, 4 Ultra Ball MEG 131, 4 Dusk Ball SSP 175, 3 Wondrous Patch PFL 94, 1 Prime Catcher TEF 157, 2 Lillie's Pearl JTG 151, 4 Area Zero Underdepths SCR 131 |
| Energy | 10 | 4 Psychic MEE 5, 2 Water MEE 3, 2 Fighting MEE 6, 1 Telepathic Psychic POR 88, 1 Fire MEE 2 |

## Estrategia

Plan-first con heurística `agents/template/heuristic/heuristic.py`. Roles del deck:

- **Draw engine**: Lillie's Clefairy ex (HandRefill), Crispin (energies + draw)
- **Stall**: Area Zero Underdepths (prizes denial), Wellspring Mask Ogerpon ex
- **Setup turn 1**: Ultra Ball/Dusk Ball → básico → bench
- **Pressure**: Boss's Orders para traer weakened threat
- **Wincon**: Mega Kangaskhan ex para prize race
