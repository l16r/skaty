import pytest
from skaty.exceptions import InvalidActionError
from skaty.player import Player
from skaty.rules import DealCards, DeclareBid, Listen, Pass, GamePhase
from skaty.isko import ISkO
from skaty.game_state import GameState


def setup_game():
    p0 = Player("Forehand")
    p1 = Player("Middlehand")
    p2 = Player("Dealer")
    ruleset = ISkO()
    game = GameState([p0, p1, p2], ruleset)
    return game, [p0, p1, p2]


def test_bidding_sequence_basic():
    game, players = setup_game()
    # Start game: deal cards
    game.apply_action(players[2], DealCards())
    assert game._phase == GamePhase.BID
    assert game._active_player == 1

    with pytest.raises(InvalidActionError):
        game.apply_action(players[0], DeclareBid(18))
        game.apply_action(players[0], Pass())
        game.apply_action(players[0], Listen())
    # Middlehand bids 18
    game.apply_action(players[1], DeclareBid(18))
    assert game._active_player == 0
    # Forehand listens
    game.apply_action(players[0], Listen())
    assert game._active_player == 1
    # Middlehand bids 20
    game.apply_action(players[1], DeclareBid(20))
    assert game._active_player == 0
    # Forehand passes
    game.apply_action(players[0], Pass())
    # Now middlehand vs backhand/dealer
    assert game._active_player == 2
    # Dealer declares ("weitersagen")
    game.apply_action(players[2], DeclareBid(22))
    assert game._active_player == 1
    # Middlehand passes
    game.apply_action(players[1], Pass())
    # Dealer should be declarer
    assert game._phase == GamePhase.DECLARATION
    # Only one player left in bidding
    assert game._declarer == 2


def test_bidding_all_pass():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], Pass())
    game.apply_action(players[2], Pass())
    game.apply_action(players[0], Pass())
    assert game._phase == GamePhase.PASSED


def test_bidding_middlehand_wins():
    game, players = setup_game()
    ruleset = ISkO()
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], DeclareBid(18))
    with pytest.raises(InvalidActionError):
        game.apply_action(players[2], DeclareBid(20))


def test_bidding_forehand_vs_dealer():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    with pytest.raises(InvalidActionError):
        game.apply_action(players[0], DeclareBid(18))
    game.apply_action(players[1], DeclareBid(18))
    game.apply_action(players[0], Pass())
    # Forehand vs dealer
    assert game._active_player == 2
    game.apply_action(players[2], DeclareBid(20))
    with pytest.raises(InvalidActionError):
        game.apply_action(players[0], Pass())
        game.apply_action(players[0], Listen())
        game.apply_action(players[0], DeclareBid(23))
    with pytest.raises(InvalidActionError):
        # Middlehand can not bid, but only listen now
        game.apply_action(players[1], DeclareBid(22))
    game.apply_action(players[1], Listen())
    game.apply_action(players[2], DeclareBid(22))
    game.apply_action(players[1], Pass())
    # Dealer should be declarer
    assert game._phase == GamePhase.DECLARATION
    assert game._declarer == 2


def test_bidding_two_pass_forehand_bid():
    game, players = setup_game()
    with pytest.raises(InvalidActionError):
        # Should not be possible, before dealing
        game.apply_action(players[0], Pass())
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], Pass())
    with pytest.raises(InvalidActionError):
        game.apply_action(players[2], Listen())
    game.apply_action(players[2], Pass())
    game.apply_action(players[0], DeclareBid(18))
    assert game._phase == GamePhase.DECLARATION
    assert game._declarer == 0
