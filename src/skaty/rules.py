from abc import ABC, abstractmethod
from enum import Enum, IntEnum
from typing import Optional
from dataclasses import dataclass
from typing import TYPE_CHECKING

# We only need Trick for typing. Import in this condition to avoid circular imports.
if TYPE_CHECKING:
    from skaty.trick import Trick

from skaty.cards import Card, Suit
from skaty.player import Player


class GamePhase(Enum):
    PRE_DEAL = "PRE_DEAL"
    BID = "BID"
    PASSED = "PASSED"
    DECLARATION = "DECLARATION"
    PLAYING = "PLAYING"
    LOST = "LOST"
    WON = "WON"


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


class ActionType(Enum):
    """
    All possible actions. The legality of the actions is decided according to the rule set.
    """

    DEAL_CARDS = "DEAL_CARDS"
    PLAY_CARD = "PLAY_CARD"
    DRAW_SKAT = "DRAW_SKAT"
    BURY_SKAT = "BURY_SKAT"
    DECLARE_BID = "DECLARE_BID"
    LISTEN = "LISTEN"
    PASS = "PASS"
    DECLARE_GAME = "DECLARE_GAME"
    GIVE_UP = "GIVE_UP"


@dataclass(frozen=True)
class Action:
    @property
    def type(self) -> ActionType:
        return ActionType[self.__class__.__name__.upper()]


@dataclass(frozen=True)
class DealCards(Action):
    """Deal cards."""

    pass


@dataclass(frozen=True)
class PlayCard(Action):
    """Play specific card."""

    card: Card


@dataclass(frozen=True)
class DrawSkat(Action):
    """Draw Skat, removing hand, Schneider and Schneider Schwarz (announced) and open as winning options (ISkO 2.5.1)."""

    pass


@dataclass(frozen=True)
class BurySkat(Action):
    """Bury cards from hand into the Skat."""

    cards: tuple[Card, Card]


@dataclass(frozen=True)
class DeclareBid(Action):
    """Declare bid value."""

    bid: int


@dataclass(frozen=True)
class Listen(Action):
    """Listen during bidding phase."""

    pass


@dataclass(frozen=True)
class Pass(Action):
    """Pass in bidding or game declaration."""

    pass


@dataclass(frozen=True)
class DeclareGame(Action):
    """Declare specific game"""

    game_type: GameType
    # Hand is always implied by drawing or not drawing the Skat.
    schneider: bool = False
    schwarz: bool = False
    open: bool = False


@dataclass(frozen=True)
class GiveUp(Action):
    """Give up."""

    pass


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
    def is_valid_action(
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
        player: Player,
        bid: DeclareBid | Listen | Pass,
        previous_bids: list[tuple[Player, DeclareBid | Listen | Pass]],
        player_pos: PlayerPosition,
        bidding_phase: BiddingPhase,
    ) -> bool:
        pass

    @abstractmethod
    def is_valid_card_play(
        self,
        player: Player,
        card: Card,
        first_card: Optional[Card],
        game_type: GameType,
    ) -> bool:
        pass

    @abstractmethod
    def is_valid_game_declaration(
        self,
        player: Player,
        skat: tuple[Card, Card],
        bid: int,
        game_type: GameType,
        hand: bool,
        schneider: bool,
        schwarz: bool,
        open: bool,
    ) -> bool:
        pass
