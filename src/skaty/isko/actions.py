from dataclasses import dataclass

from skaty.cards import Card
from skaty.isko.state import ISkOGameState
from skaty.rules import AbstractRuleSet, Action, GameType


@dataclass(frozen=True)
class DeclareBid(Action[ISkOGameState]):
    """Declare bid value."""

    bid: int

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        state.undo_memory.append(
            {
                "active_player": state.active_player,
                "bid": state.bid,
                "bidding_phase": state.bidding_phase,
                "phase": state.phase,
                "declarer_idx": state.declarer_idx,
                "highest_bid": state.highest_bid,
                "last_bid": state.last_bid,
                "bid_before": state.bid_before[self.player_idx],
            }
        )

        rule_set.advance_state(state, self)

        # Advance state expects the state before the action.
        state.highest_bid = self.bid
        state.bid = self.bid
        state.last_bid = self
        state.bid_before[self.player_idx] = True

    def undo(self, state: ISkOGameState) -> None:
        memory = state.undo_memory.pop()

        state.bid = memory["bid"]
        state.active_player = memory["active_player"]
        state.bidding_phase = memory["bidding_phase"]
        state.phase = memory["phase"]
        state.declarer_idx = memory["declarer_idx"]
        state.highest_bid = memory["highest_bid"]
        state.last_bid = memory["last_bid"]
        state.bid_before[self.player_idx] = memory["bid_before"]


@dataclass(frozen=True)
class Listen(Action[ISkOGameState]):
    """Listen during bidding phase."""

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        state.undo_memory.append(
            {
                "active_player": state.active_player,
                "bidding_phase": state.bidding_phase,
                "phase": state.phase,
                "declarer_idx": state.declarer_idx,
                "last_bid": state.last_bid,
                "bid_before": state.bid_before[self.player_idx],
            }
        )

        state.last_bid = self
        state.bid_before[self.player_idx] = True

        # Advance state expects the state before the action.
        rule_set.advance_state(state, self)

    def undo(self, state: ISkOGameState) -> None:
        memory = state.undo_memory.pop()

        state.active_player = memory["active_player"]
        state.bidding_phase = memory["bidding_phase"]
        state.phase = memory["phase"]
        state.declarer_idx = memory["declarer_idx"]
        state.last_bid = memory["last_bid"]
        state.bid_before[self.player_idx] = memory["bid_before"]


@dataclass(frozen=True)
class Pass(Action[ISkOGameState]):
    """Pass during bidding phase."""

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        state.undo_memory.append(
            {
                "active_player": state.active_player,
                "bidding_phase": state.bidding_phase,
                "phase": state.phase,
                "declarer_idx": state.declarer_idx,
                "last_bid": state.last_bid,
                "passes": state.passes[self.player_idx],
            }
        )

        rule_set.advance_state(state, self)

        # Advance state expects the state before the action.
        state.last_bid = self
        state.passes[self.player_idx] = True

    def undo(self, state: ISkOGameState) -> None:
        memory = state.undo_memory.pop()

        state.active_player = memory["active_player"]
        state.bidding_phase = memory["bidding_phase"]
        state.phase = memory["phase"]
        state.declarer_idx = memory["declarer_idx"]
        state.last_bid = memory["last_bid"]
        state.passes[self.player_idx] = memory["passes"]


@dataclass(frozen=True)
class DrawSkat(Action[ISkOGameState]):
    """Draw Skat into players hand, removing hand multiplier."""

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        state.undo_memory.append(
            {
                "skat": state.skat.copy(),
                "hand": state.hands[state.active_player].copy(),
                "hand_available": state.hand_available,
            }
        )

        state.hands[state.active_player] += state.skat
        state.skat = []
        state.hand_available = False

    def undo(self, state: ISkOGameState) -> None:
        memory = state.undo_memory.pop()

        state.skat = memory["skat"]
        state.hands[state.active_player] = memory["hand"]
        state.hand_available = memory["hand_available"]


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class DeclareGame(Action[ISkOGameState]):
    """Declare specific game. Hand is applied automatically dependent on the game state."""

    game_type: GameType
    schneider: bool = False
    schwarz: bool = False
    open: bool = False

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        state.undo_memory.append(
            {
                "active_player": state.active_player,
                "phase": state.phase,
                "declaration": state.declaration,
                "game_type": state.game_type,
                "tops": state.tops,
            }
        )

        rule_set.advance_state(state, self)

    def undo(self, state: ISkOGameState) -> None:
        memory = state.undo_memory.pop()

        state.phase = memory["phase"]
        state.declaration = memory["declaration"]
        state.active_player = memory["active_player"]
        state.game_type = memory["game_type"]
        state.tops = memory["tops"]


@dataclass(frozen=True)
class PlayCard(Action[ISkOGameState]):
    """Play specific card."""

    card: Card

    def apply(
        self, state: ISkOGameState, rule_set: AbstractRuleSet[ISkOGameState]
    ) -> None:
        trick_finishes = len(state.current_trick.cards) == 2

        state.undo_memory.append(
            {
                "active_player": state.active_player,
                "points": state.points.copy(),
                "trick_finishes": trick_finishes,
                "phase": state.phase,
                "tricks_won": state.tricks_won.copy(),
            }
        )
        state.hands[self.player_idx].remove(self.card)

        rule_set.advance_state(state, self)

    def undo(self, state: ISkOGameState) -> None:
        memory = state.undo_memory.pop()

        state.hands[self.player_idx].append(self.card)
        state.active_player = memory["active_player"]
        state.points = memory["points"]
        state.phase = memory["phase"]
        state.tricks_won = memory["tricks_won"]

        if memory["trick_finishes"]:
            state.current_trick = state.trick_history.pop()

        state.current_trick.pop()
