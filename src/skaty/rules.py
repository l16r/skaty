from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Generator, Generic, Literal, NewType, TypeVar

from skaty.cards import Card

if TYPE_CHECKING:
    from skaty.game_state import GameState

TState = TypeVar("TState", bound="GameState")

type PlayerIdx = Literal[0, 1, 2]


class PlayerPosition(IntEnum):
    """
    Position during bidding or while playing.
    """

    FOREHAND = 0
    MIDDLEHAND = 1
    BACKHAND = 2


GamePhase = NewType("GamePhase", str)


class GamePhases:
    BID = GamePhase("core:BID")
    PASSED = GamePhase("core:PASSED")
    DECLARATION = GamePhase("core:DECLARATION")
    PLAYING = GamePhase("core:PLAYING")
    GAME_OVER = GamePhase("core:GAME_OVER")


GameType = NewType("GameType", str)


class GameTypes:
    PASS = GameType("core:pass")  # used in case a game is passed during bidding


@dataclass
class Action(ABC, Generic[TState]):
    player_idx: PlayerIdx
    _memory: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def is_valid(self, state: TState, rule_set: "AbstractRuleSet[TState]") -> bool:
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
    @abstractmethod
    def initialize_state(self, state: TState) -> None:
        """
        Hook to initialize rule-specific variables in state.
        """
        pass

    @abstractmethod
    def determine_trick_winner(self, trick: list[Card], game_type: GameType) -> int:
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
        """Gets called, after action is applied on state. The rule set could for example change phases or the active player."""
        pass
