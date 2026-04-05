from copy import deepcopy
from dataclasses import dataclass

from skaty.cards import Card
from skaty.isko.state import ISkOGameState
from skaty.rules import AbstractRuleSet, Action, GameType


@dataclass
class DeclareBid(Action[ISkOGameState]):
    """Declare bid value."""

    bid: int

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bid": state.bid,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
            "highest_bid": state.highest_bid,
            "last_bid": state.last_bid,
            "bid_before": state.bid_before[self.player_idx],
        }

        rule_set.advance_state(state, self)

        # Advance state expects the state before the action.
        state.highest_bid = self.bid
        state.bid = self.bid
        state.last_bid = self
        state.bid_before[self.player_idx] = True

    def undo(self, state: ISkOGameState) -> None:
        state.bid = self._memory["bid"]
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]
        state.highest_bid = self._memory["highest_bid"]
        state.last_bid = self._memory["last_bid"]
        state.bid_before[self.player_idx] = self._memory["bid_before"]


@dataclass
class Listen(Action[ISkOGameState]):
    """Listen during bidding phase."""

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
            "last_bid": state.last_bid,
            "bid_before": state.bid_before[self.player_idx],
        }

        state.last_bid = self
        state.bid_before[self.player_idx] = True

        # Advance state expects the state before the action.
        rule_set.advance_state(state, self)

    def undo(self, state: ISkOGameState) -> None:
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]
        state.last_bid = self._memory["last_bid"]
        state.bid_before[self.player_idx] = self._memory["bid_before"]


@dataclass
class Pass(Action[ISkOGameState]):
    """Pass during bidding phase."""

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        self._memory = {
            "active_player": state.active_player,
            "bidding_phase": state.bidding_phase,
            "phase": state.phase,
            "declarer_idx": state.declarer_idx,
            "last_bid": state.last_bid,
            "passes": state.passes[self.player_idx],
        }

        rule_set.advance_state(state, self)

        # Advance state expects the state before the action.
        state.last_bid = self
        state.passes[self.player_idx] = True

    def undo(self, state: ISkOGameState) -> None:
        state.active_player = self._memory["active_player"]
        state.bidding_phase = self._memory["bidding_phase"]
        state.phase = self._memory["phase"]
        state.declarer_idx = self._memory["declarer_idx"]
        state.last_bid = self._memory["last_bid"]
        state.passes[self.player_idx] = self._memory["passes"]


@dataclass
class DrawSkat(Action[ISkOGameState]):
    """Draw Skat into players hand, removing hand multiplier."""

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        self._memory = {
            "skat": state.skat.copy(),
            "hand": state.hands[state.active_player].copy(),
            "hand_available": state.hand_available,
        }

        state.hands[state.active_player] += state.skat
        state.skat = []
        state.hand_available = False

    def undo(self, state: ISkOGameState) -> None:
        state.skat = self._memory["skat"]
        state.hands[state.active_player] = self._memory["hand"]
        state.hand_available = self._memory["hand_available"]


@dataclass
class BurySkat(Action[ISkOGameState]):
    """Bury cards from hand into the Skat."""

    cards: tuple[Card, Card]

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        state.skat = list(self.cards)
        state.hands[state.active_player].remove(self.cards[0])
        state.hands[state.active_player].remove(self.cards[1])

    def undo(self, state: ISkOGameState) -> None:
        state.skat = []
        state.hands[state.active_player] += list(self.cards)


@dataclass
class DeclareGame(Action[ISkOGameState]):
    """Declare specific game. Hand is applied automatically dependent on the game state."""

    game_type: GameType
    schneider: bool = False
    schwarz: bool = False
    open: bool = False

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        self._memory = {
            "active_player": state.active_player,
            "phase": state.phase,
            "declaration": state.declaration,
            "game_type": state.game_type,
            "tops": state.tops,
        }

        rule_set.advance_state(state, self)

    def undo(self, state: ISkOGameState) -> None:
        state.phase = self._memory["phase"]
        state.declaration = self._memory["declaration"]
        state.active_player = self._memory["active_player"]
        state.game_type = self._memory["game_type"]
        state.tops = self._memory["tops"]


@dataclass
class PlayCard(Action[ISkOGameState]):
    """Play specific card."""

    card: Card

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        trick_finishes = len(state.current_trick.cards) == 2

        self._memory = {
            "active_player": state.active_player,
            "points": state.points.copy(),
            "trick_finishes": trick_finishes,
            "phase": state.phase,
        }
        state.hands[self.player_idx].remove(self.card)

        rule_set.advance_state(state, self)

    def undo(self, state: ISkOGameState) -> None:
        state.hands[self.player_idx].append(self.card)
        state.active_player = self._memory["active_player"]
        state.points = self._memory["points"]
        state.phase = self._memory["phase"]

        if self._memory["trick_finishes"]:
            state.current_trick = state.trick_history.pop()

        state.current_trick.pop()
