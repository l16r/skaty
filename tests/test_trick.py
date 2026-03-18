from dataclasses import dataclass
import pytest
from skaty.cards import Card, Rank, Suit
from skaty.exceptions import (
    TrickFinishedError,
    TrickNotFinishedError,
)
from skaty.isko import ISkO
from skaty.rules import GameType
from skaty.trick import Trick


@dataclass
class TrickPointTestCase:
    cards: list[Card]
    expected_result: int


@pytest.mark.parametrize(
    "case",
    [
        TrickPointTestCase(
            cards=[
                Card(Rank.ACE, Suit.CLUBS),
                Card(Rank.SEVEN, Suit.DIAMONDS),
                Card(Rank.KING, Suit.CLUBS),
            ],
            expected_result=15,
        ),
        TrickPointTestCase(
            cards=[
                Card(Rank.SEVEN, Suit.CLUBS),
                Card(Rank.EIGHT, Suit.SPADES),
                Card(Rank.NINE, Suit.HEARTS),
            ],
            expected_result=0,
        ),
        TrickPointTestCase(
            cards=[
                Card(Rank.JACK, Suit.HEARTS),
                Card(Rank.JACK, Suit.CLUBS),
                Card(Rank.QUEEN, Suit.HEARTS),
            ],
            expected_result=7,
        ),
        TrickPointTestCase(
            cards=[
                Card(Rank.TEN, Suit.DIAMONDS),
                Card(Rank.NINE, Suit.DIAMONDS),
                Card(Rank.ACE, Suit.SPADES),
            ],
            expected_result=21,
        ),
        TrickPointTestCase(
            cards=[],
            expected_result=0,
        ),
    ],
)
def test_get_trick_points(case: TrickPointTestCase):
    t = Trick()
    for c in case.cards:
        t.add_card(c)

    assert case.expected_result == t.get_trick_points()


def test_trick_first_card():
    t = Trick()
    assert t.first_card is None
    card = Card(Rank.JACK, Suit.CLUBS)
    t.add_card(card)
    assert t.first_card is card
    t.add_card(Card(Rank.ACE, Suit.DIAMONDS))
    assert t.first_card is card


def test_cannot_add_to_finished_trick():
    t = Trick()
    t.add_card(Card(Rank.JACK, Suit.CLUBS))
    t.add_card(Card(Rank.KING, Suit.CLUBS))
    t.add_card(Card(Rank.SEVEN, Suit.CLUBS))
    with pytest.raises(TrickFinishedError):
        t.add_card(Card(Rank.SEVEN, Suit.HEARTS))


def test_trick_get_winner():
    t = Trick()
    with pytest.raises(TrickNotFinishedError):
        t.get_winner(ISkO(), GameType.DIAMONDS)
