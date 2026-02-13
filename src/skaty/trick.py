from functools import reduce
from typing import Optional

from skaty.cards import Card
from skaty.exceptions import InvalidGameStateError
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

    def add_card(self, card: Card):
        if self.is_complete():
            raise InvalidGameStateError("Trick already complete.")

        self._cards.append((card))

    def is_complete(self):
        return len(self._cards) == 3

    def get_winner(self, rule_set: AbstractRuleSet, game_type: GameType) -> int:
        """
        Get the index of the winner in the trick in the order the trick was played.
        """
        if not self.is_complete():
            raise InvalidGameStateError("Trick not complete. Cannot calculate winner.")
        return rule_set.determine_trick_winner(self._cards, game_type)

    def get_trick_points(self) -> int:
        """
        Returns the sum of all card points. The trick does not have to be completed.
        """
        return reduce(lambda acc, c: acc + c.points, self._cards, 0)
