import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

from skaty.rules import GameType, GamePhase
from skaty.game_state import GameState, InvalidGameStateError
from skaty.trick import Trick
from skaty.isko import ISkO


@dataclass
class ScoreTestCase:
    id: str
    game_type: GameType
    bid: int
    tops: int
    declarer_tricks_count: int
    declarer_trick_points: int
    skat_points: int
    expected_score: int

    hand: bool = False
    schneider_ann: bool = False
    schwarz_ann: bool = False
    open_ann: bool = False


@pytest.fixture
def base_state():
    state = MagicMock(spec=GameState)
    state.phase = GamePhase.GAME_OVER
    state.declarer_idx = 0
    state.trick_history = [MagicMock() for _ in range(10)]
    state.declaration = MagicMock()
    state.skat = [MagicMock(), MagicMock()]
    state.bid = 18
    state.game_type = GameType.CLUBS
    return state


@pytest.fixture
def ruleset():
    return ISkO()


TEST_CASES = [
    ScoreTestCase(
        id="null_won",
        game_type=GameType.NULL,
        bid=23,
        tops=0,
        declarer_tricks_count=0,
        declarer_trick_points=0,
        skat_points=4,
        expected_score=23,
    ),
    ScoreTestCase(
        id="null_lost",
        game_type=GameType.NULL,
        bid=23,
        tops=0,
        declarer_tricks_count=1,
        declarer_trick_points=0,
        skat_points=0,
        expected_score=-46,
    ),
    ScoreTestCase(
        id="null_hand_ouvert_won",
        game_type=GameType.NULL,
        bid=59,
        tops=0,
        hand=True,
        open_ann=True,
        declarer_tricks_count=0,
        declarer_trick_points=0,
        skat_points=0,
        expected_score=59,
    ),
    ScoreTestCase(
        id="null_overbid",
        game_type=GameType.NULL,
        bid=35,
        tops=0,
        declarer_tricks_count=0,
        declarer_trick_points=0,
        skat_points=0,
        expected_score=-46,
    ),
    ScoreTestCase(
        id="suit_simple_won",
        game_type=GameType.CLUBS,
        bid=18,
        tops=1,
        declarer_tricks_count=6,
        declarer_trick_points=61,
        skat_points=0,
        expected_score=24,
    ),
    ScoreTestCase(
        id="grand_hand_schneider_schwarz_ouvert_won",
        game_type=GameType.GRAND,
        bid=48,
        tops=4,
        hand=True,
        schneider_ann=True,
        schwarz_ann=True,
        open_ann=True,
        declarer_tricks_count=10,
        declarer_trick_points=120,
        skat_points=0,
        expected_score=264,
    ),
    ScoreTestCase(
        id="skat_points_make_it_won",
        game_type=GameType.HEARTS,
        bid=18,
        tops=1,
        declarer_tricks_count=5,
        declarer_trick_points=55,
        skat_points=6,
        expected_score=20,
    ),
    ScoreTestCase(
        id="suit_schneider_played_not_announced",
        game_type=GameType.SPADES,
        bid=18,
        tops=2,
        declarer_tricks_count=8,
        declarer_trick_points=90,
        skat_points=0,
        expected_score=44,
    ),
    ScoreTestCase(
        id="suit_schwarz_played_not_announced",
        game_type=GameType.DIAMONDS,
        bid=18,
        tops=1,
        declarer_tricks_count=10,
        declarer_trick_points=120,
        skat_points=0,
        expected_score=36,
    ),
    ScoreTestCase(
        id="suit_schneider_announced_but_failed",
        game_type=GameType.HEARTS,
        bid=18,
        tops=2,
        hand=True,
        schneider_ann=True,
        declarer_tricks_count=8,
        declarer_trick_points=89,
        skat_points=0,
        expected_score=-100,
    ),
    ScoreTestCase(
        id="suit_simple_lost",
        game_type=GameType.CLUBS,
        bid=18,
        tops=1,
        declarer_tricks_count=5,
        declarer_trick_points=60,
        skat_points=0,
        expected_score=-48,
    ),
    ScoreTestCase(
        id="suit_overbid_lost_mult_adjusted",
        game_type=GameType.CLUBS,
        bid=48,
        tops=1,
        declarer_tricks_count=6,
        declarer_trick_points=61,
        skat_points=0,
        expected_score=-96,
    ),
    ScoreTestCase(
        id="suit_overbid_saved_by_gameplay",
        game_type=GameType.SPADES,
        bid=33,
        tops=1,
        declarer_tricks_count=8,
        declarer_trick_points=90,
        skat_points=0,
        expected_score=33,
    ),
    ScoreTestCase(
        id="lost_schwarz_against_declarer",
        game_type=GameType.GRAND,
        bid=18,
        tops=1,
        declarer_tricks_count=0,
        declarer_trick_points=0,
        skat_points=0,
        expected_score=-192,
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=lambda c: c.id)
def test_calculate_game_score(case: ScoreTestCase, base_state, ruleset):
    base_state.bid = case.bid
    base_state.game_type = case.game_type
    base_state.tops = case.tops

    base_state.declaration.game_type = case.game_type
    base_state.declaration.hand = case.hand
    base_state.declaration.schneider = case.schneider_ann
    base_state.declaration.schwarz = case.schwarz_ann
    base_state.declaration.open = case.open_ann

    base_state.skat[0].points = case.skat_points // 2
    base_state.skat[1].points = case.skat_points - (case.skat_points // 2)

    declarer_tricks = []
    for i in range(case.declarer_tricks_count):
        t = MagicMock(spec=Trick)
        t.get_trick_points.return_value = case.declarer_trick_points if i == 0 else 0
        declarer_tricks.append(t)

    with patch.object(
        ruleset, "get_won_tricks", return_value=[declarer_tricks, [], []]
    ):
        scores = ruleset.calculate_game_score(base_state)

    assert scores[0] == case.expected_score
    assert scores[1] == 0
    assert scores[2] == 0


def test_calculate_game_score_raises_on_invalid_phase(base_state, ruleset):
    base_state.phase = GamePhase.PLAYING
    with pytest.raises(InvalidGameStateError):
        ruleset.calculate_game_score(base_state)


def test_calculate_game_score_raises_on_passed_game(base_state, ruleset):
    base_state.game_type = GameType.PASS
    with pytest.raises(InvalidGameStateError):
        ruleset.calculate_game_score(base_state)


def test_calculate_game_score_raises_on_missing_tops(base_state, ruleset):
    base_state.game_type = GameType.CLUBS
    base_state.tops = None

    # Built-in patch als Context Manager
    with patch.object(ruleset, "get_won_tricks", return_value=[[], [], []]):
        with pytest.raises(InvalidGameStateError):
            ruleset.calculate_game_score(base_state)


def test_calculate_game_score_raises_on_no_declarer(base_state, ruleset):
    base_state.declarer_idx = None

    with pytest.raises(InvalidGameStateError):
        ruleset.calculate_game_score(base_state)
