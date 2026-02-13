from typing import Literal, Optional, Union

from skaty.cards import Card, Rank, Suit
from skaty.comparable_card import ComparableCard
from skaty.exceptions import InvalidBidError, InvalidPlayError
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
        Pass: [GamePhase.PRE_DEAL, GamePhase.BID],
        GiveUp: [GamePhase.PLAYING],
    }

    _game_type: GameType

    def __init__(self) -> None:
        super().__init__()
        self._game_type = GameType.PASS

    def game_type(self) -> GameType:
        return self._game_type

    def set_game_type(self, v: GameType):
        self._game_type = v

    def trump_suit(self) -> Optional[Suit]:
        match self._game_type:
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

    def is_card_trump(self, card: Card) -> bool:
        # ISkO 2.2.4
        if self.game_type() in (GameType.NULL, GameType.PASS):
            return False

        # ISkO 2.2.2f.
        trump = self.trump_suit()
        return (card.suit is trump) or (card.rank is Rank.JACK)

    def has_trump(self, player: Player):
        for card in player.hand:
            if self.is_card_trump(card):
                return True
        return False

    def has_suit(self, player: Player, suit: Suit):
        for card in player.hand:
            if card.suit is suit:
                return True
        return False

    def tops(self, cards: list[Card]) -> int:
        """
        Calculates the amount of tops according to ISkO 2.3.

        Raises:
            ValueError: If the cards list is empty.
        """
        if self.game_type() in (GameType.PASS, GameType.NULL):
            return 0

        if len(cards) == 0:
            raise ValueError("The hand cannot be empty.")

        allTops = [Card(Rank.JACK, suit) for suit in Suit]
        if (trump := self.trump_suit()) is not None:
            allTops += [Card(rank, trump) for rank in Rank if rank is not Rank.JACK]
        allTops = [ComparableCard(card, self) for card in allTops]
        sortedAllTops = sorted(allTops, reverse=True)
        sortedCards = sorted(
            [ComparableCard(card, self) for card in cards], reverse=True
        )

        withTops = sortedAllTops[0] == sortedCards[0]
        counter = 0

        if withTops:
            for c in zip(sortedAllTops, sortedCards):
                if c[0] != c[1]:
                    break
                counter += 1
        else:
            try:
                highest_top = sortedAllTops.index(sortedCards[0])
                counter = highest_top
            except ValueError:
                return len(sortedAllTops)

        return counter

    def get_card_effective_rank_value(self, card: Card) -> int:
        if self._game_type is GameType.PASS:
            return 0
        if self._game_type is GameType.NULL:
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
        if self.is_card_trump(card):
            return 50 + trump_rank_map.get(card.rank, 0)
        return trump_rank_map.get(card.rank, 0)

    def determine_trick_winner(self, trick: list[Card]) -> int:
        assert len(trick) == 3

        winner = 0

        for i, c in enumerate(trick[1:]):
            if c.suit is trick[winner].suit and self.get_card_effective_rank_value(
                trick[winner]
            ) < self.get_card_effective_rank_value(c):
                winner = i + 1
            elif self.is_card_trump(c) and self.get_card_effective_rank_value(
                trick[winner]
            ) < self.get_card_effective_rank_value(c):
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

        tops = self.tops(declarer_player.hand + list(skat))
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
        allowed_phases = self._PHASE_RULES.get(type(action), [])
        return phase in allowed_phases

    def get_action_types_for_phase(self, phase: GamePhase) -> list[type[Action]]:
        return [at for at, phases in self._PHASE_RULES.items() if phase in phases]

    def get_next_valid_bid(self, current_bid: Optional[int]) -> int:
        if current_bid is None:
            return 18
        sorted_bids = sorted(self._VALID_BIDS)
        for b in sorted_bids:
            if b > current_bid:
                return b
        raise InvalidBidError(f"No bid after {current_bid} possible.")

    def is_valid_bid(
        self,
        player: Player,
        bid: DeclareBid | Listen | Pass,
        previous_bids: list[tuple[Player, DeclareBid | Listen | Pass]],
        player_pos: PlayerPosition,
        bidding_phase: BiddingPhase,
    ) -> bool:
        # Check if player has passed before
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
            # Backhand is the only one that can bid in these phases
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
                and passes < 2
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
        self, player: Player, card: Card, first_card: Optional[Card]
    ) -> bool:
        # Player can not play card not available
        if card not in player.hand:
            return False

        # No card can be played if game is passed.
        if self.game_type() is GameType.PASS:
            return False
        # Any card can be played if it is first
        if first_card is None:
            return True

        # If player has trump, he must follow
        if self.is_card_trump(first_card) and self.has_trump(player):
            return self.is_card_trump(card)

        # If player has suit, he must follow
        if self.has_suit(player, first_card.suit):
            return card.suit is first_card.suit

        return True

    def is_valid_game_declaration(
        self,
        player: Player,
        bid: int,
        game_type: GameType,
        hand: bool,
        schneider: bool = False,
        schwarz: bool = False,
        open: bool = False,
        hand_available: bool = True,
    ) -> bool:
        if game_type is GameType.PASS:
            return True
        if bid not in self._VALID_BIDS:
            return False

        if game_type is GameType.NULL:
            # ISkO 2.4.2
            if open and hand and hand_available:
                return bid <= 59
            if open:
                return bid <= 46
            if hand and hand_available:
                return bid <= 35
            return bid <= 23

        if (hand or schneider or schwarz or open) and not hand_available:
            raise InvalidPlayError("Can only play hand if the Skat has not been drawn.")
        elif (schneider or schwarz or open) and not (hand_available and hand):
            raise InvalidPlayError(
                "Can only play Schneider, Schwarz or open if hand is available and used."
            )
        if (schwarz or open) and not (hand_available and hand and schneider):
            raise InvalidPlayError(
                "Can only play Schwarz if hand is avaible and used with Schneider declaration."
            )
        if open and not (hand_available and hand and schneider and schwarz):
            raise InvalidPlayError(
                "Can only play Schwarz if hand is avaible and used with Schneider Schwarz declaration."
            )

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

        # TODO: tops need to include the Skat
        self.set_game_type(game_type)
        tops = self.tops(player.hand)

        return bid <= (tops + multiplier) * base_value
