import math
from itertools import combinations
from typing import Generator, Optional, cast

from skaty.cards import Card, Rank, Suit, create_deck
from skaty.exceptions import (
    InvalidActionError,
    InvalidGameStateError,
    InvalidGameTypeError,
    NoCardsError,
    NoHigherBidPossible,
    TrickNotFinishedError,
)
from skaty.isko.actions import (
    BurySkat,
    DeclareBid,
    DeclareGame,
    DrawSkat,
    Listen,
    Pass,
    PlayCard,
)
from skaty.isko.state import BiddingPhase, GameDeclaration, ISkOGameState, ISkOGameTypes
from skaty.rules import (
    AbstractRuleSet,
    Action,
    GamePhase,
    GamePhases,
    GameType,
    GameTypes,
    PlayerIdx,
    PlayerPosition,
)
from skaty.trick import Trick

# All bid values possible per ISkO (Null values and grand/suit values multiplied with range of their possible multipliers).
_VALID_BIDS = [
    18,
    20,
    22,
    23,
    24,
    27,
    30,
    33,
    35,
    36,
    40,
    44,
    45,
    46,
    48,
    50,
    54,
    55,
    59,
    60,
    63,
    66,
    70,
    72,
    77,
    80,
    81,
    84,
    88,
    90,
    96,
    99,
    100,
    108,
    110,
    117,
    120,
    121,
    126,
    130,
    132,
    135,
    140,
    143,
    144,
    150,
    153,
    154,
    156,
    160,
    162,
    165,
    168,
    170,
    176,
    180,
    187,
    192,
    198,
    204,
    216,
    240,
    264,
]


