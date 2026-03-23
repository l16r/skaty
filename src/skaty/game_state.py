from typing import Optional

from skaty.actions import Action, DeclareBid, Listen, Pass, PlayerIdx
from skaty.cards import Card, create_deck, shuffle_deck
from skaty.exceptions import (
    InvalidGameStateError,
)
from skaty.rules import (
    AbstractRuleSet,
    BiddingPhase,
    GamePhase,
    GameType,
    PlayerPosition,
    GameDeclaration,
)
from skaty.trick import Trick


class GameState:
    def __init__(
        self,
        rule_set: AbstractRuleSet,
        dealer_idx: PlayerIdx,
        hands: list[list[Card]],
        skat: list[Card],
        log: bool = False,
    ):
        """
        Initialize a game.

        Args:
            rule_set: Ruleset to consider during the game.
            dealer_idx: Index of the player who deals the hands.
            hands: 3 hands of 10 cards.
            skat: 2 cards.
            log: Log information about game state to stdout.

        Raises:
            InvalidGameStateError: If hands or skat or dealer_id are incorrect.
        """
        self._rule_set = rule_set
        self._log = log
        self.phase: GamePhase = GamePhase.BID
        self.game_type: GameType = GameType.PASS

        if dealer_idx < 0 or dealer_idx > 2:
            raise InvalidGameStateError(
                f"dealer_id must be 0, 1 or 2, but is {dealer_idx}."
            )
        self._forehand: PlayerIdx = (dealer_idx + 1) % 3
        self._middlehand: PlayerIdx = (dealer_idx + 2) % 3
        self._backhand: PlayerIdx = dealer_idx
        self.active_player = self._middlehand

        if len(hands) != 3:
            raise InvalidGameStateError(
                f"hands must be length 3, but is length {len(hands)}."
            )
        elif len(hands[0]) != 10 or len(hands[1]) != 10 or len(hands[2]) != 10:
            raise InvalidGameStateError(
                "hands must contain 3 hands of 10 cards, but contains at least one hand with less or more than 10 cards."
            )
        self.hands = hands

        if len(skat) != 2:
            raise InvalidGameStateError(
                f"skat must be length 2, but is length {len(skat)}."
            )
        self.skat = skat

        self.points: list[int] = [0, 0, 0]

        self.current_trick = Trick()
        self.trick_history: list[Trick] = []
        self.action_history: list[Action] = []

        self.bid: Optional[int] = None
        self.bidding_phase: BiddingPhase = BiddingPhase.ForehandMiddlehand

        self.hand_available = True
        self.declarer_idx: Optional[PlayerIdx] = None
        self.declaration: Optional[GameDeclaration] = None

    @classmethod
    def from_random_deal(
        cls, rule_set: AbstractRuleSet, dealer_idx: PlayerIdx, log: bool = False
    ) -> "GameState":
        """Creates a game with a randomized deck."""
        deck = shuffle_deck(create_deck())
        hands = [deck[0:10], deck[10:20], deck[20:30]]
        skat = deck[30:32]

        return cls(rule_set, dealer_idx, hands, skat, log)

    # TODO: implement
    def calculate_game_score(self) -> int:
        """
        Calculates the points a player gained or lost according to his declaration.
        """
        pass

    def apply_action(self, action: Action, check_validity: bool = True) -> None:
        """
        Executes the action and pushes it to the history stack.
        """
        if check_validity and not action.is_valid(self, self._rule_set):
            if self._log:
                print("Failed to apply action. Action is invalid.")
            return

        if self._log:
            print(f"Applying action: {action}")

        action.apply(self, self._rule_set)
        self.action_history.append(action)

    def undo_action(self) -> None:
        """
        Pops the last action and tells it to reverse its effects.
        """
        if not self.action_history:
            if self._log:
                print("No actions to undo.")
            return

        action = self.action_history.pop()

        if self._log:
            print(f"Undoing action: {action}")

        action.undo(self)

    def get_valid_actions(self, player_idx: int) -> list[Action]:
        """
        All valid actions for a given player in current state.
        """
        if player_idx != self.active_player or self.phase == GamePhase.GAME_OVER:
            return []
        return self._rule_set.get_valid_actions(self, player_idx)

    @property
    def all_bids(self) -> list[DeclareBid | Listen | Pass]:
        """
        Returns all previously made bids in order.
        """
        return [
            action
            for action in self.action_history
            if isinstance(action, (DeclareBid, Listen, Pass))
        ]

    @property
    def number_of_passes(self) -> int:
        return len(
            [action.player_idx for action in self.all_bids if isinstance(action, Pass)]
        )

    def get_player_position(self, player_idx: PlayerIdx) -> PlayerPosition:
        if player_idx == self._forehand:
            return PlayerPosition.FOREHAND
        elif player_idx == self._middlehand:
            return PlayerPosition.MIDDLEHAND
        return PlayerPosition.BACKHAND
