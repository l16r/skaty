from skaty.cards import Card, Rank, Suit, create_deck, shuffle_deck
from skaty.player import Player
from skaty.trick import Trick


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
        )
    ]

    for test in test_data:
        trick = Trick()
        for c in test[0]:
            trick.add_card(c, Player("test"))
        assert trick.getTrickPoints() == test[1]
