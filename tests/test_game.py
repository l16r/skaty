from pytest import raises
from skaty.exceptions import InvalidActionError, InvalidGameStateError
from skaty.game_state import GameState
from skaty.isko import ISkO
from skaty.player import Player
from skaty.rules import (
    BurySkat,
    DealCards,
    DeclareBid,
    DeclareGame,
    DrawSkat,
    GameType,
    Listen,
    Pass,
)


def test_valid_game():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    with raises(InvalidGameStateError):
        GameState([], isko)
    game = GameState([p0, p1, p2], isko, True)
    game.apply_action(p2, DealCards())
    game.apply_action(p1, Pass())
    game.apply_action(p2, DeclareBid(18))
    game.apply_action(p0, Listen())
    game.apply_action(p2, DeclareBid(23))
    game.apply_action(p0, Pass())
    game.apply_action(p2, DrawSkat())
    with raises(InvalidGameStateError):
        # Should not be able to declare, unless Skat is buried
        game.apply_action(p2, DeclareGame(GameType.CLUBS, False))
    game.apply_action(p2, BurySkat((p2.hand[0], p2.hand[1])))
    game.apply_action(p2, DeclareGame(GameType.GRAND, False))
