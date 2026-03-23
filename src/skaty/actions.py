from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from skaty.cards import Card
from skaty.rules import AbstractRuleSet, GameType

if TYPE_CHECKING:
    from skaty.game_state import GameState
    from skaty.rules import AbstractRuleSet

type PlayerIdx = Literal[0, 1, 2]


class ActionType(Enum):
    """
    All possible actions. The legality of the actions is decided according to the rule set.
    """

    PLAY_CARD = "PLAY_CARD"
    DRAW_SKAT = "DRAW_SKAT"
    BURY_SKAT = "BURY_SKAT"
    DECLARE_BID = "DECLARE_BID"
    LISTEN = "LISTEN"
    PASS = "PASS"
    DECLARE_GAME = "DECLARE_GAME"
    GIVE_UP = "GIVE_UP"


@dataclass
class Action:
    @property
    def type(self) -> ActionType:
        return ActionType[self.__class__.__name__.upper()]

    player_idx: PlayerIdx
    _memory: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    @abstractmethod
    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        # Actions are only legal for the currently active player
        return self.player_idx == state.active_player

    @abstractmethod
    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
        """Mutate state dependent on action type, state and rules."""
        pass

    @abstractmethod
    def undo(self, state: GameState) -> None:
        """Reverse to state before action was applied. Restores state exactly."""
        pass


@dataclass
class PlayCard(Action):
    """Play specific card."""

    card: Card


@dataclass
class DrawSkat(Action):
    """Draw Skat, removing hand, Schneider and Schneider Schwarz (announced) and open as winning options (ISkO 2.5.1)."""

    pass


@dataclass
class BurySkat(Action):
    """Bury cards from hand into the Skat."""

    cards: tuple[Card, Card]


@dataclass
class DeclareBid(Action):
    """Declare bid value."""

    bid: int

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
            return False
        elif not ruleset.is_valid_action_during_phase(self, state.phase):
            return False
        return ruleset.is_valid_bid(state, self)

    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bid": state.bid,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
        }
        state.bid = self.bid
        ruleset.advance_bidding(state, self)

    def undo(self, state: GameState) -> None:
        state.bid = self._memory["bid"]
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]


@dataclass
class Listen(Action):
    """Listen during bidding phase."""

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
            return False
        if not ruleset.is_valid_action_during_phase(self, state.phase):
            return False
        return ruleset.is_valid_bid(state, self)

    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
        }
        ruleset.advance_bidding(state, self)

    def undo(self, state: GameState) -> None:
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]


@dataclass
class Pass(Action):
    """Pass during bidding phase."""

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
            return False
        if not ruleset.is_valid_action_during_phase(self, state.phase):
            return False
        return ruleset.is_valid_bid(state, self)

    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
        }
        ruleset.advance_bidding(state, self)

    def undo(self, state: GameState) -> None:
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]


@dataclass
class DeclareGame(Action):
    """Declare specific game"""

    game_type: GameType
    hand: bool = False
    schneider: bool = False
    schwarz: bool = False
    open: bool = False


@dataclass
class GiveUp(Action):
    """Give up."""

    pass
