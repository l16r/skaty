from contextlib import nullcontext
from dataclasses import dataclass, field
import random
from typing import Any, ContextManager, Optional
from unittest.mock import MagicMock
import pytest
from skaty.actions import DeclareBid, Listen, Pass, PlayerIdx
from skaty.cards import Card, Rank, Suit
from skaty.exceptions import (
    InvalidDeclarationError,
    InvalidGameTypeError,
    NoCardsError,
    NoHigherBidPossible,
    TrickNotFinishedError,
)
from skaty.game_state import GameState
from skaty.isko import ISkO
from skaty.player import Player
from skaty.rules import (
    BiddingPhase,
    GameDeclaration,
    GameType,
    PlayerPosition,
)

isko = ISkO()
forehand: PlayerIdx = 0
middlehand: PlayerIdx = 1
backhand: PlayerIdx = 2

hand_with_one = [Card(Rank.JACK, Suit.CLUBS)]
hand_without_four = [Card(Rank.ACE, Suit.DIAMONDS)]


def test_get_card_effective_rank_value():
    test_data = [
        (GameType.CLUBS, Card(Rank.JACK, Suit.CLUBS), 103),
        (GameType.CLUBS, Card(Rank.JACK, Suit.SPADES), 102),
        (GameType.CLUBS, Card(Rank.JACK, Suit.HEARTS), 101),
        (GameType.CLUBS, Card(Rank.JACK, Suit.DIAMONDS), 100),
        (GameType.CLUBS, Card(Rank.ACE, Suit.CLUBS), 57),
        (GameType.CLUBS, Card(Rank.TEN, Suit.CLUBS), 56),
        (GameType.CLUBS, Card(Rank.KING, Suit.CLUBS), 55),
        (GameType.CLUBS, Card(Rank.QUEEN, Suit.CLUBS), 54),
        (GameType.CLUBS, Card(Rank.NINE, Suit.CLUBS), 53),
        (GameType.CLUBS, Card(Rank.EIGHT, Suit.CLUBS), 52),
        (GameType.CLUBS, Card(Rank.SEVEN, Suit.CLUBS), 51),
        (GameType.CLUBS, Card(Rank.ACE, Suit.HEARTS), 7),
        (GameType.CLUBS, Card(Rank.TEN, Suit.DIAMONDS), 6),
        (GameType.CLUBS, Card(Rank.KING, Suit.SPADES), 5),
        (GameType.CLUBS, Card(Rank.QUEEN, Suit.HEARTS), 4),
        (GameType.CLUBS, Card(Rank.NINE, Suit.HEARTS), 3),
        (GameType.CLUBS, Card(Rank.EIGHT, Suit.SPADES), 2),
        (GameType.CLUBS, Card(Rank.SEVEN, Suit.HEARTS), 1),
        #
        (GameType.NULL, Card(Rank.JACK, Suit.CLUBS), 11),
        (GameType.NULL, Card(Rank.JACK, Suit.SPADES), 11),
        (GameType.NULL, Card(Rank.JACK, Suit.HEARTS), 11),
        (GameType.NULL, Card(Rank.JACK, Suit.DIAMONDS), 11),
        (GameType.NULL, Card(Rank.ACE, Suit.CLUBS), 14),
        (GameType.NULL, Card(Rank.TEN, Suit.CLUBS), 10),
        (GameType.NULL, Card(Rank.KING, Suit.CLUBS), 13),
        (GameType.NULL, Card(Rank.QUEEN, Suit.CLUBS), 12),
        (GameType.NULL, Card(Rank.NINE, Suit.CLUBS), 9),
        (GameType.NULL, Card(Rank.EIGHT, Suit.CLUBS), 8),
        (GameType.NULL, Card(Rank.SEVEN, Suit.CLUBS), 7),
        (GameType.NULL, Card(Rank.ACE, Suit.HEARTS), 14),
        (GameType.NULL, Card(Rank.TEN, Suit.DIAMONDS), 10),
        (GameType.NULL, Card(Rank.KING, Suit.SPADES), 13),
        (GameType.NULL, Card(Rank.QUEEN, Suit.HEARTS), 12),
        (GameType.NULL, Card(Rank.NINE, Suit.HEARTS), 9),
        (GameType.NULL, Card(Rank.EIGHT, Suit.SPADES), 8),
        (GameType.NULL, Card(Rank.SEVEN, Suit.HEARTS), 7),
        #
        (GameType.GRAND, Card(Rank.JACK, Suit.CLUBS), 103),
        (GameType.GRAND, Card(Rank.JACK, Suit.SPADES), 102),
        (GameType.GRAND, Card(Rank.JACK, Suit.HEARTS), 101),
        (GameType.GRAND, Card(Rank.JACK, Suit.DIAMONDS), 100),
        (GameType.GRAND, Card(Rank.ACE, Suit.HEARTS), 7),
        (GameType.GRAND, Card(Rank.TEN, Suit.DIAMONDS), 6),
        (GameType.GRAND, Card(Rank.KING, Suit.SPADES), 5),
        (GameType.GRAND, Card(Rank.QUEEN, Suit.HEARTS), 4),
        (GameType.GRAND, Card(Rank.NINE, Suit.HEARTS), 3),
        (GameType.GRAND, Card(Rank.EIGHT, Suit.SPADES), 2),
        (GameType.GRAND, Card(Rank.SEVEN, Suit.HEARTS), 1),
    ]

    for test in test_data:
        assert isko.get_card_effective_rank_value(test[1], test[0]) == test[2]

    with pytest.raises(InvalidGameTypeError):
        isko.get_card_effective_rank_value(Card(Rank.ACE, Suit.DIAMONDS), GameType.PASS)


