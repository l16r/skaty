from functools import reduce
from typing import Optional

from skaty.cards import Card
from skaty.exceptions import (
    TrickFinishedError,
    TrickNotFinishedError,
)
from skaty.rules import AbstractRuleSet, GameType


class Trick:
    _cards: list[Card]

    def __init__(self):
        self._cards = list()

    @property
    def first_card(self) -> Optional[Card]:
        if len(self._cards) == 0:
            return None
        return self._cards[0]

    @property
    def len(self) -> int:
        return len(self._cards)

    @property
    def cards(self) -> list[Card]:
        return self._cards

    def add_card(self, card: Card):
        """
        Appends a card to the trick.

        Raises:
            TrickFinishedError: If the trick is already complete.
        """

        if self.is_complete():
            raise TrickFinishedError()

        self._cards.append((card))

    def pop(self) -> Optional[Card]:
        """
        Returns the last card played in the trick.
        Returns None if trick has no cards.
        """
        if len(self._cards) == 0:
            return None
        return self._cards.pop()

    def is_complete(self):
        return len(self._cards) == 3

    def get_winner(self, rule_set: AbstractRuleSet, game_type: GameType) -> int:
        """
        Determines the winner of the trick in its order (i.e. 0 if the first card wins the trick...).

        Raises:
            TrickNotFinishedError: If the trick does not contain exactly 3 cards.
        """
        if not self.is_complete():
            raise TrickNotFinishedError()
        return rule_set.determine_trick_winner(self._cards, game_type)

    def get_trick_points(self) -> int:
        """
        Returns the sum of all card points. The trick does not have to be completed.
        """
        return reduce(lambda acc, c: acc + c.points, self._cards, 0)
