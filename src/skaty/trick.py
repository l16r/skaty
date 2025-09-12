from functools import reduce

from skaty.cards import Card
from skaty.exceptions import InvalidGameStateError
from skaty.player import Player
from skaty.rules import AbstractRuleSet


class Trick:
    _cards: list[Card]

    def __init__(self):
        self._cards = list()

    def add_card(self, card: Card):
        if self.is_complete():
            raise InvalidGameStateError("Trick already complete.")

        self._cards.append((card))

    def is_complete(self):
        return len(self._cards) == 3

    def get_winner(self, rule_set: AbstractRuleSet) -> int:
        if not self.is_complete():
            raise InvalidGameStateError("Trick not complete. Cannot calculate winner.")
        return rule_set.determine_trick_winner(self._cards)

    def getTrickPoints(self) -> int:
        """
        Returns the sum of all card points.
        """
        return reduce(lambda acc, c: acc + c.points, self._cards, 0)