@dataclass
class IsValidCardPlayTestCase:
    id: str
    game_type: GameType
    hand: list[Card]
    play_card: Card
    first_card: Optional[Card] = None
    expected_result: bool = True


@pytest.mark.parametrize(
    "case",
    [
        IsValidCardPlayTestCase(
            id="card_not_in_hand",
            game_type=GameType.DIAMONDS,
            hand=[Card(Rank.ACE, Suit.DIAMONDS)],
            play_card=Card(Rank.KING, Suit.DIAMONDS),
            expected_result=False,
        ),
        IsValidCardPlayTestCase(
            id="pass",
            game_type=GameType.PASS,
            hand=[Card(Rank.ACE, Suit.DIAMONDS)],
            play_card=Card(Rank.ACE, Suit.DIAMONDS),
            expected_result=False,
        ),
        IsValidCardPlayTestCase(
            id="no_first_card",
            game_type=GameType.DIAMONDS,
            hand=[Card(Rank.ACE, Suit.DIAMONDS)],
            play_card=Card(Rank.ACE, Suit.DIAMONDS),
        ),
        IsValidCardPlayTestCase(
            id="following_trump",
            game_type=GameType.DIAMONDS,
            hand=[Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.JACK, Suit.HEARTS),
            first_card=Card(Rank.KING, Suit.DIAMONDS),
        ),
        IsValidCardPlayTestCase(
            id="not_following_trump",
            game_type=GameType.DIAMONDS,
            hand=[Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.SPADES),
            first_card=Card(Rank.KING, Suit.DIAMONDS),
            expected_result=False,
        ),
        IsValidCardPlayTestCase(
            id="following_suit",
            game_type=GameType.SPADES,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.DIAMONDS),
            first_card=Card(Rank.KING, Suit.DIAMONDS),
        ),
        IsValidCardPlayTestCase(
            id="not_following_suit",
            game_type=GameType.SPADES,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.SPADES),
            first_card=Card(Rank.KING, Suit.DIAMONDS),
            expected_result=False,
        ),
        IsValidCardPlayTestCase(
            id="cannot_follow_suit",
            game_type=GameType.SPADES,
            hand=[Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.SPADES),
            first_card=Card(Rank.SEVEN, Suit.DIAMONDS),
        ),
        IsValidCardPlayTestCase(
            id="null_follow_suit",
            game_type=GameType.NULL,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.DIAMONDS),
            first_card=Card(Rank.KING, Suit.DIAMONDS),
        ),
        IsValidCardPlayTestCase(
            id="null_not_follow_suit",
            game_type=GameType.NULL,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.SPADES),
            first_card=Card(Rank.KING, Suit.DIAMONDS),
            expected_result=False,
        ),
        IsValidCardPlayTestCase(
            id="null_cannot_follow_suit",
            game_type=GameType.NULL,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.SEVEN, Suit.SPADES)],
            play_card=Card(Rank.SEVEN, Suit.DIAMONDS),
            first_card=Card(Rank.KING, Suit.CLUBS),
        ),
        IsValidCardPlayTestCase(
            id="grand_follow_trump_1",
            game_type=GameType.GRAND,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.JACK, Suit.DIAMONDS)],
            play_card=Card(Rank.SEVEN, Suit.DIAMONDS),
            first_card=Card(Rank.JACK, Suit.HEARTS),
            expected_result=False,
        ),
        IsValidCardPlayTestCase(
            id="grand_follow_trump_2",
            game_type=GameType.GRAND,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.JACK, Suit.DIAMONDS)],
            play_card=Card(Rank.JACK, Suit.DIAMONDS),
            first_card=Card(Rank.JACK, Suit.HEARTS),
        ),
        IsValidCardPlayTestCase(
            id="grand_cannot_follow_trump",
            game_type=GameType.GRAND,
            hand=[Card(Rank.SEVEN, Suit.DIAMONDS)],
            play_card=Card(Rank.SEVEN, Suit.DIAMONDS),
            first_card=Card(Rank.JACK, Suit.HEARTS),
        ),
        IsValidCardPlayTestCase(
            id="grand_follow_suit_1",
            game_type=GameType.GRAND,
            hand=[Card(Rank.SEVEN, Suit.HEARTS), Card(Rank.JACK, Suit.DIAMONDS)],
            play_card=Card(Rank.SEVEN, Suit.HEARTS),
            first_card=Card(Rank.EIGHT, Suit.HEARTS),
        ),
        IsValidCardPlayTestCase(
            id="grand_follow_suit_2",
            game_type=GameType.GRAND,
            hand=[Card(Rank.SEVEN, Suit.HEARTS), Card(Rank.JACK, Suit.DIAMONDS)],
            play_card=Card(Rank.JACK, Suit.DIAMONDS),
            first_card=Card(Rank.EIGHT, Suit.HEARTS),
            expected_result=False,
        ),
    ],
    ids=lambda c: c.id,
)
def test_is_valid_card_play(case: IsValidCardPlayTestCase):
    assert case.expected_result == isko.is_valid_card_play(
        Player("test", hand=case.hand), case.play_card, case.first_card, case.game_type
    )


