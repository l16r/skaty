from typing import Optional

from skaty.cards import Card, Rank, Suit
from skaty.comparable_card import ComparableCard
from skaty.exceptions import (
    InvalidBidError,
    InvalidDeclarationError,
    InvalidGameTypeError,
    NoCardsError,
    NoHigherBidPossible,
    TrickNotFinishedError,
)
from skaty.player import Player
from skaty.rules import (
    AbstractRuleSet,
    Action,
    BiddingPhase,
    BurySkat,
    DealCards,
    DeclareBid,
    DeclareGame,
    DrawSkat,
    GamePhase,
    GameType,
    GiveUp,
    Listen,
    Pass,
    PlayCard,
    PlayerPosition,
)
from skaty.trick import Trick

# All bid values possible per ISkO (Null values and grand/suit values multiplied with range of their possible multipliers).
_VALID_BIDS = frozenset(
    [
        23,
        35,
        46,
        59,
        18,
        20,
        22,
        24,
        27,
        30,
        33,
        36,
        40,
        44,
        48,
        45,
        50,
        55,
        60,
        54,
        66,
        72,
        63,
        70,
        77,
        84,
        80,
        88,
        96,
        81,
        90,
        99,
        108,
        100,
        110,
        120,
        121,
        132,
        144,
        117,
        130,
        143,
        156,
        126,
        140,
        154,
        168,
        135,
        150,
        165,
        180,
        160,
        176,
        192,
        153,
        170,
        187,
        204,
        162,
        198,
        216,
        240,
        264,
    ]
)


