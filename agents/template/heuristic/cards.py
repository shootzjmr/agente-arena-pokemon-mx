"""Card database cache.

Loads all card data once via the native SDK, then exposes fast lookups by
card ID. Most agents only need card name, type, HP, attacks and a few
classification flags, so this module keeps a lightweight dict keyed by
``cardId`` to avoid re-parsing the SDK during a match.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from functools import lru_cache

# Make sure cg/ is importable when this module is run directly.
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from cg.api import all_card_data, all_attack  # noqa: E402
from cg.api import CardType  # noqa: E402


@dataclass(frozen=True)
class AttackInfo:
    attack_id: int
    name: str
    damage: int
    energies: tuple[int, ...]   # tuple of EnergyType ints
    text: str = ""


@dataclass(frozen=True)
class CardInfo:
    card_id: int
    name: str
    card_type: int              # CardType int (0=PKMN,1=ITEM,2=TOOL,3=SUPPORTER,4=STADIUM,5=BASIC_ENERGY,6=SPECIAL_ENERGY)
    energy_type: int            # EnergyType int
    hp: int
    retreat_cost: int
    weakness: int | None
    resistance: int | None
    basic: bool
    stage1: bool
    stage2: bool
    ex: bool
    mega_ex: bool
    tera: bool
    ace_spec: bool
    evolves_from: str | None
    attacks: tuple[AttackInfo, ...]
    skills: tuple[tuple[str, str], ...]   # (name, text)
    is_pokemon: bool = field(init=False)
    is_basic_energy: bool = field(init=False)
    is_special_energy: bool = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "is_pokemon", self.card_type == 0)
        object.__setattr__(self, "is_basic_energy", self.card_type == 5)
        object.__setattr__(self, "is_special_energy", self.card_type == 6)


@lru_cache(maxsize=1)
def build_card_db() -> dict[int, CardInfo]:
    """Load and cache card metadata from the native SDK."""
    cards = all_card_data()
    attacks = all_attack()
    attack_by_id = {a.attackId: a for a in attacks}
    db: dict[int, CardInfo] = {}
    for c in cards:
        atk_infos = tuple(
            AttackInfo(
                attack_id=a.attackId,
                name=a.name,
                damage=a.damage,
                energies=tuple(a.energies),
                text=a.text,
            )
            for a in (attack_by_id[a_id] for a_id in c.attacks if a_id in attack_by_id)
        )
        skills = tuple((s.name, s.text) for s in c.skills)
        db[c.cardId] = CardInfo(
            card_id=c.cardId,
            name=c.name,
            card_type=c.cardType,
            energy_type=c.energyType,
            hp=c.hp,
            retreat_cost=c.retreatCost,
            weakness=c.weakness,
            resistance=c.resistance,
            basic=c.basic,
            stage1=c.stage1,
            stage2=c.stage2,
            ex=c.ex,
            mega_ex=c.megaEx,
            tera=c.tera,
            ace_spec=c.aceSpec,
            evolves_from=c.evolvesFrom,
            attacks=atk_infos,
            skills=skills,
        )
    return db


def get_card(card_id: int) -> CardInfo | None:
    """Return cached CardInfo for ``card_id`` or ``None`` if unknown."""
    return build_card_db().get(card_id)


def card_name(card_id: int) -> str:
    info = get_card(card_id)
    return info.name if info else f"#{card_id}"


# A small helper: classify a deck by its primary energy type.
def primary_energy_type(deck_card_ids: list[int]) -> int | None:
    """Return the most common energy type among non-energy cards in the deck."""
    from collections import Counter
    db = build_card_db()
    counter: Counter[int] = Counter()
    for cid in deck_card_ids:
        info = db.get(cid)
        if info is None:
            continue
        if info.is_pokemon and info.energy_type is not None:
            counter[info.energy_type] += 1
    if not counter:
        return None
    return counter.most_common(1)[0][0]


if __name__ == "__main__":
    db = build_card_db()
    print(f"Loaded {len(db)} cards")
    for cid in (1, 3, 721, 723):
        c = db.get(cid)
        if c:
            print(f"  #{cid}: {c.name} type={c.energy_type} hp={c.hp} attacks={[(a.name,a.damage) for a in c.attacks]}")
