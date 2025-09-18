import pytest
from skaty import isko
from skaty.cards import Card, Rank, Suit
from skaty.exceptions import InvalidPlayError
from skaty.isko import ISkO
from skaty.player import Player
from skaty.rules import GameType


def test_get_card_effective_rank_value():
    ruleset = ISkO()
    test_data = [
        (GameType.PASS, Card(Rank.JACK, Suit.CLUBS), 0),
        #
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
        ruleset.set_game_type(test[0])
        assert ruleset.get_card_effective_rank_value(test[1]) == test[2]


def test_determine_trick_winner():
    ruleset = ISkO()
    test_data = [
        (
            GameType.HEARTS,
            [
                Card(Rank.QUEEN, Suit.HEARTS),
                Card(Rank.KING, Suit.HEARTS),
                Card(Rank.JACK, Suit.CLUBS),
            ],
            2,
        ),
        (
            GameType.HEARTS,
            [
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.KING, Suit.HEARTS),
                Card(Rank.ACE, Suit.HEARTS),
            ],
            2,
        ),
        (
            GameType.HEARTS,
            [
                Card(Rank.NINE, Suit.HEARTS),
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.SEVEN, Suit.HEARTS),
            ],
            0,
        ),
        (
            GameType.HEARTS,
            [
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.QUEEN, Suit.HEARTS),
                Card(Rank.KING, Suit.HEARTS),
            ],
            0,
        ),
        (
            GameType.HEARTS,
            [
                Card(Rank.KING, Suit.HEARTS),
                Card(Rank.ACE, Suit.HEARTS),
                Card(Rank.SEVEN, Suit.HEARTS),
            ],
            1,
        ),
        (
            GameType.GRAND,
            [
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.HEARTS),
            ],
            1,
        ),
        (
            GameType.GRAND,
            [
                Card(Rank.JACK, Suit.SPADES),
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.CLUBS),
            ],
            2,
        ),
        (
            GameType.GRAND,
            [
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.SPADES),
            ],
            2,
        ),
        (
            GameType.DIAMONDS,
            [
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.ACE, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.HEARTS),
            ],
            1,
        ),
        (
            GameType.DIAMONDS,
            [
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.ACE, Suit.CLUBS),
                Card(Rank.TEN, Suit.HEARTS),
            ],
            2,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.JACK, Suit.SPADES),
            ],
            0,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.ACE, Suit.DIAMONDS),
                Card(Rank.TEN, Suit.HEARTS),
            ],
            2,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.ACE, Suit.CLUBS),
                Card(Rank.TEN, Suit.HEARTS),
            ],
            2,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.NINE, Suit.HEARTS),
                Card(Rank.EIGHT, Suit.HEARTS),
                Card(Rank.SEVEN, Suit.HEARTS),
            ],
            0,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.QUEEN, Suit.HEARTS),
                Card(Rank.KING, Suit.HEARTS),
            ],
            2,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.KING, Suit.HEARTS),
                Card(Rank.ACE, Suit.HEARTS),
                Card(Rank.SEVEN, Suit.HEARTS),
            ],
            1,
        ),
        (
            GameType.NULL,
            [
                Card(Rank.TEN, Suit.HEARTS),
                Card(Rank.JACK, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.HEARTS),
            ],
            2,
        ),
    ]

    for test in test_data:
        ruleset.set_game_type(test[0])
        assert ruleset.determine_trick_winner(test[1]) == test[2]


