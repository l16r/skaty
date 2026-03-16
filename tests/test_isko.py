from contextlib import nullcontext
from dataclasses import dataclass, field
from typing import Any, ContextManager, Optional
import pytest
from skaty.cards import Card, Rank, Suit
from skaty.exceptions import InvalidDeclarationError, InvalidGameTypeError
from skaty.game_state import GameState
from skaty.isko import ISkO
from skaty.player import Player
from skaty.rules import (
    BiddingPhase,
    DealCards,
    DeclareBid,
    DeclareGame,
    GamePhase,
    GameType,
    Listen,
    Pass,
    PlayCard,
    PlayerPosition,
)

isko = ISkO()
player_with_one = Player("with one", hand=[Card(Rank.JACK, Suit.CLUBS)])
player_without_four = Player("without four", hand=[Card(Rank.ACE, Suit.DIAMONDS)])


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
    player: Player
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
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_invalid_bid",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=17,
            type=GameType.DIAMONDS,
            expectation=pytest.raises(InvalidDeclarationError),
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schneider",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=27,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schwarz",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=36,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schwarz_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=40,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schneider_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schneider=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schwarz_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schneider_schwarz_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schneider=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_open_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schwarz_open_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_schneider_schwarz_open_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            schneider=True,
            schwarz=True,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schwarz_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=40,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_no_win_levels_assuming_schwarz_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=40,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=45,
            type=GameType.DIAMONDS,
            hand=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=46,
            type=GameType.DIAMONDS,
            hand=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schwarz_not_possible",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.DIAMONDS,
            hand=True,
            schwarz=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=54,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=55,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_open_not_possible",
            player=player_with_one,
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
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=63,
            type=GameType.DIAMONDS,
            hand=True,
            schneider=True,
            schwarz=True,
        ),
        GameDeclarationTestCase(
            id="suit_hand_schneider_schwarz_too_high",
            player=player_with_one,
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
            player=player_with_one,
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
            player=player_with_one,
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
            player=player_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=63,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_without_four_too_high",
            player=player_without_four,
            skat=(Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=66,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="suit_hand_without_four_ignores_skat",
            player=player_without_four,
            skat=(Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS)),
            bid=63,
            hand=True,
            type=GameType.DIAMONDS,
        ),
        GameDeclarationTestCase(
            id="suit_without_four_includes_skat",
            player=player_without_four,
            skat=(Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.DIAMONDS)),
            bid=63,
            type=GameType.DIAMONDS,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="pass",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=18,
            type=GameType.PASS,
            expectation=pytest.raises(InvalidGameTypeError),
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_no_win_levels",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=23,
            type=GameType.NULL,
        ),
        GameDeclarationTestCase(
            id="null_no_win_levels_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=24,
            type=GameType.NULL,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_hand",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=35,
            type=GameType.NULL,
            hand=True,
        ),
        GameDeclarationTestCase(
            id="null_hand",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=36,
            type=GameType.NULL,
            hand=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_ouvert",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=46,
            type=GameType.NULL,
            open=True,
        ),
        GameDeclarationTestCase(
            id="null_ouvert_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=48,
            type=GameType.NULL,
            open=True,
            expected_result=False,
        ),
        GameDeclarationTestCase(
            id="null_hand_ouvert",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=59,
            type=GameType.NULL,
            hand=True,
            open=True,
        ),
        GameDeclarationTestCase(
            id="null_hand_ouvert_too_high",
            player=player_with_one,
            skat=(Card(Rank.ACE, Suit.DIAMONDS), Card(Rank.NINE, Suit.CLUBS)),
            bid=60,
            type=GameType.NULL,
            hand=True,
            open=True,
            expected_result=False,
        ),
    ],
    ids=lambda c: c.id,
)
def test_is_valid_game_declaration(case: GameDeclarationTestCase):
    with case.expectation:
        result = isko.is_valid_game_declaration(
            case.player,
            case.skat,
            case.bid,
            case.type,
            case.hand,
            case.schneider,
            case.schwarz,
            case.open,
        )
        assert result == case.expected_result