@dataclass
class GameDeclarationTestCase:
    id: str
    player_hand: list[Card]
    skat: tuple[Card, Card]
    bid: int
    type: GameType

    hand: bool = False
    schneider: bool = False
    schwarz: bool = False
    open: bool = False

    expectation: ContextManager[Any] = field(default_factory=nullcontext)
    expected_result: bool = True


@pytest.mark.parametrize(
    "case",
    [
        GameDeclarationTestCase(
            id="suit_no_win_levels",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_invalid_bid",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=17,
            type=GameType.DIAMONDS,
            expectation=pytest.raises(InvalidDeclarationError),
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schneider",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=27,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schwarz",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=36,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schwarz_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=40,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schneider_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schneider=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schwarz_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schneider_schwarz_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schneider=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schwarz_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schneider_schwarz_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schneider=True,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=45,
            type=GameType.DIAMONDS,
            hand=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=46,
            type=GameType.DIAMONDS,
            hand=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schwarz_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            hand=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=54,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=55,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=54,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_schwarz",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=63,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            schwarz=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_schwarz_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=66,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_schwarz_open",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=72,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            schwarz=True,
            open=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_schwarz_open_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=77,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_without_four",
            player_hand=hand_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=63,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_without_four_too_high",
            player_hand=hand_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=66,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_without_four_ignores_skat",
            player_hand=hand_without_four,
            skat=(Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS)),
            bid=63,
            hand=True,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_without_four_includes_skat",
            player_hand=hand_without_four,
            skat=(Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS)),
            bid=63,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="pass",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.PASS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_no_win_levels",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=23,
            type=GameType.NULL,
        ),
        GameDeclarationTestCase(
            id="null_no_win_levels_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=24,
            type=GameType.NULL,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_hand",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=35,
            type=GameType.NULL,
            hand=True,
        ),
        GameDeclarationTestCase(
            id="null_hand",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=36,
            type=GameType.NULL,
            hand=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_ouvert",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=46,
            type=GameType.NULL,
            open=True,
        ),
        GameDeclarationTestCase(
            id="null_ouvert_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=48,
            type=GameType.NULL,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_hand_ouvert",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=59,
            type=GameType.NULL,
            hand=True,
            open=True,
        ),
        GameDeclarationTestCase(
            id="null_hand_ouvert_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=60,
            type=GameType.NULL,
            hand=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=24,
            type=GameType.GRAND,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_assuming_schneider",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=48,
            type=GameType.GRAND,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_assuming_schwarz",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=96,
            type=GameType.GRAND,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_assuming_schwarz_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=99,
            type=GameType.GRAND,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_schneider_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            schneider=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_schwarz_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_schneider_schwarz_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            schneider=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_schwarz_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_no_win_levels_schneider_schwarz_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            schneider=True,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_hand",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=120,
            type=GameType.GRAND,
            hand=True,
        ),
        GameDeclarationTestCase(
            id="grand_hand_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=121,
            type=GameType.GRAND,
            hand=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schwarz_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.GRAND,
            hand=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=144,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=150,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider_open_not_possible",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=54,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider_schwarz",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=168,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
            schwarz=True,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider_schwarz_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=170,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider_schwarz_open",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=192,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
            schwarz=True,
            open=True,
        ),
        GameDeclarationTestCase(
            id="grand_hand_schneider_schwarz_open_too_high",
            player_hand=hand_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=198,
            type=GameType.GRAND,
            hand=True,
            schneider=True,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_without_four",
            player_hand=hand_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=168,
            type=GameType.GRAND,
        ),
        GameDeclarationTestCase(
            id="grand_without_four_too_high",
            player_hand=hand_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=170,
            type=GameType.GRAND,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="grand_without_four_hand_schneider_schwarz_open",
            player_hand=hand_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=264,
            hand=True,
            schneider=True,
            schwarz=True,
            open=True,
            type=GameType.GRAND,
        ),
        GameDeclarationTestCase(
            id="grand_without_four_hand_schneider_schwarz_open_is_max",
            player_hand=hand_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=265,
            hand=True,
            schneider=True,
            schwarz=True,
            open=True,
            type=GameType.GRAND,
            expectation=pytest.raises(InvalidDeclarationError),
        ),
        GameDeclarationTestCase(
            id="grand_hand_without_four_ignores_skat",
            player_hand=hand_without_four,
            skat=(Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS)),
            bid=168,
            hand=True,
            type=GameType.GRAND,
        ),
        GameDeclarationTestCase(
            id="grand_without_four_includes_skat",
            player_hand=hand_without_four,
            skat=(Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS)),
            bid=99,
            type=GameType.GRAND,
            expected_result=False,
        ),
    ],
    ids=lambda c: c.id,
)
def test_is_valid_game_declaration(case: GameDeclarationTestCase):
    declaration = GameDeclaration(
        game_type=case.type,
        hand=case.hand,
        schneider=case.schneider,
        schwarz=case.schwarz,
        open=case.open,
    )

    state = MagicMock()
    state.bid = case.bid
    state.hands = [case.player_hand, [], []]
    state.skat = list(case.skat)
    state.active_player = 0

    with case.expectation:
        result = isko.is_valid_game_declaration(state, declaration)
        assert result == case.expected_result


