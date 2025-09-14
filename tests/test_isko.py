from skaty.cards import Card, Rank, Suit
from skaty.isko import ISkO
from skaty.rules import GameType


def test_get_card_effective_rank_value():
    isko = ISkO()
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
    ]

    for test in test_data:
        isko.set_game_type(test[0])
        assert isko.get_card_effective_rank_value(test[1]) == test[2]


def test_determine_trick_winner():
    isko = ISkO()

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
        isko.set_game_type(test[0])
        assert isko.determine_trick_winner(test[1]) == test[2]