def test_is_valid_card_play():
    test_data = [
        (
            GameType.DIAMONDS,  # Game type
            [
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.SEVEN, Suit.DIAMONDS),
            ],  # Player.hand
            Card(Rank.ACE, Suit.DIAMONDS),  # First card in trick
            Card(Rank.JACK, Suit.CLUBS),  # Second card in trick
            True,  # Expected result
        ),
        (
            GameType.DIAMONDS,
            [],
            Card(Rank.TEN, Suit.SPADES),
            Card(Rank.JACK, Suit.CLUBS),
            False,
        ),
        (
            GameType.DIAMONDS,
            [Card(Rank.JACK, Suit.CLUBS)],
            Card(Rank.TEN, Suit.SPADES),
            Card(Rank.JACK, Suit.CLUBS),
            True,
        ),
        (
            GameType.DIAMONDS,
            [Card(Rank.JACK, Suit.CLUBS), Card(Rank.SEVEN, Suit.DIAMONDS)],
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.JACK, Suit.CLUBS),
            True,
        ),
        (
            GameType.DIAMONDS,
            [Card(Rank.KING, Suit.CLUBS), Card(Rank.SEVEN, Suit.DIAMONDS)],
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.SEVEN, Suit.DIAMONDS),
            True,
        ),
        (
            GameType.SPADES,
            [Card(Rank.SEVEN, Suit.DIAMONDS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.SEVEN, Suit.DIAMONDS),
            False,
        ),
        (
            GameType.SPADES,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.ACE, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            True,
        ),
        (
            GameType.GRAND,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            True,
        ),
        (
            GameType.GRAND,
            [Card(Rank.JACK, Suit.CLUBS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.SEVEN, Suit.SPADES),
            False,
        ),
        (
            GameType.NULL,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            False,
        ),
        (
            GameType.NULL,
            [Card(Rank.JACK, Suit.CLUBS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.SEVEN, Suit.SPADES),
            True,
        ),
        (
            GameType.PASS,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.JACK, Suit.HEARTS),
            False,
        ),
        (
            GameType.GRAND,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            None,
            Card(Rank.JACK, Suit.HEARTS),
            True,
        ),
        (
            GameType.DIAMONDS,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            None,
            Card(Rank.SEVEN, Suit.SPADES),
            True,
        ),
        (
            GameType.SPADES,
            [Card(Rank.JACK, Suit.HEARTS), Card(Rank.SEVEN, Suit.SPADES)],
            None,
            Card(Rank.SEVEN, Suit.SPADES),
            True,
        ),
    ]
    ruleset = ISkO()

    for test in test_data:
        p = Player("test", test[1])
        ruleset.set_game_type(test[0])
        assert ruleset.is_valid_card_play(p, test[3], test[2]) == test[4]


def test_is_valid_game_declaration():
    test_cases = [
        (
            18,  # bid
            GameType.DIAMONDS,  # Game type
            False,  # hand
            False,  # schneider announced
            False,  # schwarz announced
            False,  # open
            True,  # hand available
            True,  # expected
        ),
        (9, GameType.DIAMONDS, False, False, False, False, False, False),
        (-1, GameType.GRAND, False, False, False, False, False, False),
        (-1, GameType.PASS, False, False, False, False, False, True),
        (18, GameType.PASS, False, False, False, False, False, True),
        (18, GameType.DIAMONDS, False, False, False, False, False, True),
        (24, GameType.DIAMONDS, True, False, False, False, True, True),
        (18, GameType.DIAMONDS, False, False, False, False, False, True),
        (18, GameType.DIAMONDS, False, False, False, False, False, True),
        #
        (23, GameType.NULL, False, False, False, False, False, True),
        (35, GameType.NULL, True, False, False, False, True, True),
        (35, GameType.NULL, True, True, True, True, True, True),
        (46, GameType.NULL, False, False, False, True, False, True),
        (59, GameType.NULL, True, False, False, True, True, True),
        (60, GameType.NULL, True, False, False, True, True, False),
    ]
    rule_set = ISkO()

    for test in test_cases:
        assert (
            rule_set.is_valid_game_declaration(
                Player("test"),
                test[0],
                test[1],
                test[2],
                test[3],
                test[4],
                test[5],
                test[6],
            )
            == test[7]
        )

    test_cases_exceptions = [
        (
            18,  # bid
            GameType.DIAMONDS,  # Game type
            True,  # hand
            False,  # schneider announced
            False,  # schwarz announced
            False,  # open
            False,  # hand available
        ),
        (18, GameType.DIAMONDS, True, True, False, False, False),
        (18, GameType.DIAMONDS, True, True, True, False, False),
        (18, GameType.DIAMONDS, False, False, False, True, False),
        (18, GameType.DIAMONDS, False, False, True, False, False),
        (18, GameType.DIAMONDS, False, True, False, False, False),
    ]

    for test in test_cases_exceptions:
        with pytest.raises(InvalidPlayError):
            rule_set.is_valid_game_declaration(
                Player("test"),
                test[0],
                test[1],
                test[2],
                test[3],
                test[4],
                test[5],
                test[6],
            )


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
        ruleset.set_game_type(test[0])
        assert ruleset.tops(test[1]) == test[2]
