from typing import Optional
from pytest import raises
from skaty.cards import Card
from skaty.exceptions import InvalidActionError, InvalidGameStateError
from skaty.game_state import GameState
from skaty.isko import ISkO
from skaty.player import Player
from skaty.rules import (
    AbstractRuleSet,
    BurySkat,
    DealCards,
    DeclareBid,
    DeclareGame,
    DrawSkat,
    GamePhase,
    GameType,
    GiveUp,
    Listen,
    Pass,
    PlayCard,
)


def any_valid_card(player: Player, rules: AbstractRuleSet, first_card: Optional[Card]):
    print(f"{first_card=}")
    for c in player.hand:
        if rules.is_valid_card_play(player, c, first_card):
            return c
    return player.hand[0]


def test_valid_game():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    with raises(InvalidGameStateError):
        GameState([], isko, 2)
    game = GameState([p0, p1, p2], isko, 2, log=True)
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

    for _ in range(10):
        active_player = game.active_player
        actions = game.get_valid_actions(active_player)
        game.apply_action(active_player, actions[0])

        active_player = game.active_player
        actions = game.get_valid_actions(active_player)
        game.apply_action(active_player, actions[0])

        active_player = game.active_player
        actions = game.get_valid_actions(active_player)
        game.apply_action(active_player, actions[0])


def test_play_card_not_active():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    game = GameState([p0, p1, p2], isko, 2, log=True)
    game.apply_action(p2, DealCards())
    game.apply_action(p1, Pass())
    game.apply_action(p2, DeclareBid(18))
    game.apply_action(p0, Listen())
    game.apply_action(p2, DeclareBid(23))
    game.apply_action(p0, Pass())
    game.apply_action(p2, DrawSkat())
    game.apply_action(p2, BurySkat((p2.hand[0], p2.hand[1])))
    game.apply_action(p2, DeclareGame(GameType.GRAND, False))
    # p1 tries to play a card out of turn
    with raises(InvalidActionError):
        game.apply_action(p1, PlayCard(p1.hand[0]))


def test_play_before_declaration():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    game = GameState([p0, p1, p2], isko, 2, log=True)
    game.apply_action(p2, DealCards())

    with raises(InvalidGameStateError):
        game.apply_action(p1, PlayCard(p0.hand[0]))


def test_give_up_in_various_phases():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    game = GameState([p0, p1, p2], isko, 2, log=True)

    with raises(InvalidGameStateError):
        game.apply_action(p2, GiveUp())
    game.apply_action(p2, DealCards())
    # Give up during bidding
    with raises(InvalidGameStateError):
        game.apply_action(p1, GiveUp())


def test_calculate_score_invalid_state():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    game = GameState([p0, p1, p2], isko, 2, log=True)
    # Not enough info to calculate score
    with raises(InvalidGameStateError):
        game.calculate_game_score()


def test_null_game_edge_cases():
    p0 = Player("0")
    p1 = Player("1")
    p2 = Player("2")
    isko = ISkO()
    game = GameState([p0, p1, p2], isko, 2, log=True)
    game.apply_action(p2, DealCards())
    game.apply_action(p1, Pass())
    game.apply_action(p2, DeclareBid(63))
    game.apply_action(p0, Pass())

    with raises(InvalidActionError):
        game.apply_action(p2, DeclareGame(GameType.NULL, True, False, False, True))
