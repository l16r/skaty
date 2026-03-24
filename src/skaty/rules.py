from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Optional
from typing import TYPE_CHECKING


# Import in this condition to avoid circular imports.
if TYPE_CHECKING:
    from skaty.trick import Trick
    from skaty.actions import Action, DeclareBid, Listen, Pass, PlayCard
    from skaty.game_state import GameState

from skaty.cards import Card, Suit
from skaty.player import Player


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
    def trump_suit(self, game_type: GameType) -> Optional[Suit]:
        pass

    @abstractmethod
    def is_card_trump(self, card: Card, game_type: GameType) -> bool:
        pass

    @abstractmethod
    def tops(self, cards: list[Card], game_type: GameType) -> int:
        pass

    @abstractmethod
    def get_card_effective_rank_value(self, card: Card, game_type: GameType) -> int:
        pass

    @abstractmethod
    def determine_trick_winner(self, trick: list[Card], game_type: GameType) -> int:
        pass

    @abstractmethod
    def calculate_game_score(
        self,
        players: list[Player],
        declarer: int,
        points: dict[Player, int],
        tricks: list[tuple[Trick, Player]],
        game_type: GameType,
        bid: int,
        skat: tuple[Card, Card],
        hand: bool = False,
        schneider_announced: bool = False,
        schwarz_announced: bool = False,
        ouvert: bool = False,
    ) -> int:
        pass

    @abstractmethod
    def is_valid_action_during_phase(
        self,
        action: Action,
        phase: GamePhase,
    ) -> bool:
        pass

    @abstractmethod
    def get_action_types_for_phase(self, phase: GamePhase) -> list[type[Action]]:
        pass

    @abstractmethod
    def get_next_valid_bid(self, current_bid: Optional[int]) -> int:
        pass

    @abstractmethod
    def is_valid_bid(
        self,
        state: GameState,
        bid: DeclareBid | Listen | Pass,
    ) -> bool:
        pass

    @abstractmethod
    def is_valid_card_play(
        self,
        hand: list[Card],
        card: Card,
        first_card: Optional[Card],
        game_type: GameType,
    ) -> bool:
        pass

    @abstractmethod
    def is_valid_game_declaration(
        self, state: GameState, declaration: GameDeclaration
    ) -> bool:
        pass

    @abstractmethod
    def get_valid_actions(self, state: GameState, player_idx: int) -> list["Action"]:
        pass

    @abstractmethod
    def advance_bidding(
        self, state: GameState, action: DeclareBid | Listen | Pass
    ) -> None:
        """
        Mutate the state in bidding dependent on action.
        """

    @abstractmethod
    def advance_playing(self, state: GameState, action: PlayCard) -> None:
        """
        Mutate the state as card is played.
        """
