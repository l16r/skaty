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
    GameType,
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
    active_player = 0
    for _ in range(10):
        first_card = game._players[active_player].hand[0]
        game.apply_action(
            game._players[active_player], PlayCard(game._players[active_player].hand[0])
        )
        active_player = game._active_player
        game.apply_action(
            game._players[active_player],
            PlayCard(
                any_valid_card(game._players[active_player], game._rule_set, first_card)
            ),
        )
        active_player = game._active_player
        game.apply_action(
            game._players[active_player],
            PlayCard(
                any_valid_card(game._players[active_player], game._rule_set, first_card)
            ),
        )
        active_player = game._active_player
        first_card = None
