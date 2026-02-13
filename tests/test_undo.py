import pytest
from skaty.cards import Card, Rank, Suit
from skaty.player import Player
from skaty.game_state import GameState
from skaty.isko import ISkO
from skaty.rules import (
    DealCards,
    DeclareGame,
    PlayCard,
    DeclareBid,
    Pass,
    BiddingPhase,
    GamePhase,
    GameType,
    DrawSkat,
    BurySkat,
)


@pytest.fixture
def players():
    return [Player("FH"), Player("MH"), Player("BH")]


@pytest.fixture
def game_instance(players):
    return GameState(players, ISkO(), dealer=2)


@pytest.fixture
def dealt_game(game_instance) -> GameState:
    gs = game_instance
    gs.apply_action(gs.active_player, DealCards())
    return gs


def get_snapshot(gs: GameState):
    return {
        "phase": gs._phase,
        "active_player": gs._active_player,
        "bid": gs._bid,
        "hands": [list(p.hand) for p in gs._players],
        "points": list(gs._points.values()),
        "skat": gs._skat,
        "history_len": len(gs._action_history),
    }


def test_undo_deal_cards(game_instance):
    gs = game_instance
    before = get_snapshot(gs)

    gs.apply_action(gs.active_player, DealCards())
    gs.undo_action()

    after = get_snapshot(gs)
    assert before == after
    assert all(len(p.hand) == 0 for p in gs._players)


def test_undo_bidding_sequence(dealt_game):
    gs = dealt_game
    before = get_snapshot(gs)

    # bidding
    p1 = gs.active_player
    gs.apply_action(p1, DeclareBid(18))

    p2 = gs.active_player
    gs.apply_action(p2, Pass())

    gs.undo_action()
    gs.undo_action()

    after = get_snapshot(gs)
    assert before == after


def test_undo_complete_trick_and_points(dealt_game: GameState):
    gs = dealt_game

    gs.apply_action(gs._players[gs._middlehand], Pass())
    gs.apply_action(gs._players[gs._backhand], DeclareBid(18))
    gs.apply_action(gs._players[gs._forehand], Pass())

    gs.apply_action(gs.active_player, DrawSkat())
    cards_to_bury = (gs.active_player.hand[0], gs.active_player.hand[1])
    gs.apply_action(gs.active_player, BurySkat(cards_to_bury))

    gs.apply_action(gs.active_player, DeclareGame(GameType.CLUBS, False))

    before_trick = get_snapshot(gs)

    players_in_order = [
        gs._players[gs._forehand],
        gs._players[gs._middlehand],
        gs._players[gs._backhand],
    ]
    for p in players_in_order:
        gs.apply_action(p, gs.get_valid_actions(p)[0])

    assert len(gs._trick_history) == 1
    assert sum(gs._points.values()) > 0

    gs.undo_action()
    gs.undo_action()
    gs.undo_action()

    after_trick = get_snapshot(gs)

    assert len(gs._trick_history) == 0
    assert sum(gs._points.values()) == 0
    assert set(after_trick["hands"][0]) == set(before_trick["hands"][0])
    assert gs._phase == GamePhase.PLAYING


def test_undo_skat_handling(dealt_game):
    gs = dealt_game
    # Skip bidding
    gs._phase = GamePhase.DECLARATION
    gs._declarer = 0
    gs._active_player = 0

    before = get_snapshot(gs)

    gs.apply_action(gs._players[0], DrawSkat())
    assert len(gs._players[0].hand) == 12
    assert gs._skat is None

    gs.undo_action()

    after = get_snapshot(gs)
    assert len(gs._players[0].hand) == 10
    assert after["skat"] is not None
    assert before == after