def test_tops():
    test_cases = [
        (
            GameType.NULL,
            [
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.ACE, Suit.CLUBS),
            ],
            0,
        ),
        (
            GameType.PASS,
            [Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.HEARTS)],
            0,
        ),
        (
            GameType.HEARTS,
            [Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.HEARTS)],
            1,
        ),
        (
            GameType.HEARTS,
            [Card(Rank.JACK, Suit.CLUBS), Card(Rank.JACK, Suit.SPADES)],
            2,
        ),
        (
            GameType.HEARTS,
            [Card(Rank.JACK, Suit.DIAMONDS), Card(Rank.JACK, Suit.SPADES)],
            1,
        ),
        (
            GameType.HEARTS,
            [
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
            11,
        ),
        (
            GameType.HEARTS,
            [
                Card(Rank.SEVEN, Suit.HEARTS),
            ],
            10,
        ),
        (
            GameType.HEARTS,
            [Card(Rank.ACE, Suit.SPADES)],
            11,
        ),
        (
            GameType.GRAND,
            [
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.ACE, Suit.CLUBS),
            ],
            4,
        ),
        (
            GameType.GRAND,
            [
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.ACE, Suit.CLUBS),
            ],
            1,
        ),
        (
            GameType.GRAND,
            [Card(Rank.ACE, Suit.SPADES)],
            4,
        ),
    ]
    ruleset = ISkO()

    for test in test_cases:
        assert ruleset.tops(test[1], test[0]) == test[2]


def test_is_valid_bid():
    p1 = Player("forehand")
    p2 = Player("middlehand")
    p3 = Player("backhand")
    test_data = [
        (
            [
                (p2, DeclareBid(18)),
                (p1, Listen()),
                (p2, DeclareBid(20)),
                (p1, Pass()),
                (p3, Pass()),
            ],
            p1,
            Pass(),
            PlayerPosition.MIDDLEHAND,
            BiddingPhase.MiddlehandBackhand,
            False,
        ),
        (
            [
                (p2, Pass()),
                (p1, Pass()),
            ],
            p3,
            Pass(),
            PlayerPosition.BACKHAND,
            BiddingPhase.ForehandBackhand,
            True,
        ),
        (
            [
                (p2, DeclareBid(18)),
                (p1, Listen()),
                (p2, DeclareBid(20)),
                (p1, Pass()),
                (p3, Pass()),
            ],
            p1,
            Pass(),
            PlayerPosition.FOREHAND,
            BiddingPhase.MiddlehandBackhand,
            False,
        ),
        (
            [
                (p2, DeclareBid(18)),
                (p1, Listen()),
                (p2, DeclareBid(20)),
                (p1, Pass()),
                (p3, Pass()),
            ],
            p1,
            DeclareBid(22),
            PlayerPosition.FOREHAND,
            BiddingPhase.MiddlehandBackhand,
            False,
        ),
        (
            [
                (p2, DeclareBid(18)),
                (p1, Listen()),
                (p2, DeclareBid(20)),
                (p1, Pass()),
                (p3, Pass()),
            ],
            p2,
            DeclareBid(20),
            PlayerPosition.FOREHAND,
            BiddingPhase.MiddlehandBackhand,
            False,
        ),
        (
            [
                (p2, Pass()),
                (p3, DeclareBid(18)),
                (p1, Pass()),
            ],
            p3,
            DeclareBid(18),
            PlayerPosition.BACKHAND,
            BiddingPhase.ForehandBackhand,
            False,
        ),
        (
            [
                (p2, Pass()),
                (p3, DeclareBid(18)),
                (p1, Pass()),
            ],
            p3,
            DeclareBid(20),
            PlayerPosition.BACKHAND,
            BiddingPhase.ForehandBackhand,
            True,
        ),
        (
            [
                (p2, Pass()),
                (p3, DeclareBid(18)),
                (p1, Pass()),
            ],
            p3,
            Listen(),
            PlayerPosition.BACKHAND,
            BiddingPhase.ForehandBackhand,
            False,
        ),
        (
            [],
            p2,
            Pass(),
            PlayerPosition.MIDDLEHAND,
            BiddingPhase.ForehandMiddlehand,
            True,
        ),
        (
            [],
            p2,
            Listen(),
            PlayerPosition.MIDDLEHAND,
            BiddingPhase.ForehandMiddlehand,
            False,
        ),
        (
            [],
            p2,
            DeclareBid(18),
            PlayerPosition.MIDDLEHAND,
            BiddingPhase.ForehandMiddlehand,
            True,
        ),
        (
            [],
            p2,
            DeclareBid(19),
            PlayerPosition.MIDDLEHAND,
            BiddingPhase.ForehandMiddlehand,
            False,
        ),
        (
            [],
            p2,
            DeclareBid(-1),
            PlayerPosition.MIDDLEHAND,
            BiddingPhase.ForehandMiddlehand,
            False,
        ),
    ]

    ruleset = ISkO()

    for test in test_data:
        assert (
            ruleset.is_valid_bid(test[1], test[2], test[0], test[3], test[4]) == test[5]
        )


def test_is_valid_action():
    test_data = [
        (DealCards(), GamePhase.PRE_DEAL, True),
        (DealCards(), GamePhase.PRE_DEAL, True),
        (PlayCard(Card(Rank.ACE, Suit.CLUBS)), GamePhase.DECLARATION, False),
        (DeclareGame(GameType.CLUBS, False), GamePhase.DECLARATION, True),
    ]

    ruleset = ISkO()

    for test in test_data:
        assert ruleset.is_valid_action(test[0], test[1]) == test[2]


