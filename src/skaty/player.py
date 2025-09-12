from enum import Enum

from skaty.cards import Card


class Role(Enum):
    Defender = 0
    Declarer = 1


class Player:
    _role: Role
    _cards: list[Card]

    def __init__(self, name: str):
        self._name = name
