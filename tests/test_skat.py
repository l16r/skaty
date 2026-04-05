import pytest
from unittest.mock import MagicMock
from skaty.cards import Card, Suit, Rank
from skaty.isko.actions import BurySkat, DrawSkat
from skaty.isko.rules import ISkO
from skaty.rules import GamePhase, GamePhases


@pytest.fixture
def ruleset():
    return ISkO()


@pytest.fixture
def mock_state():
    """A dummy state with exactly what the actions need to interact with."""
    state = MagicMock()
    state.active_player = 1
    state.phase = GamePhases.DECLARATION
    state.skat = [Card(Rank.SEVEN, Suit.CLUBS), Card(Rank.EIGHT, Suit.CLUBS)]
    state.hands = [
        [],
        [Card(Rank.ACE, Suit.HEARTS), Card(Rank.TEN, Suit.HEARTS)],
        [],
    ]
    state.hand_available = True
    return state


def test_draw_skat_is_valid(mock_state, ruleset):
    action = DrawSkat(player_idx=1)

    # Valid
    assert action.is_valid(mock_state, ruleset) is True

    # Invalid (wrong player)
    action_wrong_player = DrawSkat(player_idx=2)
    assert action_wrong_player.is_valid(mock_state, ruleset) is False

    # Invalid (phase not permitted by ruleset)
    mock_state.phase = GamePhases.BID
    assert action.is_valid(mock_state, ruleset) is False
    mock_state.phase = GamePhases.DECLARATION

    # Invalid (Skat already drawn (len != 2))
    mock_state.skat = []
    assert action.is_valid(mock_state, ruleset) is False


def test_draw_skat_apply_and_undo(mock_state, ruleset):
    action = DrawSkat(player_idx=1)
    action.apply(mock_state, ruleset)

    assert len(mock_state.skat) == 0
    assert len(mock_state.hands[1]) == 4  # 2 original + 2 from skat
    assert mock_state.hand_available is False

    # Check if cards actually moved
    assert Card(Rank.SEVEN, Suit.CLUBS) in mock_state.hands[1]

    # Undo
    action.undo(mock_state)

    assert len(mock_state.skat) == 2
    assert len(mock_state.hands[1]) == 2
    assert mock_state.hand_available is True
    assert Card(Rank.SEVEN, Suit.CLUBS) in mock_state.skat


def test_bury_skat_is_valid(mock_state, ruleset):
    # Setup state with skat already drawn
    mock_state.skat = []
    c1 = Card(Rank.ACE, Suit.HEARTS)
    c2 = Card(Rank.TEN, Suit.HEARTS)
    mock_state.hands[1] = [c1, c2, Card(Rank.SEVEN, Suit.CLUBS)]

    action = BurySkat(player_idx=1, cards=(c1, c2))

    # Valid
    assert action.is_valid(mock_state, ruleset) is True

    # Invalid (trying to bury before drawing)
    mock_state.skat = [Card(Rank.SEVEN, Suit.HEARTS)]
    assert action.is_valid(mock_state, ruleset) is False
    mock_state.skat = []

    # Invalid (trying to bury cards not in hand)
    missing_card = Card(Rank.ACE, Suit.SPADES)
    invalid_action = BurySkat(player_idx=1, cards=(c1, missing_card))
    assert invalid_action.is_valid(mock_state, ruleset) is False

    # Invalid (trying to bury the same card twice)
    duplicate_action = BurySkat(player_idx=1, cards=(c1, c1))
    assert duplicate_action.is_valid(mock_state, ruleset) is False


def test_bury_skat_apply_and_undo(mock_state, ruleset):
    mock_state.skat = []
    c1 = Card(Rank.ACE, Suit.HEARTS)
    c2 = Card(Rank.TEN, Suit.HEARTS)
    mock_state.hands[1] = [c1, c2, Card(Rank.SEVEN, Suit.CLUBS)]

    action = BurySkat(player_idx=1, cards=(c1, c2))
    action.apply(mock_state, ruleset)

    assert len(mock_state.skat) == 2
    assert mock_state.skat == [c1, c2]
    assert len(mock_state.hands[1]) == 1
    assert c1 not in mock_state.hands[1]
    assert c2 not in mock_state.hands[1]

    # Undo
    action.undo(mock_state)

    assert len(mock_state.skat) == 0
    assert len(mock_state.hands[1]) == 3
    assert c1 in mock_state.hands[1]
    assert c2 in mock_state.hands[1]
