from dataclasses import dataclass
from functools import total_ordering

from skaty.cards import Card
from skaty.exceptions import IncompatibleRulesError
from skaty.rules import AbstractRuleSet, GameType


@total_ordering
@dataclass(frozen=True)
class ComparableCard:
    """
    A wrapper around a Card instance that makes in comparable based on a given AbstractRuleSet. Can be used to sort or compare cards in a specific game context.
    """

    card: Card
    rule_set: AbstractRuleSet
    game_type: GameType

    def __lt__(self, other: object) -> bool:
        """
        Compares to another card based on rule_set.

        Raises:
            IncomptabileRulesError: If both cards have another ruleset.
        """
        if not isinstance(other, ComparableCard):
            return False
        if self.rule_set is not other.rule_set:
            raise IncompatibleRulesError(
                "Cannot compare cards using different rule sets."
            )

        self_value = self.rule_set.get_card_effective_rank_value(
            self.card, self.game_type
        )
        other_value = self.rule_set.get_card_effective_rank_value(
            other.card, self.game_type
        )
        return self_value < other_value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ComparableCard):
            return False
        return self.card == other.card
