from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Optional

from skaty.game_state import GameState
from skaty.rules import GameType, GameTypes

if TYPE_CHECKING:
    from skaty.isko.actions import DeclareBid, Listen, Pass


class BiddingPhase(IntEnum):
    """
    Phase in the bidding process.
    """

    ForehandMiddlehand = 0
    ForehandBackhand = 1
    MiddlehandBackhand = 2


class ISkOGameTypes(GameTypes):
    DIAMONDS = GameType("isko:diamonds")
    HEARTS = GameType("isko:hearts")
    SPADES = GameType("isko:spades")
    CLUBS = GameType("isko:clubs")
    NULL = GameType("isko:null")
    GRAND = GameType("isko:grand")


@dataclass
class GameDeclaration:
    game_type: GameType
    hand: bool = False
    schneider: bool = False
    schwarz: bool = False
    open: bool = False


class ISkOGameState(GameState):
    __slots__ = (
        "bidding_phase",
        "declaration",
        "highest_bid",
        "last_bid",
        "bid_before",
        "passes",
    )

    bidding_phase: BiddingPhase
    declaration: Optional[GameDeclaration]
    highest_bid: int
    last_bid: Optional[DeclareBid | Listen | Pass]
    bid_before: list[bool]
    passes: list[bool]