@dataclass
class TopsTestCase:
    id: str
    game_type: GameType
    cards: list[Card]

    expected_result: int = 0
    expectation: ContextManager[Any] = field(default_factory=nullcontext)


@pytest.mark.parametrize(
    "case",
    [
        TopsTestCase(
            id="no_cards",
            game_type=GameType.DIAMONDS,
            cards=[],
            expectation=pytest.raises(NoCardsError),
        ),
        TopsTestCase(
            id="null",
            game_type=GameType.NULL,
            cards=[
                Card(Rank.JACK, Suit.CLUBS),
            ],
            expectation=pytest.raises(InvalidGameTypeError),
        ),
        TopsTestCase(
            id="pass",
            game_type=GameType.PASS,
            cards=[Card(Rank.JACK, Suit.CLUBS)],
            expectation=pytest.raises(InvalidGameTypeError),
        ),
        TopsTestCase(
            id="suit_with_1",
            game_type=GameType.HEARTS,
            cards=[Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.HEARTS)],
            expected_result=1,
        ),
        TopsTestCase(
            id="suit_without_1",
            game_type=GameType.HEARTS,
            cards=[Card(Rank.JACK, Suit.DIAMONDS), Card(Rank.JACK, Suit.SPADES)],
            expected_result=1,
        ),
        TopsTestCase(
            id="suit_with_2",
            game_type=GameType.HEARTS,
            cards=[Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.SPADES)],
            expected_result=2,
        ),
        TopsTestCase(
            id="suit_without_4",
            game_type=GameType.HEARTS,
            cards=[Card(Rank.ACE, Suit.HEARTS)],
            expected_result=4,
        ),
        TopsTestCase(
            id="suit_with_11",
            game_type=GameType.HEARTS,
            cards=[
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.HEARTS),
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.KING, Suit.HEARTS),
                Card(Rank.QUEEN, Suit.HEARTS),
                Card(Rank.NINE, Suit.HEARTS),
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.SEVEN, Suit.HEARTS),
            ],
            expected_result=11,
        ),
        TopsTestCase(
            id="suit_without_10",
            game_type=GameType.HEARTS,
            cards=[Card(Rank.SEVEN, Suit.HEARTS), Card(Rank.ACE, Suit.SPADES)],
            expected_result=10,
        ),
        TopsTestCase(
            id="suit_without_11",
            game_type=GameType.HEARTS,
            cards=[Card(Rank.ACE, Suit.SPADES)],
            expected_result=11,
        ),
        TopsTestCase(
            id="grand_with_1",
            game_type=GameType.GRAND,
            cards=[Card(Rank.JACK, Suit.CLUBS)],
            expected_result=1,
        ),
        TopsTestCase(
            id="grand_without_1",
            game_type=GameType.GRAND,
            cards=[Card(Rank.JACK, Suit.HEARTS), Card(Rank.JACK, Suit.SPADES)],
            expected_result=1,
        ),
        TopsTestCase(
            id="grand_with_4",
            game_type=GameType.GRAND,
            cards=[
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.ACE, Suit.CLUBS),
            ],
            expected_result=4,
        ),
        TopsTestCase(
            id="grand_without_4",
            game_type=GameType.GRAND,
            cards=[Card(Rank.ACE, Suit.SPADES)],
            expected_result=4,
        ),
    ],
)
def test_tops(case: TopsTestCase):
    with case.expectation:
        result = isko.tops(case.cards, case.game_type)
        assert case.expected_result == result