class ISkO(AbstractRuleSet[ISkOGameState]):
    _VALID_BIDS = _VALID_BIDS

    # Map of actions to phases in which they are valid.
    _PHASE_RULES: dict[type[Action], list[GamePhase]] = {
        PlayCard: [GamePhases.PLAYING],
        DrawSkat: [GamePhases.DECLARATION],
        BurySkat: [GamePhases.DECLARATION],
        DeclareGame: [GamePhases.DECLARATION],
        DeclareBid: [GamePhases.BID],
        Listen: [GamePhases.BID],
        Pass: [GamePhases.BID],
    }

    _TRUMP_RANK_MAP = {
        Rank.ACE: 7,
        Rank.TEN: 6,
        Rank.KING: 5,
        Rank.QUEEN: 4,
        Rank.NINE: 3,
        Rank.EIGHT: 2,
        Rank.SEVEN: 1,
    }

    _GLOBAL_PLAY_CARDS = tuple(
        tuple(
            PlayCard(player_idx=p, card=c)
            for c in sorted(create_deck(), key=lambda c: c.uid)
        )
        for p in (0, 1, 2)
    )

    def __init__(self) -> None:
        super().__init__()

    def initialize_state(self, state: ISkOGameState) -> None:
        state.bidding_phase = BiddingPhase.ForehandMiddlehand
        state.declaration = None
        state.highest_bid = 0
        state.last_bid = None
        state.bid_before = [False, False, False]
        state.passes = [False, False, False]

    def trump_suit(self, game_type: GameType) -> Optional[Suit]:
        match game_type:
            case ISkOGameTypes.DIAMONDS:
                return Suit.DIAMONDS
            case ISkOGameTypes.HEARTS:
                return Suit.HEARTS
            case ISkOGameTypes.SPADES:
                return Suit.SPADES
            case ISkOGameTypes.CLUBS:
                return Suit.CLUBS
        # Null, Grand, Passed
        return None

    def is_card_trump(self, card: Card, game_type: GameType) -> bool:
        # ISkO 2.2.4
        if game_type in (ISkOGameTypes.NULL, ISkOGameTypes.PASS):
            return False

        # ISkO 2.2.2f.
        trump = self.trump_suit(game_type)
        return (card.suit is trump) or (card.rank is Rank.JACK)

    def has_suit(self, hand: list[Card], suit: Suit) -> bool:
        for card in hand:
            if card.suit == suit:
                return True
        return False

    def has_trump(self, hand: list[Card], game_type: GameType) -> bool:
        for card in hand:
            if self.is_card_trump(card, game_type):
                return True
        return False

    def tops(self, cards: list[Card], game_type: GameType) -> int:
        """
        Calculates the amount of tops according to ISkO 2.3.

        Raises:
            ValueError: If the cards list is empty.
            InvalidGameTypeError: If game_type is GameType.NULL or GameType.PASS.
        """
        if game_type in (ISkOGameTypes.PASS, ISkOGameTypes.NULL):
            raise InvalidGameTypeError("No tops can be calculated in Null or Pass.")

        if len(cards) == 0:
            raise NoCardsError("The hand cannot be empty.")

        # Gather all possible tops in game type.
        trump_order = [
            (Rank.JACK, Suit.CLUBS),
            (Rank.JACK, Suit.SPADES),
            (Rank.JACK, Suit.HEARTS),
            (Rank.JACK, Suit.DIAMONDS),
        ]
        if (suit := self.trump_suit(game_type)) is not None:
            for r in [
                Rank.ACE,
                Rank.TEN,
                Rank.KING,
                Rank.QUEEN,
                Rank.NINE,
                Rank.EIGHT,
                Rank.SEVEN,
            ]:
                trump_order.append((r, suit))

        hand_set = {(c.rank, c.suit) for c in cards}

        # ISkO 2.3.2
        with_tops = trump_order[0] in hand_set
        amount = 0

        for t in trump_order:
            if (t in hand_set) == with_tops:
                amount += 1
            else:
                break

        return amount

    def get_card_effective_rank_value(self, card: Card, game_type: GameType) -> int:
        """
        Returns a value representing a cards relative strength in a game type.

        Raises:
            InvalidGameTypeError: If game_type is GameType.PASS.
        """
        if game_type == ISkOGameTypes.PASS:
            raise InvalidGameTypeError
        if game_type == ISkOGameTypes.NULL:
            return card.rank.value
        # Suit or Grand
        if card.rank is Rank.JACK:
            # Jacks are highest trump
            return 100 + card.suit.value

        if self.is_card_trump(card, game_type):
            return 50 + self._TRUMP_RANK_MAP.get(card.rank, 0)
        return self._TRUMP_RANK_MAP.get(card.rank, 0)

    def determine_trick_winner(self, trick: list[Card], game_type: GameType) -> int:
        """
        Determines the winner of the trick in its order (i.e. 0 if the first card wins the trick...).

        Raises:
            TrickNotFinishedError: If trick does not contain exactly 3 cards.
            InvalidGameTypeError: If game_type is GameType.PASS.
        """
        if game_type == ISkOGameTypes.PASS:
            raise InvalidGameTypeError()
        if len(trick) != 3:
            raise TrickNotFinishedError()

        # Assume first player wins.
        winner = 0
        winner_card = trick[winner]
        winner_val = self.get_card_effective_rank_value(winner_card, game_type)

        for i in range(1, 3):
            c = trick[i]
            c_val = self.get_card_effective_rank_value(c, game_type)

            # Followed suit and played a stronger card.
            if c.suit is winner_card.suit and winner_val < c_val:
                # Due to slicing, i starts at 0
                winner = i
                winner_card = c
                winner_val = c_val

            # Played a stronger trump card.
            elif self.is_card_trump(c, game_type) and winner_val < c_val:
                winner = i
                winner_card = c
                winner_val = c_val

        return winner

    def _get_basic_value(self, game_type: GameType) -> int:
        """
        Returns the basic value per ISkO 2.4.1.

        Raises:
            InvalidGameTypeError: If game_type is Pass or Null.
        """
        match game_type:
            case ISkOGameTypes.DIAMONDS:
                return 9
            case ISkOGameTypes.HEARTS:
                return 10
            case ISkOGameTypes.SPADES:
                return 11
            case ISkOGameTypes.CLUBS:
                return 12
            case ISkOGameTypes.GRAND:
                return 24

        raise InvalidGameTypeError()

    def calculate_game_score(self, state: ISkOGameState) -> list[int]:
        scores = [0, 0, 0]
        declarer = state.declarer_idx
        bid = state.bid
        game_type = state.game_type

        if (
            game_type is GameTypes.PASS
            or state.phase is GamePhases.PASSED
            or bid is None
        ):
            raise InvalidGameStateError("A game has no score if it is passed.")
        if declarer is None or state.declaration is None:
            raise InvalidGameStateError(
                "A game has no score if there is no declarer or declaration."
            )
        if len(state.trick_history) != 10 or state.phase != GamePhases.GAME_OVER:
            raise InvalidGameStateError(
                "A game has no score if it is not finished yet."
            )

        hand = state.declaration.hand
        schneider_announced = state.declaration.schneider
        schwarz_announced = state.declaration.schwarz
        open = state.declaration.open

        # Reconstruct the tricks
        tricks_won_by_player = self.get_won_tricks(state)
        declarer_tricks = tricks_won_by_player[declarer]

        if state.game_type is ISkOGameTypes.NULL:
            if hand and open:
                game_value = 59
            elif open:
                game_value = 46
            elif hand:
                game_value = 35
            else:
                game_value = 23

            won = len(declarer_tricks) == 0

            if game_value < bid:
                won = False

            scores[declarer] = game_value if won else -2 * game_value
            return scores

        tops = state.tops
        if tops is None:
            raise InvalidGameStateError("No tops were saved during declaration.")

        base_value = self._get_basic_value(game_type)
        declarer_points = (
            sum(trick.get_trick_points() for trick in tricks_won_by_player[declarer])
            + state.skat[0].points
            + state.skat[1].points
        )
        opponents_points = 120 - declarer_points

        is_schneider = (opponents_points <= 30) or (declarer_points <= 30)
        is_schwarz = len(declarer_tricks) == 0 or len(declarer_tricks) == 10

        multiplier = 1 + tops
        if hand:
            multiplier += 1
        if schneider_announced:
            multiplier += 1
        if is_schneider:
            multiplier += 1
        if schwarz_announced:
            multiplier += 1
        if is_schwarz:
            multiplier += 1
        if open:
            multiplier += 1

        game_value = multiplier * base_value

        won = True
        if schwarz_announced and not is_schwarz:
            won = False
        elif schneider_announced and not is_schneider:
            won = False
        elif declarer_points < 61:
            won = False

        # Overbid
        if game_value < bid:
            won = False
            multiplier = math.ceil(bid / base_value)
            game_value = multiplier * base_value

        if won:
            scores[declarer] = game_value
        else:
            scores[declarer] = -2 * game_value
        return scores

    def get_won_tricks(self, state: ISkOGameState) -> list[list[Trick]]:
        """
        Reconstructs the tricks won by each player.

        Returns:
            A list of length 3. The index corresponds to player_idx. The value at the index if a list of tricks that this player won.
        """
        tricks_won: list[list[Trick]] = [[], [], []]

        if state.declaration is None or state.declaration.game_type is GameTypes.PASS:
            return tricks_won

        game_type = state.game_type
        current_leader = state._forehand

        for trick in state.trick_history:
            cards = trick.cards
            winner_offset = self.determine_trick_winner(cards, game_type)
            winner_idx = (current_leader + winner_offset) % 3

            tricks_won[winner_idx].append(trick)
            current_leader = winner_idx

        return tricks_won

    def is_valid_action_during_phase(
        self,
        action: Action,
        phase: GamePhase,
    ) -> bool:
        """
        Tests if action is possible in game phase. Does not imply the particular action itself is valid (e.g. for Bid(17), GamePhase.BIDDING it would return True, as Bid is a valid action in bidding even though Bid(17) itself is not valid).
        """
        allowed_phases = self._PHASE_RULES.get(type(action), [])
        return phase in allowed_phases

    def get_action_types_for_phase(self, phase: GamePhase) -> list[type[Action]]:
        """
        Returns all valid action types for a given phase.
        """
        return [at for at, phases in self._PHASE_RULES.items() if phase in phases]

    def get_next_valid_bid(self, current_bid: Optional[int]) -> int:
        """
        Calculates the next highest valid bid.

        Raises:
            NoHigherBidPossible: If no higher bid is possible.
        """
        if current_bid is None:
            return 18
        for b in self._VALID_BIDS:
            if b > current_bid:
                return b
        raise NoHigherBidPossible()

    def is_valid_bid(
        self,
        state: ISkOGameState,
        bid: DeclareBid | Listen | Pass,
    ) -> bool:
        """
        Determines if bid is valid for player in player_pos in the context of previous_bids and bidding_phase. Passing is allowed for every player in every bidding phase if they have not passed before or bid/listened before and are the only one left.
        """
        player = bid.player_idx
        player_pos = state.get_player_position(player)
        bidding_phase = state.bidding_phase

        # Check if player has passed before.
        if state.passes[bid.player_idx]:
            return False

        # Count passes
        passes = sum(state.passes)
        bid_before = state.bid_before[bid.player_idx]

        # If both other players have passed, reject Pass if player has listened/bid before
        if passes == 2 and isinstance(bid, Pass) and bid_before:
            return False

        if isinstance(bid, DeclareBid):
            # Backhand is the only one that can bid in these phases. However, if 2 players passed, anyone can bid.
            if (
                bidding_phase
                in (BiddingPhase.ForehandBackhand, BiddingPhase.MiddlehandBackhand)
                and player_pos != PlayerPosition.BACKHAND
                and passes < 2
            ):
                return False
            # Middlehand can only bid in ForehandMiddlehand
            if (
                bidding_phase is BiddingPhase.ForehandMiddlehand
                and player_pos != PlayerPosition.MIDDLEHAND
            ):
                return False

            # Must be higher than all previous bids and valid value
            return bid.bid > state.highest_bid and bid.bid in self._VALID_BIDS

        # Listen can only be done in response to a bid directly before
        if isinstance(bid, Listen):
            return isinstance(state.last_bid, DeclareBid)

        # Pass is allowed unless already passed or forbidden by above rule
        if isinstance(bid, Pass):
            return True

    def is_valid_card_play(
        self,
        hand: list[Card],
        card: Card,
        first_card: Optional[Card],
        game_type: GameType,
    ) -> bool:
        """
        Determines if player can play card in a trick started with first_card in some GameType. For an empty trick, first_card is None. If game_type is GameType.PASS always returns False regardless of card and first_card.
        """
        # Player can not play card not available
        if card not in hand:
            return False

        # No card can be played if game is passed.
        if game_type is GameTypes.PASS:
            return False
        # Any card can be played if it is first
        if first_card is None:
            return True

        # If player has trump, he must follow
        if self.is_card_trump(first_card, game_type) and self.has_trump(
            hand, game_type
        ):
            return self.is_card_trump(card, game_type)

        # If player has suit, he must follow
        if self.has_suit(hand, first_card.suit):
            return card.suit is first_card.suit

        # Otherwise, any card is valid
        return True

    def is_valid_game_declaration(self, declaration: GameDeclaration) -> bool:
        """
        Determines if the game declaration is formally correct. It does not check if the game satisfies the bid. A player is allowed to overbid, but will lose during score calculation.
        """
        game_type = declaration.game_type
        hand = declaration.hand
        schneider = declaration.schneider
        schwarz = declaration.schwarz
        open = declaration.open

        if game_type == GameTypes.PASS:
            return False

        if game_type == ISkOGameTypes.NULL:
            if schneider or schwarz:
                return False
        else:  # Suit and Grand
            if schneider and not hand:
                return False
            if schwarz and not (hand and schneider):
                return False
            if open and not (hand and schneider and schwarz):
                return False

        return True

    def get_valid_actions(
        self, state: ISkOGameState, player_idx: PlayerIdx
    ) -> Generator[Action, None, None]:
        if player_idx != state.active_player or state.phase == GamePhases.GAME_OVER:
            return

        valid_actions = self.get_action_types_for_phase(state.phase)

        for action_type in valid_actions:
            if action_type is PlayCard:
                hand = state.hands[player_idx]
                for card in hand:
                    if self.is_valid_card_play(
                        hand, card, state.current_trick.first_card, state.game_type
                    ):
                        yield self._GLOBAL_PLAY_CARDS[player_idx][card.uid]

            elif action_type is DeclareBid:
                try:
                    next_bid = self.get_next_valid_bid(state.bid)
                except NoHigherBidPossible:
                    continue

                if self.is_valid_bid(
                    state, DeclareBid(player_idx=player_idx, bid=next_bid)
                ):
                    yield DeclareBid(bid=next_bid, player_idx=player_idx)

            elif action_type in (Pass, Listen, DrawSkat):
                action = action_type(player_idx=player_idx)
                if action.is_valid(state, self):
                    yield action

            elif action_type is BurySkat and len(state.skat) == 0:
                hand = state.hands[player_idx]
                for combo in combinations(hand, 2):
                    yield BurySkat(cards=(combo[0], combo[1]), player_idx=player_idx)

            elif action_type is DeclareGame:
                for gt in [
                    ISkOGameTypes.NULL,
                    ISkOGameTypes.DIAMONDS,
                    ISkOGameTypes.HEARTS,
                    ISkOGameTypes.SPADES,
                    ISkOGameTypes.CLUBS,
                    ISkOGameTypes.GRAND,
                ]:
                    if gt is ISkOGameTypes.NULL:
                        yield DeclareGame(
                            game_type=gt, open=False, player_idx=player_idx
                        )
                        yield DeclareGame(
                            game_type=gt, open=True, player_idx=player_idx
                        )
                    else:  # Suit or Grand
                        # Hand or not hand game without any modifiers
                        yield DeclareGame(game_type=gt, player_idx=player_idx)
                        if not state.hand_available:
                            # Schneider etc. not applicable
                            continue

                        yield DeclareGame(
                            game_type=gt, schneider=True, player_idx=player_idx
                        )
                        yield DeclareGame(
                            game_type=gt,
                            schneider=True,
                            schwarz=True,
                            player_idx=player_idx,
                        )
                        yield DeclareGame(
                            game_type=gt,
                            schneider=True,
                            schwarz=True,
                            open=True,
                            player_idx=player_idx,
                        )

    def is_valid_action(self, state: ISkOGameState, action: Action) -> bool:
        # Only the active player can take action
        if action.player_idx != state.active_player:
            return False

        # Only allow actions their phase
        if not self.is_valid_action_during_phase(action, state.phase):
            return False

        match action:
            case DeclareBid() | Listen() | Pass():
                return self.is_valid_bid(state, action)

            case BurySkat(player_idx, cards):
                if len(state.skat) != 0:
                    return False

                hand = state.hands[player_idx]
                # Cannot bury card not in hand
                if cards[0] not in hand or cards[1] not in hand:
                    return False
                if cards[0] == cards[1]:
                    return False

                return True

            case DrawSkat(player_idx):
                return len(state.skat) == 2

            case DeclareGame(player_idx, game_type, schneider, schwarz, open):
                if player_idx != state.declarer_idx:
                    return False

                declaration = GameDeclaration(
                    game_type,
                    hand=state.hand_available,
                    schneider=schneider,
                    schwarz=schwarz,
                    open=open,
                )
                return self.is_valid_game_declaration(declaration)

            case PlayCard(player_idx, card):
                return self.is_valid_card_play(
                    state.hands[player_idx],
                    card,
                    state.current_trick.first_card,
                    state.game_type,
                )

        raise InvalidActionError(
            f"Cannot determine if action {action} is valid in {state}."
        )

    def advance_state(self, state: ISkOGameState, action: Action) -> None:
        match action:
            case DeclareBid() | Listen() | Pass():
                return self.advance_bidding(state, action)
            case DrawSkat() | BurySkat():
                return
            case DeclareGame(player_idx, game_type, schneider, schwarz, open):
                state.phase = GamePhases.PLAYING
                state.declaration = GameDeclaration(
                    game_type, state.hand_available, schneider, schwarz, open
                )
                state.active_player = state._forehand
                state.game_type = game_type
                if game_type not in (GameTypes.PASS, ISkOGameTypes.NULL):
                    state.tops = self.tops(state.hands[player_idx], game_type)
            case PlayCard():
                return self.advance_playing(state, action)

    def advance_bidding(
        self, state: ISkOGameState, action: DeclareBid | Listen | Pass
    ) -> None:
        """
        Mutate the state in bidding dependent on action.
        Might modify:

        - state.active_player
        - state.bidding_phase
        - state.phase
        - state.declarer_idx

        If bidding continues after action, update:

        - state.active_player: to the next player bidding
        - state.bidding_phase: if a player passes

        If bidding finishes with a declarer after action, update:

        - state.active_player: to be index of declarer
        - state.phase: to GamePhase.DECLARATION
        - state.declarer_idx: to be index of declarer

        If bidding finishes with all players passing after action, update:

        - state.phase: to GamePhase.GAME_OVER.
        """
        player = state.active_player
        passes = sum(state.passes)
        bid_before = state.bid is not None

        if state.bidding_phase is BiddingPhase.ForehandMiddlehand:
            # Pass, switch to other phase
            if isinstance(action, Pass):
                # Backhand does "weitersagen"
                state.active_player = state._backhand
                if player == state._forehand:
                    state.bidding_phase = BiddingPhase.MiddlehandBackhand
                else:
                    state.bidding_phase = BiddingPhase.ForehandBackhand
            # Otherwise, alternate between forehand and middlehand
            else:
                if player == state._forehand:
                    state.active_player = state._middlehand
                elif player == state._middlehand:
                    state.active_player = state._forehand
            return

        elif state.bidding_phase is BiddingPhase.ForehandBackhand:
            other_player = (
                state._forehand
                if state.active_player == state._backhand
                else state._backhand
            )
        else:  # MiddlehandBackhand
            other_player = (
                state._middlehand
                if state.active_player == state._backhand
                else state._backhand
            )

        if isinstance(action, Pass):
            # 2 players passed
            if bid_before:
                state.phase = GamePhases.DECLARATION
                state.declarer_idx = other_player
                state.active_player = state.declarer_idx
            elif passes == 2:
                state.phase = GamePhases.PASSED
            elif passes < 2:
                state.active_player = other_player

        elif isinstance(action, (Listen, DeclareBid)):
            if passes == 2:
                state.phase = GamePhases.DECLARATION
                state.declarer_idx = player
                state.active_player = state.declarer_idx
            else:
                state.active_player = other_player

    def advance_playing(self, state: ISkOGameState, action: PlayCard) -> None:
        """
        Mutate the state as card is played.
        Might modify:

        - state.active_player
        - state.phase
        - state.current_trick
        - state.trick_history
        - state.points
        """
        state.current_trick.add_card(action.card)

        if state.current_trick.is_complete():
            points = state.current_trick.get_trick_points()
            # Index of winner in trick order
            winner_offset = state.current_trick.get_winner(self, state.game_type)

            current_player = state.active_player
            first_player = (current_player - 2) % 3
            winner = (first_player + winner_offset) % 3
            state.points[winner] += points

            state.trick_history.append(state.current_trick)
            # Reset trick
            state.current_trick = Trick()
            if len(state.trick_history) == 10:
                state.phase = GamePhases.GAME_OVER
                return

            # Winner of trick starts next trick
            state.active_player = cast(PlayerIdx, winner)
        else:
            state.active_player = (state.active_player + 1) % 3
