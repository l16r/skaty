import random
from enum import IntEnum


class Rank(IntEnum):
    # Using rank values to differentiate between values
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
        if self in (Rank.TEN, Rank.KING):
            return 10
        elif self == Rank.ACE:
            return 11
        elif self == Rank.QUEEN:
            return 3
        elif self == Rank.JACK:
            return 2
        # 7,8,9
        return 0


class Suit(IntEnum):
    """
    ISkO 1.2.1.
    """

    DIAMONDS = 0
    HEARTS = 1
    SPADES = 2
    CLUBS = 3


class Card:
    def __init__(self, rank: Rank, suit: Suit) -> None:
        self._rank = rank
        self._suit = suit

    @property
    def rank(self) -> Rank:
        return self._rank

    @property
    def suit(self) -> Suit:
        return self._suit

    @property
    def points(self) -> int:
        return self._rank.points

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit is other.suit and self.rank is other.rank

    def __str__(self) -> str:
        return f"{self.rank.name} of {self.suit.name}"

    def __repr__(self) -> str:
        return f"Card({self.rank.name}, {self.suit.name})"

    def __hash__(self) -> int:
        return hash((self.suit, self.rank))


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
    return random.sample(deck, len(deck))
