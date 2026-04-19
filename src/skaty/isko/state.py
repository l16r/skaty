from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Optional, TypeVar

from skaty.game_state import GameState
from skaty.rules import GameType, GameTypes, PlayerIdx

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
    """Extending GameTypes with ISkO game types."""

    DIAMONDS = GameType("isko:diamonds")
    """DIAMONDS"""
    HEARTS = GameType("isko:hearts")
    """HEARTS"""
    SPADES = GameType("isko:spades")
    """SPADES"""
    CLUBS = GameType("isko:clubs")
    """CLUBS"""
    NULL = GameType("isko:null")
    """NULL"""
    GRAND = GameType("isko:grand")
    """GRAND"""


@dataclass
class GameDeclaration:
    """Everything an ISkO game declaration can contain."""

    game_type: GameType
    """Game type to be played."""
    hand: bool = False
    """Has the declarer looked at the Skat?"""
    schneider: bool = False
    """Has the declarer announced Schneider?"""
    schwarz: bool = False
    """Has the declarer announced Schwarz?"""
    open: bool = False
    """Has the declarer announced open? In case of Null game equivalent to ouvert."""


class ISkOGameState(GameState):
    """
    Extending GameState with attributes for ISkO rules.
    """

    __slots__ = (
        "tops",
        "bidding_phase",
        "declarer_idx",
        "declaration",
        "last_bid",
        "bid_before",
        "passes",
        "tricks_won",
    )

    tops: Optional[int]
    """Tops in declarers hand and the start of game."""
    bidding_phase: BiddingPhase
    """Current bidding phase."""
    declarer_idx: Optional[PlayerIdx]
    """PlayerIdx of the declarer."""
    declaration: Optional[GameDeclaration]
    """Declaration made by declarer."""
    last_bid: Optional[DeclareBid | Listen | Pass]
    """Last bid action to happen."""
    bid_before: list[bool]
    """Has the player with player_idx asserted a positive bid (DeclareBid or Listen) before?"""
    passes: list[bool]
    """Has the player with player_idx asserted a negative bid/Pass before?"""
    tricks_won: list[int]
    """Tricks won by player with player_idx"""


T_ISkOGameState = TypeVar("T_ISkOGameState", bound=ISkOGameState)
"""Any GameState based on ISkOGameState."""
