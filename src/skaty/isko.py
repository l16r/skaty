from typing import Optional

from skaty.cards import Card, Rank, Suit
from skaty.comparable_card import ComparableCard
from skaty.exceptions import InvalidPlayError
from skaty.player import Player
from skaty.rules import AbstractRuleSet, Action, GamePhase, GameType

# All bid values possible. The Null values and the grand and suit values multiplied with the range of their possible multipliers.
VALID_BID_VALUES = [
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


class ISkO(AbstractRuleSet):
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

        print(f"sortedAllTops: {sortedAllTops}")
        print(f"sortedCards: {sortedCards}")
        print(f"withTops: {withTops}")

        if withTops:
            for c in zip(sortedAllTops, sortedCards):
                print(f"comparing: {c}")
                if c[0] != c[1]:
                    print("break with tops")
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

    def calculate_game_score(self) -> int:
        # TODO: implement
        return 0

    def is_valid_action(self, player: Player, action: Action, phase: GamePhase) -> bool:
        # TODO: implement
        return True

    def is_valid_bid(self, player: Player, bid: int) -> bool:
        # TODO: implement
        return True

    def is_valid_card_play(
        self, player: Player, card: Card, first_card: Optional[Card]
    ) -> bool:
        if card not in player.hand:
            return False

        if self.game_type() is GameType.PASS:
            return False
        if first_card is None:
            return True

        if self.is_card_trump(first_card):
            return self.is_card_trump(card)
        if card.suit is not first_card.suit:
            for c in player.hand:
                if c.suit is first_card.suit:
                    return False
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
        if bid not in VALID_BID_VALUES:
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

        # Not really a good solution
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

        tops = self.tops(player.hand)

        return bid <= (tops + multiplier) * base_value
