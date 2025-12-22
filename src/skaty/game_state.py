from typing import Optional
from skaty.cards import Card, create_deck, shuffle_deck
from skaty.exceptions import InvalidGameStateError, InvalidPlayError
from skaty.player import Player
from skaty.rules import (
    AbstractRuleSet,
    Action,
    BurySkat,
    DealCards,
    DeclareBid,
    DeclareGame,
    DrawSkat,
    GamePhase,
    GiveUp,
    Listen,
    Pass,
    PlayCard,
)
from skaty.trick import Trick


class GameState:
    _players: list[Player]
    _active_player: int
    _trick: Trick
    _rule_set: AbstractRuleSet
    _trick_history: list[Trick]
    _action_history: list[tuple[Player, Action]]
    _bid: int
    _phase: GamePhase
    _skat: Optional[tuple[Card, Card]]
    _points: dict[Player, int]
    _hand_available: bool

    def __init__(self, players: list[Player], rule_set: AbstractRuleSet):
        """
        Initialize a game.

        Raises:
            InvalidGameStateError: If the number of players does not equal 3.
        """
        if len(players) != 3:
            raise InvalidGameStateError("A game must consist of 3 players.")
        self._players = players
        self._active_player = 0
        self._trick = Trick()
        self._rule_set = rule_set
        self._bid = 0
        self._trick_history = list()
        self._phase = GamePhase.PRE_DEAL
        self._skat = None
        self._points = dict()
        self._hand_available = True

    def calculate_game_score(self) -> tuple[Player, int]:
        """
        Calculates the points a player gained or lost according to his declaration.
        """
        return (
            self._players[self._active_player],
            self._rule_set.calculate_game_score(),
        )

    def apply_action(self, player: Player, action: Action) -> bool:
        """
        Tries to apply the action to the game.

        Returns:
            A boolean indicating if the action has been applied or not. In the latter case, the action can be considered illegal.

        Raises:
            InvalidPlayError: If the player tries to play a card it does not have.
        """
        if not self._rule_set.is_valid_action(player, action, self._phase):
            raise InvalidGameStateError(
                f"Action {action} is not possible during {self._phase}"
            )

        match action:
            case DealCards():
                shuffled = shuffle_deck(create_deck())
                self._players[0].add_cards(shuffled[0:10])
                self._players[1].add_cards(shuffled[10:20])
                self._players[2].add_cards(shuffled[20:30])
                self._skat = (shuffled[30], shuffled[31])
            case PlayCard(card=played_card):
                if played_card not in player.hand:
                    raise InvalidPlayError(
                        f"{player.name} does not have {played_card}."
                    )
                elif not self._rule_set.is_valid_card_play(
                    player, played_card, self._trick.first_card
                ):
                    raise InvalidPlayError(
                        f"Can not play {played_card}, because it is illegal."
                    )
                player.remove_card(played_card)
                self._trick.add_card(played_card)
                if self._trick.is_complete():
                    points = self._trick.get_trick_points()
                    winner = self._trick.get_winner(self._rule_set)
                    # TODO: add points to winner (self._points)
            case DrawSkat():
                assert self._skat is not None
                assert len(self._skat) == 2
                self._hand_available = False
                self._players[self._active_player].add_card(self._skat[0])
                self._players[self._active_player].add_card(self._skat[1])
                self._skat = None
            case BurySkat(cards):
                assert self._skat is None
                assert not self._hand_available
                assert len(cards) == 2
                self._skat = (cards[0], cards[1])
                self._players[self._active_player].remove_card(cards[0])
                self._players[self._active_player].remove_card(cards[1])
            case DeclareBid(bid=value):
                if not self._rule_set.is_valid_bid(player, value):
                    return False
                self._bid = value
                # TODO: implement bidding logic
            case Listen():
                # TODO: implement bidding logic
                pass
            case Pass():
                # TODO: implement bidding logic
                pass
            case DeclareGame(game_type, hand, schneider, schwarz, open):
                assert self._skat is not None

                if not self._rule_set.is_valid_game_declaration(
                    self._players[self._active_player],
                    self._bid,
                    game_type,
                    hand,
                    schneider,
                    schwarz,
                    open,
                    self._hand_available,
                ):
                    return False
            case GiveUp():
                # TODO: implement giving up
                pass

        self._advance_turn()
        return True

    def _advance_turn(self):
        # TODO: implement phase changes. this may be done via receiving an argument to _advance_turn or by changing the phase in apply_action.
        self._active_player = (self._active_player + 1) % 3
        pass
