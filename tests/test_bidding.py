import pytest
from skaty.exceptions import InvalidActionError, InvalidBidError, InvalidGameStateError
from skaty.player import Player
from skaty.rules import DealCards, DeclareBid, Listen, Pass, GamePhase
from skaty.isko import ISkO
from skaty.game_state import GameState


def setup_game():
    p0 = Player("Forehand")
    p1 = Player("Middlehand")
    p2 = Player("Dealer")
    ruleset = ISkO()
    game = GameState([p0, p1, p2], ruleset, 2, log=True)
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


def test_bidding_invalid_bid_value():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    # Middlehand tries invalid bid (not in allowed set)
    with pytest.raises(InvalidActionError):
        game.apply_action(players[1], DeclareBid(19))
    # Middlehand tries too low bid
    with pytest.raises(InvalidActionError):
        game.apply_action(players[1], DeclareBid(0))
    # Middlehand tries negative bid
    with pytest.raises(InvalidActionError):
        game.apply_action(players[1], DeclareBid(-1))


def test_bidding_out_of_turn():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    # Forehand tries to bid out of turn
    with pytest.raises(InvalidActionError):
        game.apply_action(players[0], DeclareBid(18))
    # Dealer tries to pass out of turn
    with pytest.raises(InvalidActionError):
        game.apply_action(players[2], Pass())


def test_bidding_listen_out_of_turn():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    # Forehand tries to listen out of turn
    with pytest.raises(InvalidActionError):
        game.apply_action(players[0], Listen())
    # Middlehand bids, then dealer tries to listen (not allowed)
    game.apply_action(players[1], DeclareBid(18))
    with pytest.raises(InvalidActionError):
        game.apply_action(players[2], Listen())


def test_bidding_pass_after_pass():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], Pass())
    # Middlehand tries to pass again
    with pytest.raises(InvalidActionError):
        game.apply_action(players[1], Pass())


def test_bidding_bid_after_pass():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], Pass())
    # Middlehand tries to bid after passing
    with pytest.raises(InvalidActionError):
        game.apply_action(players[1], DeclareBid(18))


def test_bidding_maximum_bid():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    # Middlehand bids minimum
    game.apply_action(players[1], DeclareBid(18))
    # Forehand listens
    game.apply_action(players[0], Listen())
    # Middlehand bids maximum allowed
    max_bid = max(ISkO._VALID_BIDS)
    game.apply_action(players[1], DeclareBid(max_bid))
    # Forehand passes
    game.apply_action(players[0], Pass())
    with pytest.raises(InvalidActionError):
        game.apply_action(players[2], DeclareBid(max_bid + 12))
    # Dealer passes
    game.apply_action(players[2], Pass())
    assert game._phase == GamePhase.DECLARATION
    assert game._declarer == 1


def test_bidding_repeated_bid_value():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], DeclareBid(18))
    game.apply_action(players[0], Listen())
    # Middlehand tries to bid 18 again (should not be allowed)
    with pytest.raises(InvalidActionError):
        game.apply_action(players[1], DeclareBid(18))


def test_bidding_after_declaration_phase():
    game, players = setup_game()
    game.apply_action(players[2], DealCards())
    game.apply_action(players[1], DeclareBid(18))
    game.apply_action(players[0], Pass())
    game.apply_action(players[2], Pass())
    # Forehand is declarer, phase is DECLARATION
    assert game._phase == GamePhase.DECLARATION
    # No more bidding allowed
    with pytest.raises(InvalidGameStateError):
        game.apply_action(players[0], DeclareBid(20))
