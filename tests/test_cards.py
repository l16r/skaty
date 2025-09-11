from skaty.cards import Card, Suit, Value


def test_eq():
    non_card = object()
    c1 = Card(Value.ACE, Suit.SPADES)
    c2 = Card(Value.JACK, Suit.CLUBS)
    c3 = Card(Value.JACK, Suit.CLUBS)

    assert c1 != c2
    assert c2 == c3
    assert c1 != non_card
