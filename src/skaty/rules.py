from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Generator, Optional
from typing import TYPE_CHECKING


# Import in this condition to avoid circular imports.
if TYPE_CHECKING:
    from skaty.actions import Action, PlayerIdx
    from skaty.game_state import GameState

from skaty.cards import Card, Suit


class GamePhase(Enum):
    BID = "BID"
    PASSED = "PASSED"
    DECLARATION = "DECLARATION"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"


class PlayerPosition(IntEnum):
    """
    Position during bidding or while playing.
    """

    FOREHAND = 0
    MIDDLEHAND = 1
    BACKHAND = 2


class BiddingPhase(IntEnum):
    """
    Phase in the bidding process.
    """

    ForehandMiddlehand = 0
    ForehandBackhand = 1
    MiddlehandBackhand = 2


class GameType(IntEnum):
    """
    Basic values for suit, grand and null games according to ISkO 2.4.1, 2.4.2. Null {hand|ouvert} are respected in the rule sets calculate_game_score method.
    """

    PASS = 0  # used in case a game is passed during bidding
    DIAMONDS = 9
    HEARTS = 10
    SPADES = 11
    CLUBS = 12
    NULL = 23
    GRAND = 24


@dataclass
class GameDeclaration:
    game_type: GameType
    hand: bool = False
    schneider: bool = False
    schwarz: bool = False
    open: bool = False


class AbstractRuleSet(ABC):
    @abstractmethod
    def determine_trick_winner(self, trick: list[Card], game_type: GameType) -> int:
        pass

    @abstractmethod
    def calculate_game_score(self, state: GameState) -> list[int]:
        """
        Attempt to calculate the game score in state.
        Returns a list with points (positive or negative) for each player with indexes corresponding to the state's players.

        Raises:
            InvalidGameStateError: If there is no game score in the current state.
        """
        pass

    @abstractmethod
    def is_valid_action(self, state: GameState, action: Action) -> bool:
        """Checks if an action is valid in the current state."""
        pass

    @abstractmethod
    def get_valid_actions(
        self, state: GameState, player_idx: PlayerIdx
    ) -> Generator["Action", None, None]:
        """Yields all valid actions the player can take in state."""
        pass

    @abstractmethod
    def advance_state(self, state: GameState, action: Action) -> None:
        """Gets called, after action is applied on state. The rule set could for example change phases or the active player."""
        pass
