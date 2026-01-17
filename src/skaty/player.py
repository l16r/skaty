from enum import Enum
from typing import Optional

from skaty.cards import Card


class Role(Enum):
    OPPOSITION = 0
    DECLARER = 1


class Player:
    _name: str
    role: Role
    _hand: list[Card]

    def __init__(self, name: str, hand: Optional[list[Card]] = None):
        self._name = name
        self.role = Role.OPPOSITION
        self._hand = hand if hand is not None else []

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name

    @property
    def hand(self) -> list[Card]:
        return self._hand

    def add_card(self, card: Card):
        self._hand.append(card)

    def add_cards(self, cards: list[Card]):
        for c in cards:
            self.add_card(c)

    def remove_card(self, card: Card):
        self._hand.remove(card)
