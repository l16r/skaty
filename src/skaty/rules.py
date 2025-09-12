from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional

from skaty.cards import Card, Suit
from skaty.player import Player


class Action(Enum):
    """
    All possible actions. The legality of the actions is decided according to the rule set.
    """

    PLAY_CARD = auto()
    DRAW_SKAT = auto()
    BURY_SKAT = auto()
    DECLARE_BID = auto()
    LISTEN = auto()
    PASS = auto()
    DECLARE_GAME = auto()
    GIVE_UP = auto()


class GameType(Enum):
    """
    Basic values for suit, grand and null games according to ISkO 2.4.1, 2.4.2. Null {hand|ouvert} are respected in the rule sets calculate_game_score method.
    """

    PASS = 0
    DIAMONDS = 9
    HEARTS = 10
    SPADES = 11
    CLUBS = 12
    NULL = 23
    GRAND = 24


class AbstractRuleSet(ABC):
    @abstractmethod
    def game_type() -> GameType:
        pass

    @abstractmethod
    def trump_suit() -> Optional[Suit]:
        pass

    @abstractmethod
    def is_card_trump(self, card: Card) -> bool:
        pass

    @abstractmethod
    def get_card_effective_rank_value(self, card: Card) -> int:
        pass

    @abstractmethod
    def determine_trick_winner(self, trick: list[tuple[Card, Player]]) -> int:
        pass

    @abstractmethod
    def calculate_game_score(self) -> int:
        pass

    @abstractmethod
    def isValidAction(self, player: Player, action: Action) -> bool:
        pass

    @abstractmethod
    def isValidBid(self, player: Player, action: Action, bid: int) -> bool:
        pass

    @abstractmethod
    def isValidCardPlay(self, player: Player, card: Card) -> bool:
        pass

    @abstractmethod
    def isValidGameDeclaration(
        self,
        player: Player,
        action: Action,
        bid: int,
        game_type: GameType,
        hand: bool,
        schneider: bool = False,
        schwarz: bool = False,
        open: bool = False,
    ) -> bool:
        pass
