from typing import Any, Iterator, Optional, Self

from skaty.cards import Card, create_deck, shuffle_deck
from skaty.exceptions import (
    InvalidActionError,
    InvalidGameStateError,
)
from skaty.rules import (
    AbstractRuleSet,
    Action,
    GamePhase,
    GamePhases,
    GameType,
    PlayerIdx,
    PlayerPosition,
)
from skaty.trick import Trick


class GameState:
    """
    Contains all the state of a specific game.
    State should never be directly modified by the user. Instead, state modification is left to the rule set and actions.
    Actions are applied/undone by directly calling their apply/undo method.
    The validity of actions and calculation of game score is strictly delegated to the rule set passed.
    """

    __slots__ = (
        "_rule_set",
        "_log",
        "phase",
        "game_type",
        "_forehand",
        "_middlehand",
        "_backhand",
        "active_player",
        "hands",
        "skat",
        "points",
        "current_trick",
        "trick_history",
        "action_history",
        "undo_memory",
        "bid",
        "tops",
        "hand_available",
        "declarer_idx",
    )

    def __init__(
        self,
        rule_set: AbstractRuleSet["GameState"],
        dealer_idx: PlayerIdx,
        hands: list[list[Card]],
        skat: list[Card],
        log: bool = False,
    ):
        """
        Initialize a game.

        Args:
            rule_set: Ruleset to consider during the game.
            dealer_idx: Index of the player who deals the hands.
            hands: 3 hands of 10 cards, with the primary index corresponding to the player's index.
            skat: 2 cards to be buried in the Skat.
            log: Whether to log information about game state to stdout.

        Raises:
            InvalidGameStateError: If hands or skat or dealer_idx are incorrect.
        """
        self._rule_set = rule_set
        self._log = log

        self.phase: GamePhase = GamePhases.BID
        """Current game phase."""

        self.game_type: Optional[GameType] = None
        """Current game type."""

        if dealer_idx < 0 or dealer_idx > 2:
            raise InvalidGameStateError(
                f"dealer_id must be 0, 1 or 2, but is {dealer_idx}."
            )
        self._forehand: PlayerIdx = (dealer_idx + 1) % 3
        self._middlehand: PlayerIdx = (dealer_idx + 2) % 3
        self._backhand: PlayerIdx = dealer_idx
        self.active_player: PlayerIdx = self._middlehand
        """Currently active player."""

        if len(hands) != 3:
            raise InvalidGameStateError(
                f"hands must be length 3, but is length {len(hands)}."
            )
        elif len(hands[0]) != 10 or len(hands[1]) != 10 or len(hands[2]) != 10:
            raise InvalidGameStateError(
                "hands must contain 3 hands of 10 cards, but contains at least one hand with less or more than 10 cards."
            )
        self.hands = hands
        """List of player hands indexed with PlayerIdx."""

        if len(skat) != 2:
            raise InvalidGameStateError(
                f"skat must be length 2, but is length {len(skat)}."
            )
        self.skat = skat
        """List of two card Skat."""

        self.points: list[int] = [0, 0, 0]
        """Points achieved in won tricks."""

        self.current_trick = Trick()
        """Current trick."""

        self.trick_history: list[Trick] = []
        """List of all tricks in chronological order."""

        self.action_history: list[Action] = []
        """List of all actions in chronological order. Should not be directly modified, because apply_action and undo_action manage it."""

        self.undo_memory: list[dict[str, Any]] = []
        """
        Every action's apply method pushes a dictionary to this list with information about the previous state. This is in turn popped and used in the undo method.
        Index corresponds to action_history.
        """

        self.bid: Optional[int] = None
        """Highest bid yet."""

        self.hand_available = True
        """Has the player looked at the skat?"""

        # Allow rulesets with custom states to initialize it.
        self._rule_set.initialize_state(self)

    @classmethod
    def from_random_deal(
        cls, rule_set: AbstractRuleSet, dealer_idx: PlayerIdx, log: bool = False
    ) -> Self:
        """Creates a game with a randomized deck. See __init__ for docs."""
        deck = shuffle_deck(create_deck())
        hands = [deck[0:10], deck[10:20], deck[20:30]]
        skat = deck[30:32]

        return cls(rule_set, dealer_idx, hands, skat, log)

    def calculate_game_score(self) -> list[int]:
        """Wrapper for AbstractRuleSet.calculate_game_score."""
        return self._rule_set.calculate_game_score(self)

    def apply_action(self, action: Action, check_validity: bool = True) -> None:
        """
        Optionally check if action is valid, then call its apply method. Appends action to action_history.
        """
        if check_validity and not action.is_valid(self, self._rule_set):
            if self._log:
                print("Failed to apply action. Action is invalid.")
            raise InvalidActionError(f"Action {action} is not valid.")

        if self._log:
            print(f"Applying action: {action}")

        action.apply(self, self._rule_set)
        self.action_history.append(action)

    def undo_action(self) -> None:
        """
        Pops the last action from action_history and executes its undo method.

        Raises:
            InvalidGameStateError: If action_history contains no action to undo.
        """
        if not self.action_history:
            if self._log:
                print("No actions to undo.")
            raise InvalidGameStateError(
                "Cannot undo action, because no previous action exists."
            )

        action = self.action_history.pop()

        if self._log:
            print(f"Undoing action: {action}")

        action.undo(self)

    def get_valid_actions(self, player_idx: PlayerIdx) -> Iterator[Action]:
        """
        Wrapper for AbstractRuleSet.get_valid_actions.
        """
        return self._rule_set.get_valid_actions(self, player_idx)

    def get_player_position(self, player_idx: PlayerIdx) -> PlayerPosition:
        """
        Returns the PlayerPosition for a given player with player_idx.
        """
        if player_idx == self._forehand:
            return PlayerPosition.FOREHAND
        elif player_idx == self._middlehand:
            return PlayerPosition.MIDDLEHAND
        return PlayerPosition.BACKHAND
