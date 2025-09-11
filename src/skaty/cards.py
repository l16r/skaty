from enum import Enum


class Value(Enum):
    """
    ISkO 1.2.2.
    """

    SEVEN = 0
    EIGHT = 0
    NINE = 0
    JACK = 2
    QUEEN = 3
    KING = 4
    TEN = 10
    ACE = 11


class Suit(Enum):
    """
    ISkO 1.2.1.
    """

    DIAMONDS = 9
    HEARTS = 10
    SPADES = 11
    CLUBS = 12


class Card:
    def __init__(self, value: Value, suit: Suit) -> None:
        self._value = value
        self._suit = suit

    @property
    def value(self) -> Value:
        return self._value

    @property
    def suit(self) -> Suit:
        return self._suit

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit is other.suit and self.value is other.value
