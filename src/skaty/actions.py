from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal
from copy import deepcopy

from skaty.cards import Card
from skaty.rules import AbstractRuleSet, GameType

if TYPE_CHECKING:
    from skaty.game_state import GameState

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


@dataclass
class Action:
    @property
    def type(self) -> ActionType:
        return ActionType[self.__class__.__name__.upper()]

    player_idx: PlayerIdx
    _memory: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def is_valid(self, state: GameState, rule_set: AbstractRuleSet) -> bool:
        return rule_set.is_valid_action(state, self)

    @abstractmethod
    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        """Mutate state dependent on action type, state and rules."""
        pass

    @abstractmethod
    def undo(self, state: GameState) -> None:
        """Reverse to state before action was applied. Restores state exactly."""
        pass


@dataclass
class DeclareBid(Action):
    """Declare bid value."""

    bid: int

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bid": state.bid,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
        }
        state.bid = self.bid
        rule_set.advance_state(state, self)

    def undo(self, state: GameState) -> None:
        state.bid = self._memory["bid"]
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]


@dataclass
class Listen(Action):
    """Listen during bidding phase."""

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
        }
        rule_set.advance_state(state, self)

    def undo(self, state: GameState) -> None:
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]


@dataclass
class Pass(Action):
    """Pass during bidding phase."""

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
        }
        rule_set.advance_state(state, self)

    def undo(self, state: GameState) -> None:
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]


@dataclass
class DrawSkat(Action):
    """Draw Skat into players hand, removing hand multiplier."""

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        self._memory = {
            "skat": state.skat.copy(),
            "hand": state.hands[state.active_player].copy(),
            "hand_available": state.hand_available,
        }

        state.hands[state.active_player] += state.skat
        state.skat = []
        state.hand_available = False

    def undo(self, state: GameState) -> None:
        state.skat = self._memory["skat"]
        state.hands[state.active_player] = self._memory["hand"]
        state.hand_available = self._memory["hand_available"]


@dataclass
class BurySkat(Action):
    """Bury cards from hand into the Skat."""

    cards: tuple[Card, Card]

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        state.skat = list(self.cards)
        state.hands[state.active_player].remove(self.cards[0])
        state.hands[state.active_player].remove(self.cards[1])

    def undo(self, state: GameState) -> None:
        state.skat = []
        state.hands[state.active_player] += list(self.cards)


@dataclass
class DeclareGame(Action):
    """Declare specific game. Hand is applied automatically dependent on the game state."""

    game_type: GameType
    schneider: bool = False
    schwarz: bool = False
    open: bool = False

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "phase": state.phase,
            "declaration": state.declaration,
            "game_type": state.game_type,
            "tops": state.tops,
        }

        rule_set.advance_state(state, self)

    def undo(self, state: GameState) -> None:
        state.phase = self._memory["phase"]
        state.declaration = self._memory["declaration"]
        state.active_player = self._memory["active_player"]
        state.game_type = self._memory["game_type"]
        state.tops = self._memory["tops"]


@dataclass
class PlayCard(Action):
    """Play specific card."""

    card: Card

    def apply(self, state: GameState, rule_set: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "points": state.points.copy(),
            "current_trick": deepcopy(state.current_trick),
            "trick_history": state.trick_history.copy(),
            "phase": state.phase,
        }
        state.hands[self.player_idx].remove(self.card)

        rule_set.advance_state(state, self)

    def undo(self, state: GameState) -> None:
        state.hands[self.player_idx].append(self.card)
        state.active_player = self._memory["active_player"]
        state.points = self._memory["points"]
        state.current_trick = self._memory["current_trick"]
        state.trick_history = self._memory["trick_history"]
        state.phase = self._memory["phase"]
