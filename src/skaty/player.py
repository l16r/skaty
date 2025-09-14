from enum import Enum

from skaty.cards import Card


class Role(Enum):
    OPPOSITION = 0
    DECLARER = 1


class Player:
    _name: str
    role: Role
    _hand: list[Card]

    def __init__(self, name: str):
        self._name = name
        self.role = Role.OPPOSITION
        self._hand = list()

    @property
    def name(self) -> str:
        return self._name

    @property
    def hand(self) -> list[Card]:
        return self._hand

    def addCard(self, card: Card):
        self._hand.append(card)

    def addCards(self, cards: list[Card]):
        for c in cards:
            self.addCard(c)

    def removeCard(self, card: Card):
        self._hand.remove(card)