@dataclass
class TrickWinnerTestCase:
    id: str
    trick: list[Card]
    game_type: GameType
    expected_result: int
    expectation: ContextManager[Any] = field(default_factory=nullcontext)


@pytest.mark.parametrize(
    "case",
    [
        TrickWinnerTestCase(
            id="no_tricks",
            trick=[],
            game_type=GameType.DIAMONDS,
            expected_result=0,
            expectation=pytest.raises(TrickNotFinishedError),
        ),
        TrickWinnerTestCase(
            id="trick_not_finished",
            trick=[Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.JACK, Suit.HEARTS)],
            game_type=GameType.DIAMONDS,
            expected_result=0,
            expectation=pytest.raises(TrickNotFinishedError),
        ),
        TrickWinnerTestCase(
            id="pass",
            trick=[],
            game_type=GameType.PASS,
            expected_result=0,
            expectation=pytest.raises(InvalidGameTypeError),
        ),
        TrickWinnerTestCase(
            id="suit_same_rank",
            trick=[
                Card(Rank.ACE, Suit.CLUBS),
                Card(Rank.ACE, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.SPADES),
            ],
            game_type=GameType.HEARTS,
            expected_result=0,
        ),
        TrickWinnerTestCase(
            id="suit_same_rank_second_trump",
            trick=[
                Card(Rank.ACE, Suit.CLUBS),
                Card(Rank.ACE, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.SPADES),
            ],
            game_type=GameType.SPADES,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="suit_lower_rank",
            trick=[
                Card(Rank.KING, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.DIAMONDS),
            ],
            game_type=GameType.DIAMONDS,
            expected_result=1,
        ),
        TrickWinnerTestCase(
            id="suit_jack",
            trick=[
                Card(Rank.KING, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.DIAMONDS),
            ],
            game_type=GameType.DIAMONDS,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="suit_jack_order",
            trick=[
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.CLUBS),
            ],
            game_type=GameType.DIAMONDS,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="suit_7_8_9",
            trick=[
                Card(Rank.SEVEN, Suit.DIAMONDS),
                Card(Rank.EIGHT, Suit.DIAMONDS),
                Card(Rank.NINE, Suit.DIAMONDS),
            ],
            game_type=GameType.DIAMONDS,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="suit_taking_with_trump",
            trick=[
                Card(Rank.KING, Suit.DIAMONDS),
                Card(Rank.SEVEN, Suit.HEARTS),
                Card(Rank.TEN, Suit.DIAMONDS),
            ],
            game_type=GameType.HEARTS,
            expected_result=1,
        ),
        TrickWinnerTestCase(
            id="null_jack_order",
            trick=[
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.QUEEN, Suit.CLUBS),
                Card(Rank.JACK, Suit.DIAMONDS),
            ],
            game_type=GameType.NULL,
            expected_result=1,
        ),
        TrickWinnerTestCase(
            id="null_ten_order_lower",
            trick=[
                Card(Rank.NINE, Suit.DIAMONDS),
                Card(Rank.EIGHT, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.DIAMONDS),
            ],
            game_type=GameType.NULL,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="null_ten_order_upper",
            trick=[
                Card(Rank.NINE, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.DIAMONDS),
                Card(Rank.QUEEN, Suit.DIAMONDS),
            ],
            game_type=GameType.NULL,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="null_has_no_trump",
            trick=[
                Card(Rank.NINE, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.CLUBS),
            ],
            game_type=GameType.NULL,
            expected_result=1,
        ),
        TrickWinnerTestCase(
            id="grand_has_no_trump_suit",
            trick=[
                Card(Rank.KING, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.CLUBS),
            ],
            game_type=GameType.GRAND,
            expected_result=1,
        ),
        TrickWinnerTestCase(
            id="grand_jack_order_1",
            trick=[
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.SPADES),
            ],
            game_type=GameType.GRAND,
            expected_result=2,
        ),
        TrickWinnerTestCase(
            id="grand_jack_order_2",
            trick=[
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.CLUBS),
            ],
            game_type=GameType.GRAND,
            expected_result=2,
        ),
    ],
    ids=lambda c: c.id,
)
def test_determine_trick_winner(case: TrickWinnerTestCase):
    with case.expectation:
        result = isko.determine_trick_winner(case.trick, case.game_type)
        assert case.expected_result == result