class ISkO(AbstractRuleSet):
    _VALID_BIDS = _VALID_BIDS

    # Map of actions to phases in which they are valid.
    _PHASE_RULES: dict[type[Action], list[GamePhase]] = {
        DealCards: [GamePhase.PRE_DEAL],
        PlayCard: [GamePhase.PLAYING],
        DrawSkat: [GamePhase.DECLARATION],
        BurySkat: [GamePhase.DECLARATION],
        DeclareGame: [GamePhase.DECLARATION],
        DeclareBid: [GamePhase.BID],
        Listen: [GamePhase.BID],
        Pass: [GamePhase.BID],
        GiveUp: [GamePhase.PLAYING],
    }

    def __init__(self) -> None:
        super().__init__()

    def trump_suit(self, game_type: GameType) -> Optional[Suit]:
        match game_type:
            case GameType.DIAMONDS:
                return Suit.DIAMONDS
            case GameType.HEARTS:
                return Suit.HEARTS
            case GameType.SPADES:
                return Suit.SPADES
            case GameType.CLUBS:
                return Suit.CLUBS
        # Null, Grand, Passed
        return None

    def is_card_trump(self, card: Card, game_type: GameType) -> bool:
        # ISkO 2.2.4
        if game_type in (GameType.NULL, GameType.PASS):
            return False

        # ISkO 2.2.2f.
        trump = self.trump_suit(game_type)
        return (card.suit is trump) or (card.rank is Rank.JACK)

    def has_trump(self, player: Player, game_type: GameType) -> bool:
        for card in player.hand:
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
        if game_type in (GameType.PASS, GameType.NULL):
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
        if game_type is GameType.PASS:
            raise InvalidGameTypeError
        if game_type is GameType.NULL:
            return card.rank.value
        # Suit or Grand
        if card.rank is Rank.JACK:
            # Jacks are highest trump
            return 100 + card.suit.value

        trump_rank_map = {
            Rank.ACE: 7,
            Rank.TEN: 6,
            Rank.KING: 5,
            Rank.QUEEN: 4,
            Rank.NINE: 3,
            Rank.EIGHT: 2,
            Rank.SEVEN: 1,
        }
        if self.is_card_trump(card, game_type):
            return 50 + trump_rank_map.get(card.rank, 0)
        return trump_rank_map.get(card.rank, 0)

    def determine_trick_winner(self, trick: list[Card], game_type: GameType) -> int:
        """
        Determines the winner of the trick in its order (i.e. 0 if the first card wins the trick...).

        Raises:
            TrickNotFinishedError: If trick does not contain exactly 3 cards.
            InvalidGameTypeError: If game_type is GameType.PASS.
        """
        if game_type is GameType.PASS:
            raise InvalidGameTypeError()
        if len(trick) != 3:
            raise TrickNotFinishedError()

        # Assume first player wins.
        winner = 0

        for i, c in enumerate(trick[1:]):
            # Followed suit and played a stronger card.
            if c.suit is trick[winner].suit and self.get_card_effective_rank_value(
                trick[winner], game_type
            ) < self.get_card_effective_rank_value(c, game_type):
                # Due to slicing, i starts at 0
                winner = i + 1
            # Played a stronger trump card.
            elif self.is_card_trump(
                c, game_type
            ) and self.get_card_effective_rank_value(
                trick[winner], game_type
            ) < self.get_card_effective_rank_value(c, game_type):
                winner = i + 1

        return winner

    def calculate_game_score(
        self,
        players: list[Player],
        declarer: int,
        points: dict[Player, int],
        tricks: list[tuple[Trick, Player]],
        game_type: GameType,
        bid: int,
        skat: tuple[Card, Card],
        hand: bool = False,
        schneider_announced: bool = False,
        schwarz_announced: bool = False,
        ouvert: bool = False,
    ) -> int:
        """
        Calculate the game score according to Skat rules.
        Returns positive score if declarer wins, negative if loses.
        """
        # Points
        declarer_player = players[declarer]
        declarer_points = points[declarer_player]

        tricks_scored = sum(1 for _, player in tricks if player == declarer_player)
        # ISkO 2.5.5
        is_schneider = declarer_points >= 90 or declarer_points <= 30
        # ISkO 2.5.6
        is_schwarz = tricks_scored == 0 or tricks_scored == 10

        base_value = game_type.value

        if game_type is GameType.NULL:
            # ISkO 2.4.2
            if hand and ouvert:
                base_value = 59
            elif hand:
                base_value = 35
            elif ouvert:
                base_value = 46
            if tricks_scored > 0 or bid > base_value:
                # Lost
                base_value *= -2
            return base_value

        tops = self.tops(declarer_player.hand + list(skat), game_type)
        multiplier = 1 + tops
        lost = declarer_points <= 60
        if hand:
            multiplier += 1

        if is_schneider:
            multiplier += 1
        if is_schwarz:
            multiplier += 1
        if ouvert:
            multiplier += 1
        if schneider_announced:
            multiplier += 1
        if schwarz_announced:
            multiplier += 1

        # Check if announcements are correct
        if ouvert and not is_schwarz:
            lost = True
        if schwarz_announced and not is_schwarz:
            lost = True
        if schneider_announced and not is_schneider:
            lost = True
        if bid > multiplier * base_value:
            lost = True

        if lost:
            return -2 * multiplier * base_value
        return multiplier * base_value

    def is_valid_action(
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
        sorted_bids = sorted(self._VALID_BIDS)
        for b in sorted_bids:
            if b > current_bid:
                return b
        raise NoHigherBidPossible()

    def is_valid_bid(
        self,
        player: Player,
        bid: DeclareBid | Listen | Pass,
        previous_bids: list[tuple[Player, DeclareBid | Listen | Pass]],
        player_pos: PlayerPosition,
        bidding_phase: BiddingPhase,
    ) -> bool:
        """
        Determines if bid is valid for player in player_pos in the context of previous_bids and bidding_phase. Passing is allowed for every player in every bidding phase if they have not passed before or bid/listened before and are the only one left.
        """
        # Check if player has passed before.
        for b in previous_bids:
            if b[0] == player and isinstance(b[1], Pass):
                return False

        # Count passes
        passes = len([p for p, a in previous_bids if isinstance(a, Pass)])
        bid_before = any(
            isinstance(a, (DeclareBid, Listen)) for p, a in previous_bids if p == player
        )

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
            max_bid = max(
                (a.bid for _, a in previous_bids if isinstance(a, DeclareBid)),
                default=0,
            )
            return bid.bid > max_bid and bid.bid in self._VALID_BIDS

        # Listen can only be done in response to a bid directly before
        if isinstance(bid, Listen):
            if len(previous_bids) == 0:
                return False
            bid_before = previous_bids[-1]
            return isinstance(bid_before[1], DeclareBid)

        # Pass is allowed unless already passed or forbidden by above rule
        if isinstance(bid, Pass):
            return True

    def is_valid_card_play(
        self,
        player: Player,
        card: Card,
        first_card: Optional[Card],
        game_type: GameType,
    ) -> bool:
        """
        Determines if player can play card in a trick started with first_card in some GameType. For an empty trick, first_card is None. If game_type is GameType.PASS always returns False regardless of card and first_card.
        """
        # Player can not play card not available
        if card not in player.hand:
            return False

        # No card can be played if game is passed.
        if game_type is GameType.PASS:
            return False
        # Any card can be played if it is first
        if first_card is None:
            return True

        # If player has trump, he must follow
        if self.is_card_trump(first_card, game_type) and self.has_trump(
            player, game_type
        ):
            return self.is_card_trump(card, game_type)

        # If player has suit, he must follow
        if player.has_suit(first_card.suit):
            return card.suit is first_card.suit

        # Otherwise, any card is valid
        return True

    def is_valid_game_declaration(
        self,
        player: Player,
        skat: tuple[Card, Card],
        bid: int,
        game_type: GameType,
        hand: bool,
        schneider: bool,
        schwarz: bool,
        open: bool,
    ) -> bool:
        """
        Determines if the arguments represent a valid game declaration given the bid value. The multipliers must be applied correctly. The most favorable scenario for the player (i.e. assuming playing Schwarz) must give him enough points to achieve the bid. When playing hand, the skat is ignored from tops, as the player possesses no information about it.

        Raises:
            InvalidDeclarationError: If bid is invalid.
            InvalidGameTypeError: If game_type is GameType.PASS.
        """
        if game_type is GameType.PASS:
            raise InvalidGameTypeError(
                "A game declaration can not be made with GameType.PASS."
            )
        if bid not in self._VALID_BIDS:
            raise InvalidDeclarationError("Invalid bid value.")

        if game_type is GameType.NULL:
            # ISkO 2.4.2
            if open and hand:
                return bid <= 59
            elif open:
                return bid <= 46
            elif hand:
                return bid <= 35
            return bid <= 23

        # Check multiplier validity. Open requires Schwarz requires Schneider requires Hand.
        if schneider and not hand:
            return False
        elif schwarz and not (hand and schneider):
            return False
        elif open and not (hand and schneider and schwarz):
            return False

        base_value = game_type.value
        multiplier = 1
        if hand:
            multiplier += 1
        if schneider and hand:
            multiplier += 1
        if schwarz and schneider and hand:
            multiplier += 1
        if open and schwarz and schneider and hand:
            multiplier += 1

        # The declaration is based upon the knowledge of the player.
        if hand:
            tops = self.tops(player.hand, game_type)
        else:
            tops = self.tops(player.hand + list(skat), game_type)

        # If the player plays Schwarz, he also gets one multiplier for each playing Schneider and Schwarz.
        return bid <= (tops + multiplier + 2) * base_value
