from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Generator, Generic, Literal, NewType, TypeVar

from skaty.cards import Card

if TYPE_CHECKING:
    from skaty.game_state import GameState

TState = TypeVar("TState", bound="GameState")
"""Any GameState."""

type PlayerIdx = Literal[0, 1, 2]
"""Number to uniquely identify player in a single game."""


class PlayerPosition(IntEnum):
    """
    Position during bidding or while playing.
    """

    FOREHAND = 0
    MIDDLEHAND = 1
    BACKHAND = 2


GamePhase = NewType("GamePhase", str)
"""Differentiate between GamePhases and strings for type checking. GamePhase should have form scope + ':' + IDENTIFIER (e.g. 'core:BID')."""


class GamePhases:
    BID = GamePhase("core:BID")
    """Bidding phase."""

    DECLARATION = GamePhase("core:DECLARATION")
    """Waiting for a player to declare or use Skat."""

    PLAYING = GamePhase("core:PLAYING")
    """Playing cards in tricks."""

    GAME_OVER = GamePhase("core:GAME_OVER")
    """Game over."""


GameType = NewType("GameType", str)
"""Differentiate between GameTypes and strings for type checking. GameType should have form scope + ':' + IDENTIFIER (e.g. 'core:PASS')"""


class GameTypes:
    PASS = GameType("core:PASS")
    """Used if a game is passed during bidding."""


@dataclass(frozen=True)
class Action(ABC, Generic[TState]):
    """
    Base class for any action.
    """

    player_idx: PlayerIdx
    """Player taking the action."""

    def is_valid(self, state: TState, rule_set: "AbstractRuleSet[TState]") -> bool:
        """Wrapper for rule_set.is_valid_action(state,self)."""
        return rule_set.is_valid_action(state, self)

    @abstractmethod
    def apply(self, state: TState, rule_set: "AbstractRuleSet[TState]") -> None:
        """Mutate state dependent on action type, state and rules."""
        pass

    @abstractmethod
    def undo(self, state: TState) -> None:
        """Reverse to state before action was applied. Restores state exactly."""
        pass


class AbstractRuleSet(ABC, Generic[TState]):
    """
    Base class for every rule set over a given type of state.
    The rule set itself is stateless. All state belongs to TState.
    """

    @abstractmethod
    def initialize_state(self, state: TState) -> None:
        """
        Hook to initialize rule-specific attributes in state.
        """
        pass

    @abstractmethod
    def determine_trick_winner(self, trick: list[Card], game_type: GameType) -> int:
        """
        Calculates index of winning player.

        Args:
            trick: Cards played in order of the trick.
            game_type: Game type used for trick.

        Returns:
            (PlayerIdx): Of the winning player

        Raises:
            TrickNotFinishedError: If trick is not finished.
            InvalidGameTypeError: If game type does not allow for tricks.
        """
        pass

    @abstractmethod
    def calculate_game_score(self, state: TState) -> list[int]:
        """
        Attempt to calculate the game score in state.
        Returns a list with points (positive or negative) for each player with indexes corresponding to the state's players.

        Raises:
            InvalidGameStateError: If there is no game score in the current state.
        """
        pass

    @abstractmethod
    def is_valid_action(self, state: TState, action: Action) -> bool:
        """Checks if an action is valid in the current state."""
        pass

    @abstractmethod
    def get_valid_actions(
        self, state: TState, player_idx: PlayerIdx
    ) -> Generator["Action", None, None]:
        """Yields all valid actions the player can take in state."""
        pass

    @abstractmethod
    def advance_state(self, state: TState, action: Action) -> None:
        """Hook for rule set to change state after an action is applied (e.g. change bidding phase)."""
        pass
