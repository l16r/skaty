from skaty.cards import Card, Rank, Suit, create_deck, shuffle_deck
from skaty.exceptions import InvalidGameStateError, InvalidPlayError
from skaty.isko import ISkO
from skaty.rules import GameType
from skaty.trick import Trick

import pytest


def test_eq():
    non_card = object()
    c1 = Card(Rank.ACE, Suit.SPADES)
    c2 = Card(Rank.JACK, Suit.CLUBS)
    c3 = Card(Rank.JACK, Suit.CLUBS)

    assert c1 != c2
    assert c2 == c3
    assert c1 != non_card


def test_create_deck():
    deck = create_deck()
    # A Skat deck contains exactly 32 cards
    assert len(deck) == 32
    # Check for unique cards
    assert len(set(deck)) == 32


def test_shuffle_deck():
    deck = create_deck()
    shuffled = shuffle_deck(deck)
    # All cards must still be present and unique
    assert len(shuffled) == len(deck)
    assert set(shuffled) == set(deck)

    # Test how many cards are still in place (flaky). This could be done better by shuffling multiple times and measuring the shift.
    in_place = 0
    for i in range(len(deck)):
        if deck[i] == shuffled[i]:
            in_place += 1
    # At least 7 cards should move
    assert in_place < len(deck) - 6


def test_trick_points():
    test_data = [
        (
            [
                Card(Rank.ACE, Suit.CLUBS),
                Card(Rank.SEVEN, Suit.DIAMONDS),
                Card(Rank.KING, Suit.CLUBS),
            ],
            15,
        ),
        (
            [
                Card(Rank.SEVEN, Suit.CLUBS),
                Card(Rank.EIGHT, Suit.SPADES),
                Card(Rank.NINE, Suit.HEARTS),
            ],
            0,
        ),
        (
            [
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.QUEEN, Suit.HEARTS),
            ],
            7,
        ),
        (
            [
                Card(Rank.TEN, Suit.DIAMONDS),
                Card(Rank.NINE, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.SPADES),
            ],
            21,
        ),
        (
            [],
            0,
        ),
    ]

    for test in test_data:
        trick = Trick()
        for c in test[0]:
            trick.add_card(c)
        assert trick.get_trick_points() == test[1]

    # Exception check
    trick = Trick()
    for c in test_data[0][0]:
        trick.add_card(c)

    with pytest.raises(InvalidGameStateError):
        trick.add_card(Card(Rank.SEVEN, Suit.HEARTS))


def test_trick_first_card():
    t = Trick()
    assert t.first_card is None
    card = Card(Rank.JACK, Suit.CLUBS)
    t.add_card(card)
    assert t.first_card is card
    t.add_card(Card(Rank.ACE, Suit.DIAMONDS))
    assert t.first_card is card


def test_trick_get_winner():
    t = Trick()
    with pytest.raises(InvalidGameStateError):
        t.get_winner(ISkO())
