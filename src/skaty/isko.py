from typing import Optional

from skaty.cards import Card, Rank, Suit
from skaty.player import Player
from skaty.rules import AbstractRuleSet, Action, GamePhase, GameType, Pass


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

    def is_valid_card_play(self, player: Player, card: Card, first_card: Card) -> bool:
        if card not in player.hand:
            return False

        if self.game_type() is GameType.PASS:
            return False
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
    ) -> bool:
        # TODO: implement
        return True
