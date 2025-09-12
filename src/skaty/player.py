from enum import Enum

from skaty.cards import Card


class Role(Enum):
    OPPOSITION = 0
    DECLARER = 1


class Player:
    _role: Role
    _hand: list[Card]

    def __init__(self, name: str):
        self._name = name
