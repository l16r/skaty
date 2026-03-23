from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from skaty.cards import Card
from skaty.rules import AbstractRuleSet, GameDeclaration, GamePhase, GameType

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
    GIVE_UP = "GIVE_UP"


@dataclass
class Action:
    @property
    def type(self) -> ActionType:
        return ActionType[self.__class__.__name__.upper()]

    player_idx: PlayerIdx
    _memory: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        # Actions are only legal for the currently active player
        if self.player_idx != state.active_player:
            return False
        # Actions are only allowed in some phases
        if not ruleset.is_valid_action_during_phase(self, state.phase):
            return False
        return True

    @abstractmethod
    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
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

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
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
class DrawSkat(Action):
    """Draw Skat into players hand, removing hand multiplier."""

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
            return False

        return len(state.skat) == 2

    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
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

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
            return False

        if len(state.skat) != 0:
            return False

        hand = state.hands[state.active_player]
        # Cannot bury card not in hand
        if self.cards[0] not in hand or self.cards[1] not in hand:
            return False
        # Cannot bury same card twice
        if self.cards[0] == self.cards[1]:
            return False

        return True

    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
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

    def is_valid(self, state: GameState, ruleset: AbstractRuleSet) -> bool:
        if not super().is_valid(state, ruleset):
            return False

        # Only the declarer can declare a game
        if self.player_idx != state.declarer_idx:
            return False

        return ruleset.is_valid_game_declaration(
            state,
            GameDeclaration(
                game_type=self.game_type,
                hand=state.hand_available,
                schneider=self.schneider,
                schwarz=self.schwarz,
                open=self.open,
            ),
        )

    def apply(self, state: GameState, ruleset: AbstractRuleSet) -> None:
        self._memory = {
            "active_player": state.active_player,
            "phase": state.phase,
            "declaration": state.declaration,
            "game_type": state.game_type,
        }

        state.phase = GamePhase.PLAYING
        state.declaration = GameDeclaration(
            game_type=self.game_type,
            hand=state.hand_available,
            schneider=self.schneider,
            schwarz=self.schwarz,
            open=self.open,
        )
        state.active_player = state._forehand
        state.game_type = self.game_type

    def undo(self, state: GameState) -> None:
        state.phase = self._memory["phase"]
        state.declaration = self._memory["declaration"]
        state.active_player = self._memory["active_player"]
        state.game_type = self._memory["game_type"]


@dataclass
class PlayCard(Action):
    """Play specific card."""

    card: Card


@dataclass
class GiveUp(Action):
    """Give up."""

    pass
