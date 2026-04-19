import random
from enum import IntEnum


class Rank(IntEnum):
    """
    Rank values to differentiate the cards value. These are not to be confused with their actual points according to ISkO 1.2.2 which are returned with the points method.
    """

    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def points(self) -> int:
        """
        Returns the point value of the card rank in Skat (ISkO 1.2.2).
        """
        if self == Rank.ACE:
            return 11
        elif self == Rank.TEN:
            return 10
        elif self == Rank.KING:
            return 4
        elif self == Rank.QUEEN:
            return 3
        elif self == Rank.JACK:
            return 2
        # 7,8,9
        return 0


class Suit(IntEnum):
    """
    Suits according to ISkO 1.2.1.
    """

    DIAMONDS = 0
    """DIAMONDS"""
    HEARTS = 1
    """HEARTS"""
    SPADES = 2
    """SPADES"""
    CLUBS = 3
    """CLUBS"""


class Card:
    """Card identified by rank and suit."""

    __slots__ = "_rank", "_suit", "points", "uid"
    _instances: dict[tuple[Rank, Suit], "Card"] = {}

    def __new__(cls, rank: Rank, suit: Suit):
        key = (rank, suit)
        if key not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(self, rank: Rank, suit: Suit):
        if hasattr(self, "uid"):
            return

        self._rank = rank
        self._suit = suit
        self.points = rank.points
        self.uid = self._suit.value * 8 + (self._rank.value - 7)

    @property
    def rank(self) -> Rank:
        """Rank of card."""
        return self._rank

    @property
    def suit(self) -> Suit:
        """Suit of card."""
        return self._suit

    def __str__(self) -> str:
        return f"{self.rank.name} of {self.suit.name}"

    def __repr__(self) -> str:
        return f"Card({self.rank.name}, {self.suit.name})"


def create_deck() -> list[Card]:
    """
    Creates an unshuffled Skat deck.
    """
    deck = list()
    for suit in Suit:
        for rank in Rank:
            deck.append(Card(rank, suit))
    return deck


def shuffle_deck(deck: list[Card]) -> list[Card]:
    """Shuffles a given deck of cards."""
    return random.sample(deck, len(deck))
