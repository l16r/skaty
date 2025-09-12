from functools import reduce

from skaty.cards import Card
from skaty.exceptions import InvalidGameStateError
from skaty.player import Player
from skaty.rules import AbstractRuleSet


class Trick:
    _cards: list[tuple[Card, Player]]

    def __init__(self):
        self._cards = list()

    def add_card(self, card: Card, player: Player):
        if self.is_complete():
            raise InvalidGameStateError("Trick already complete.")

        self._cards.append((card, player))

    def is_complete(self):
        return len(self._cards) == 3

    def get_winner(self, rule_set: AbstractRuleSet) -> Player:
        if not self.is_complete():
            raise InvalidGameStateError("Trick not complete. Cannot calculate winner.")
        return self._cards[rule_set.determine_trick_winner(self._cards)][1]

    def getTrickPoints(self) -> int:
        """
        Returns the sum of all card points.
        """
        return reduce(lambda acc, c: acc + c[0].points, self._cards, 0)
