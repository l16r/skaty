from typing import Literal, Optional, Union
from skaty.cards import Card, create_deck, shuffle_deck
from skaty.exceptions import InvalidActionError, InvalidGameStateError, InvalidPlayError
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
    GameType,
    GiveUp,
    Listen,
    Pass,
    PlayCard,
)
from skaty.trick import Trick


class GameState:
    _players: list[Player]
    # Currently active player. Do not confuse with _declarer.
    _active_player: int
    _trick: Trick
    # Some ruleset to consider during game. Could be ISkO or some extension.
    _rule_set: AbstractRuleSet
    _game_type: GameType
    _trick_history: list[Trick]
    # List of all actions with their player in chronological order.
    _action_history: list[tuple[Player, Action]]
    # Highgest bid observed. Can also be calculated by considering _trick_history.
    _bid: Optional[int]
    _phase: GamePhase
    # None during GamePhase.DECLARATION between drawing skat and burying skat.
    _skat: Optional[tuple[Card, Card]]
    # Points each player scored. Can also be calculated by considering _trick_history.
    _points: dict[Player, int]
    _hand_available: bool
    # Contains the game result in GamePhase.WON or GamePhase.LOST. Can also be calculated by calling calculate_game_score().
    _game_result: int
    # None if game was passed.
    # Declarer, constant after game was bid. None if game is before GamePhase.BID or in GamePhase.PASSED.
    _declarer: Optional[int]
    _declaration: tuple[bool, bool, bool, bool]
    _log: bool

    def __init__(
        self, players: list[Player], rule_set: AbstractRuleSet, log: bool = False
    ):
        """
        Initialize a game.

        Raises:
            InvalidGameStateError: If the number of players does not equal 3.
        """
        if len(players) != 3:
            raise InvalidGameStateError("A game must consist of 3 players.")
        self._players = players
        self._active_player = 2
        self._trick = Trick()
        self._rule_set = rule_set
        self._bid = None
        self._action_history = []
        self._trick_history = list()
        self._phase = GamePhase.PRE_DEAL
        self._skat = None
        self._points = dict()
        self._points[players[0]] = 0
        self._points[players[1]] = 0
        self._points[players[2]] = 0
        self._hand_available = True
        self._game_result = 0
        self._declarer = None
        self._log = log

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
            InvalidActionError: If the player is not active.
        """
        if not self._rule_set.is_valid_action(action, self._phase):
            raise InvalidGameStateError(
                f"Action {action} is not possible during {self._phase}"
            )
        if isinstance(
            action, (DeclareBid, Listen, Pass)
        ) and not self._rule_set.is_valid_bid(
            player, action, self._get_previous_bids()
        ):
            raise InvalidActionError(f"Bid {action} is not possible.")
        if player is not self._players[self._active_player]:
            raise InvalidActionError(
                f"Player {player} can not {action} because he is not active."
            )

        if self._log:
            print(f"Player {player} plays {action}.")

        # --- Enforce listen-only and declare-only in weitersagen (middlehand vs dealer) ---
        # Maybe refactor is_valid_action to receive more args so that this condition can be integrated
        if self._phase == GamePhase.BID:
            bids = self._get_previous_bids()
            players = self._players
            passed = set(p for p, a in bids if isinstance(a, Pass))
            in_bidding = [p for p in players if p not in passed]
            # Only middlehand and dealer left, forehand out
            if (
                players[0] in passed
                and players[1] in in_bidding
                and players[2] in in_bidding
                and len(in_bidding) == 2
            ):
                if player is players[1] and not isinstance(action, (Listen, Pass)):
                    raise InvalidActionError(
                        "Middlehand can only Listen or Pass after forehand passes and backhand is at weitersagen stage."
                    )
                if player is players[2]:
                    if isinstance(action, Listen):
                        raise InvalidActionError(
                            "Dealer cannot Listen after middlehand passes; only DeclareBid or Pass is allowed."
                        )
                    if not isinstance(action, (DeclareBid, Pass)):
                        raise InvalidActionError(
                            "Dealer can only DeclareBid or Pass in weitersagen stage."
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
                    winner = self._trick.get_winner(
                        self._rule_set
                    )  # index in trick order
                    current_player = self._players.index(player)  # last to play
                    first_player = (current_player - 2) % 3
                    winner_player_index = (first_player + winner) % 3
                    winner_player = self._players[winner_player_index]
                    # Add points to winner
                    self._points[winner_player] += points
                    # Reset trick
                    self._trick = Trick()
            case DrawSkat():
                assert self._skat is not None
                assert len(self._skat) == 2
                assert self._declarer is not None
                self._hand_available = False
                self._players[self._declarer].add_card(self._skat[0])
                self._players[self._declarer].add_card(self._skat[1])
                self._skat = None
            case BurySkat(cards):
                assert self._skat is None
                assert not self._hand_available
                assert len(cards) == 2
                assert self._declarer is not None
                self._skat = (cards[0], cards[1])
                self._players[self._declarer].remove_card(cards[0])
                self._players[self._declarer].remove_card(cards[1])
            case DeclareBid(bid=value):
                if not self._rule_set.is_valid_bid(
                    player, action, self._get_previous_bids()
                ):
                    return False
                self._bid = value
            case Listen():
                if not self._rule_set.is_valid_bid(
                    player, action, self._get_previous_bids()
                ):
                    return False

            case Pass():
                if not self._rule_set.is_valid_bid(
                    player, action, self._get_previous_bids()
                ):
                    return False
            case DeclareGame(game_type, hand, schneider, schwarz, open):
                if self._skat is None:
                    raise InvalidGameStateError("Skat must be buried before declaring.")
                assert self._bid is not None

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
                self._rule_set.set_game_type(game_type)
                self._game_type = game_type
                self._declaration = (hand, schneider, schwarz, open)
            case GiveUp():
                player, score = self.calculate_game_score()
                self._game_result = score

        self._action_history.append((player, action))
        self._advance_turn(action)
        return True

    def _advance_turn(self, action: Action):
        if isinstance(action, GiveUp):
            self._phase = GamePhase.LOST
            return

        if self._phase == GamePhase.BID:
            self._advance_bidding(action)
            return

        if isinstance(action, PlayCard):
            self._active_player = (self._active_player + 1) % 3
            return

        if isinstance(action, DealCards):
            self._phase = GamePhase.BID
            self._active_player = 1  # Middlehand starts bidding
            return

        if isinstance(action, DeclareGame):
            self._phase = GamePhase.PLAYING
            self._active_player = 0
            return

    def _advance_bidding(self, action: Action):
        """
        Clean, explicit Skat bidding (geben-hören-sagen-weitersagen) logic.
        """
        bids = self._get_previous_bids()
        players = self._players
        passed = set(p for p, a in bids if isinstance(a, Pass))
        in_bidding = [p for p in players if p not in passed]

        # All passed: game is passed
        if len(bids) >= 3 and len([a for _, a in bids if isinstance(a, Pass)]) == 3:
            if self._log:
                print("Passing game")
            self._phase = GamePhase.PASSED
            return

        # Only one left: they are declarer, except the case in which forehand has not said anything yet
        if len(in_bidding) == 1 and players[0] in passed:
            self._declarer = players.index(in_bidding[0])
            self._active_player = self._declarer
            self._phase = GamePhase.DECLARATION
            return

        # --- Bidding stages ---
        # 1. geben/hören: 0 vs 1
        if (
            players[0] in in_bidding
            and players[1] in in_bidding
            and players[2] in in_bidding
        ):
            # Table order: 1 (middlehand) starts after deal
            self._active_player = 0 if self._active_player == 1 else 1
            return

        # 2. sagen/weitersagen: winner vs 2
        # If only two left, always alternate between them
        if len(in_bidding) == 2:
            # If forehand is out, only middlehand and dealer left
            if (
                players[0] in passed
                and players[1] in in_bidding
                and players[2] in in_bidding
            ):
                # Middlehand can only Listen, not bid
                if self._active_player == 0:
                    # Backhand must declare now (weitersagen)
                    assert isinstance(action, Pass)
                    # Backhand must then declare, middlehand is listening
                    self._active_player = 2
                elif self._active_player == 1:
                    if isinstance(action, DeclareBid):
                        raise InvalidActionError(
                            "Middlehand can only Listen/Pass after forehand passes and backhand is at weitersagen stage."
                        )
                    self._active_player = 2
                elif self._active_player == 2:
                    if not isinstance(action, (DeclareBid, Pass)):
                        raise InvalidActionError(
                            "Backhand can only Declare/Pass after forehand passes and backhand is at weitersagen stage."
                        )
                    self._active_player = 1
                return
            # If middlehand is out, only forehand and dealer left
            elif (
                players[1] in passed
                and players[0] in in_bidding
                and players[2] in in_bidding
            ):
                # Alternate between 0 and 2
                if self._active_player == 0:
                    if not isinstance(action, (Listen, Pass)):
                        raise InvalidActionError(
                            "Forehand can only Listen/Pass after middlehand passes and backhand is at weitersagen stage."
                        )
                    self._active_player = 2
                elif self._active_player == 1:
                    if not isinstance(action, Pass):
                        raise InvalidGameStateError("Middlehand should pass now.")
                    self._active_player = 2
                elif self._active_player == 2:
                    if not isinstance(action, (DeclareBid, Pass)):
                        raise InvalidActionError(
                            "Backhand can only Declare/Pass after middlehand passes and forehand is still listening."
                        )
                    self._active_player = 0
                return
            # If dealer is out, only forehand and middlehand left (should not happen in Skat)
            elif (
                players[2] in passed
                and players[0] in in_bidding
                and players[1] in in_bidding
            ):
                raise InvalidGameStateError(
                    "Dealer is out, but forehand and middlehand are not. This should not have happened."
                )
                # self._active_player = 1 if self._active_player == 0 else 0
                # return
            else:
                raise InvalidActionError(
                    "Bidding logic error: unexpected two-player state."
                )
        if len(bids) == 2 and len(in_bidding) == 1:
            self._active_player = 0
            return
        if len(in_bidding) == 1:
            self._phase = GamePhase.DECLARATION
            self._declarer = self._players.index(in_bidding[0])
            self._active_player = self._declarer
            return

        raise InvalidActionError("Bidding logic error: no valid next player.")

    def _get_previous_bids(self) -> list[tuple[Player, DeclareBid | Listen | Pass]]:
        """
        Return the previous bids (filters _action_history).
        """
        trick_history: list[tuple[Player, DeclareBid | Listen | Pass]] = []
        for p, a in self._action_history:
            if (
                isinstance(a, DeclareBid)
                or isinstance(a, Listen)
                or isinstance(a, Pass)
            ):
                trick_history.append((p, a))
        return trick_history