def test_calculate_game_score():
    ruleset = ISkO()
    p1 = Player("p1")
    p2 = Player("p2")
    p3 = Player("p3")

    p1_with_3 = Player("p1")
    p1_with_3.add_cards(
        [
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.ACE, Suit.DIAMONDS),
        ]
    )

    p1_without_2 = Player("p1")
    p1_without_2.add_cards([Card(Rank.JACK, Suit.HEARTS)])

    p1_with_6_diamonds = Player("p1")
    p1_with_6_diamonds.add_cards(
        [
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.JACK, Suit.DIAMONDS),
            Card(Rank.ACE, Suit.DIAMONDS),
            Card(Rank.TEN, Suit.DIAMONDS),
            Card(Rank.QUEEN, Suit.DIAMONDS),
        ]
    )

    p1_without_11_diamonds = Player("p1")
    p1_without_11_diamonds.add_cards([Card(Rank.ACE, Suit.CLUBS)])

    players = [p1, p2, p3]
    # Each test tuple: (players, declarer, points, tricks, game_type, bid, skat, hand, schneider_announced, schwarz_announced, ouvert, expected_score)
    test_data = [
        # Declarer wins a suit game
        (
            players,
            0,
            {p1: 61, p2: 30, p3: 29},
            [(None, p1)] * 7 + [(None, p2)] * 2 + [(None, p3)],
            GameType.DIAMONDS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            18,
        ),
        # Declarer loses a suit game
        (
            players,
            0,
            {p1: 60, p2: 30, p3: 30},
            [(None, p1)] * 7 + [(None, p2)] * 2 + [(None, p3)],
            GameType.DIAMONDS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            -36,
        ),
        # Null game, declarer wins
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            23,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            23,
        ),
        # Null game, declarer loses
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p1)] + [(None, p2)] * 4 + [(None, p3)] * 5,
            GameType.NULL,
            23,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            -46,
        ),
        # Null game, declarer loses (overbid)
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            24,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            -46,
        ),
        # Null hand
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            35,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            False,
            False,
            False,
            35,
        ),
        # Null ouvert
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            46,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            True,
            46,
        ),
        # Null ouvert
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            46,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            True,
            46,
        ),
        # Null hand ouvert
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            59,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            False,
            False,
            True,
            59,
        ),
        # Null hand ouvert (overbid)
        (
            players,
            0,
            {p1: 0, p2: 60, p3: 60},
            [(None, p2)] * 5 + [(None, p3)] * 5,
            GameType.NULL,
            60,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            False,
            False,
            True,
            -118,
        ),
        # Suit game without modifiers
        (
            [p1_with_3, p2, p3],
            0,
            {p1_with_3: 61, p2: 29, p3: 30},
            [(None, p1_with_3)] * 7 + [(None, p3)] * 3,
            GameType.DIAMONDS,
            36,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            36,
        ),
        # Suit game without modifiers
        (
            [p1_with_3, p2, p3],
            0,
            {p1_with_3: 61, p2: 29, p3: 30},
            [(None, p1_with_3)] * 7 + [(None, p3)] * 3,
            GameType.DIAMONDS,
            36,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            36,
        ),
        # Suit game without modifiers (overbid)
        (
            [p1_with_3, p2, p3],
            0,
            {p1_with_3: 61, p2: 29, p3: 30},
            [(None, p1_with_3)] * 7 + [(None, p3)] * 3,
            GameType.DIAMONDS,
            40,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            -72,
        ),
        # Suit game without modifiers (lost)
        (
            [p1_with_3, p2, p3],
            0,
            {p1_with_3: 60, p2: 30, p3: 30},
            [(None, p1_with_3)] * 7 + [(None, p3)] * 3,
            GameType.DIAMONDS,
            36,
            (Card(Rank.ACE, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            -72,
        ),
        # Grand game with 4
        (
            [p1_with_3, p2, p3],
            0,
            {p1_with_3: 61, p2: 30, p3: 29},
            [(None, p1_with_3)] * 7 + [(None, p3)] * 3,
            GameType.GRAND,
            120,
            (Card(Rank.JACK, Suit.DIAMONDS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            120,
        ),
        # Grand game without 2
        (
            [p1_without_2, p2, p3],
            0,
            {p1_without_2: 61, p2: 30, p3: 29},
            [(None, p1_without_2)] * 7 + [(None, p3)] * 3,
            GameType.GRAND,
            72,
            (Card(Rank.JACK, Suit.DIAMONDS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            72,
        ),
        # Schneider achieved
        (
            players,
            0,
            {p1: 90, p2: 15, p3: 15},
            [(None, p1)] * 7 + [(None, p3)] * 3,
            GameType.CLUBS,
            36,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            36,
        ),
        # Schneider for opposition achieved
        (
            players,
            0,
            {p1: 30, p2: 10, p3: 80},
            [(None, p1)] * 7 + [(None, p3)] * 3,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            False,
            False,
            False,
            False,
            -72,
        ),
        # Hand
        (
            players,
            0,
            {p1: 61, p2: 29, p3: 30},
            [(None, p1)] * 7 + [(None, p3)] * 3,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            False,
            False,
            False,
            36,
        ),
        # Hand, Schneider announced
        (
            players,
            0,
            {p1: 90, p2: 10, p3: 20},
            [(None, p1)] * 7 + [(None, p3)] * 3,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            False,
            False,
            60,
        ),
        # Hand, Schneider announced, but not reached
        (
            players,
            0,
            {p1: 89, p2: 11, p3: 20},
            [(None, p1)] * 7 + [(None, p3)] * 3,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            False,
            False,
            -96,
        ),
        # Hand, Schneider announced, but opposition played Schneider
        (
            players,
            0,
            {p1: 30, p2: 10, p3: 80},
            [(None, p1)] * 3 + [(None, p3)] * 7,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            False,
            False,
            -120,
        ),
        # Hand, Schwarz announced
        (
            players,
            0,
            {p1: 120, p2: 0, p3: 0},
            [(None, p1)] * 10,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            False,
            84,
        ),
        # Hand, Schwarz announced, but not reached, still played Schneider
        (
            players,
            0,
            {p1: 120, p2: 0, p3: 0},
            [(None, p1)] * 9 + [(None, p3)],
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            False,
            -144,
        ),
        # Hand, Schwarz announced, but not reached, no Schneider
        (
            players,
            0,
            {p1: 61, p2: 29, p3: 31},
            [(None, p1)] * 9 + [(None, p3)],
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            False,
            -120,
        ),
        # Hand, Schneider announced, but opposition played Schneider
        (
            players,
            0,
            {p1: 30, p2: 10, p3: 80},
            [(None, p1)] * 3 + [(None, p3)] * 7,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            False,
            -144,
        ),
        # Open
        (
            players,
            0,
            {p1: 120, p2: 0, p3: 0},
            [(None, p1)] * 10,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            True,
            96,
        ),
        # Open, no schwarz
        (
            players,
            0,
            {p1: 120, p2: 0, p3: 0},
            [(None, p1)] * 9 + [(None, p3)],
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            True,
            -168,
        ),
        # Open, no schwarz, no schneider
        (
            players,
            0,
            {p1: 89, p2: 21, p3: 10},
            [(None, p1)] * 7 + [(None, p3)] * 3,
            GameType.CLUBS,
            18,
            (Card(Rank.JACK, Suit.CLUBS), Card(Rank.TEN, Suit.HEARTS)),
            True,
            True,
            True,
            True,
            -144,
        ),
    ]

    for (
        players,
        declarer,
        points,
        tricks,
        game_type,
        bid,
        skat,
        hand,
        schneider_announced,
        schwarz_announced,
        ouvert,
        expected_score,
    ) in test_data:
        score = ruleset.calculate_game_score(
            players,
            declarer,
            points,
            tricks,
            game_type,
            bid,
            skat,
            hand,
            schneider_announced,
            schwarz_announced,
            ouvert,
        )
        assert score == expected_score


def test_get_valid_actions():
    p1 = Player("p1")
    p2 = Player("p2")
    p3 = Player("p3")
    players = [p1, p2, p3]
    ruleset = ISkO()
    game = GameState(players, ruleset, 2)

    assert list(game.get_valid_actions(p1)) == []
    assert list(game.get_valid_actions(p2)) == []
    assert set(game.get_valid_actions(p3)) == {DealCards()}

    game.apply_action(p3, DealCards())
    # Not active
    assert list(game.get_valid_actions(p1)) == []
    assert list(game.get_valid_actions(p3)) == []
    # Active (declarer)
    assert set(game.get_valid_actions(p2)) == {Pass(), DeclareBid(18)}

    game.apply_action(p2, DeclareBid(18))
    # Not active
    assert list(game.get_valid_actions(p2)) == []
    assert list(game.get_valid_actions(p3)) == []
    # Active (listener)
    assert set(game.get_valid_actions(p1)) == {Pass(), Listen()}

    game.apply_action(p1, Listen())
    # Not active
    assert list(game.get_valid_actions(p1)) == []
    assert list(game.get_valid_actions(p3)) == []
    # Active (listener)
    assert set(game.get_valid_actions(p2)) == {Pass(), DeclareBid(20)}