@dataclass
class IsValidBidTestCase:
    id: str
    previous_bids: list[DeclareBid | Listen | Pass]
    player_pos: PlayerPosition
    bid: DeclareBid | Listen | Pass
    bidding_phase: BiddingPhase
    expected_result: bool = True


@pytest.mark.parametrize(
    "case",
    [
        IsValidBidTestCase(
            id="backhand_cannot_bid_first",
            previous_bids=[],
            player_pos=PlayerPosition.BACKHAND,
            bid=DeclareBid(bid=18, player_idx=backhand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="backhand_can_pass_first",
            previous_bids=[],
            player_pos=PlayerPosition.BACKHAND,
            bid=Pass(player_idx=backhand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
        ),
        IsValidBidTestCase(
            id="backhand_cannot_listen_first",
            previous_bids=[],
            player_pos=PlayerPosition.BACKHAND,
            bid=Listen(player_idx=backhand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="forehand_cannot_bid_first",
            previous_bids=[],
            player_pos=PlayerPosition.FOREHAND,
            bid=DeclareBid(bid=18, player_idx=forehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="forehand_can_pass_first",
            previous_bids=[],
            player_pos=PlayerPosition.FOREHAND,
            bid=Pass(player_idx=forehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
        ),
        IsValidBidTestCase(
            id="forehand_cannot_listen_first",
            previous_bids=[],
            player_pos=PlayerPosition.FOREHAND,
            bid=Listen(player_idx=forehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="middlehand_can_declare_first",
            previous_bids=[],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=DeclareBid(bid=24, player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
        ),
        IsValidBidTestCase(
            id="middlehand_cannot_listen_first",
            previous_bids=[],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Listen(player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="middlehand_can_pass_first",
            previous_bids=[],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Pass(player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
        ),
        IsValidBidTestCase(
            id="all_pass",
            previous_bids=[Pass(player_idx=middlehand), Pass(player_idx=backhand)],
            player_pos=PlayerPosition.FOREHAND,
            bid=Pass(player_idx=forehand),
            bidding_phase=BiddingPhase.ForehandBackhand,
        ),
        IsValidBidTestCase(
            id="cannot_declare_invalid_bid",
            previous_bids=[],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=DeclareBid(bid=19, player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="middlehand_backhand_cannot_listen",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
            ],
            player_pos=PlayerPosition.BACKHAND,
            bid=Listen(player_idx=backhand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="middlehand_backhand_bid_must_be_higher",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
            ],
            player_pos=PlayerPosition.BACKHAND,
            bid=DeclareBid(bid=18, player_idx=backhand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="middlehand_backhand_can_bid",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
            ],
            player_pos=PlayerPosition.BACKHAND,
            bid=DeclareBid(bid=20, player_idx=backhand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
        ),
        IsValidBidTestCase(
            id="middlehand_backhand_middlehand_can_listen",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
                DeclareBid(bid=20, player_idx=backhand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Listen(player_idx=middlehand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
        ),
        IsValidBidTestCase(
            id="middlehand_backhand_middlehand_can_pass",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
                DeclareBid(bid=20, player_idx=backhand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Pass(player_idx=middlehand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
        ),
        IsValidBidTestCase(
            id="middlehand_backhand_middlehand_cannot_declare",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
                DeclareBid(bid=20, player_idx=backhand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=DeclareBid(bid=22, player_idx=middlehand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="forehand_middlehand_cannot_listen",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Listen(player_idx=forehand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Listen(player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="forehand_middlehand_can_pass",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Listen(player_idx=forehand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Pass(player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
        ),
        IsValidBidTestCase(
            id="forehand_middlehand_can_bid",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Listen(player_idx=forehand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=DeclareBid(bid=20, player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
        ),
        IsValidBidTestCase(
            id="forehand_middlehand_bid_must_be_higher",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Listen(player_idx=forehand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=DeclareBid(bid=18, player_idx=middlehand),
            bidding_phase=BiddingPhase.ForehandMiddlehand,
            expected_result=False,
        ),
        IsValidBidTestCase(
            id="cannot_pass_if_bid_before_and_others_passed",
            previous_bids=[
                DeclareBid(bid=18, player_idx=middlehand),
                Pass(player_idx=forehand),
                Pass(player_idx=backhand),
            ],
            player_pos=PlayerPosition.MIDDLEHAND,
            bid=Pass(player_idx=middlehand),
            bidding_phase=BiddingPhase.MiddlehandBackhand,
            expected_result=False,
        ),
    ],
    ids=lambda c: c.id,
)
def test_is_valid_bid(case: IsValidBidTestCase):
    game = GameState.from_random_deal(isko, backhand)
    for bid in case.previous_bids:
        previous_state = {
            "active_player": game.active_player,
            "bidding_phase": game.bidding_phase,
            "bid": game.bid,
            "phase": game.phase,
            "declarer_idx": game.declarer_idx,
        }

        game.apply_action(bid)

        # Randomly undo an action to test restoration of state
        if random.random() > 0.5:
            game.undo_action()
            assert previous_state["active_player"] == game.active_player
            assert previous_state["bidding_phase"] == game.bidding_phase
            assert previous_state["bid"] == game.bid
            assert previous_state["phase"] == game.phase
            assert previous_state["declarer_idx"] == game.declarer_idx
            game.apply_action(bid)

    assert game.bidding_phase == case.bidding_phase

    result = isko.is_valid_bid(game, case.bid)
    assert case.expected_result == result


@dataclass
class GetNextValidBidTestCase:
    id: str
    current_bid: Optional[int]
    expected_result: int
    expectation: ContextManager[Any] = field(default_factory=nullcontext)


@pytest.mark.parametrize(
    "case",
    [
        GetNextValidBidTestCase(id="start_at_18", current_bid=None, expected_result=18),
        GetNextValidBidTestCase(id="after_18", current_bid=18, expected_result=20),
        GetNextValidBidTestCase(
            id="highest_bid",
            current_bid=264,
            expected_result=0,
            expectation=pytest.raises(NoHigherBidPossible),
        ),
    ],
    ids=lambda c: c.id,
)
def test_get_next_valid_bid(case: GetNextValidBidTestCase):
    with case.expectation:
        assert case.expected_result == isko.get_next_valid_bid(case.current_bid)
