from typing import Any, Generator, Optional

import itertools
from skaty.cards import Card, create_deck, shuffle_deck
from skaty.exceptions import InvalidActionError, InvalidGameStateError, InvalidPlayError
from skaty.player import Player
from skaty.rules import (
    AbstractRuleSet,
    Action,
    BiddingPhase,
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
    PlayerPosition,
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
    _trick_history: list[tuple[Trick, Player]]
    # List of all actions with their player in chronological order.
    _action_history: list[tuple[Player, Action]]
    _undo_stack: list[dict[str, Any]]
    # Highgest bid observed. Can also be calculated by considering _action_history.
    _bid: Optional[int]
    _bidding_phase: BiddingPhase
    _phase: GamePhase
    # None during GamePhase.DECLARATION between drawing skat and burying skat.
    _skat: Optional[tuple[Card, Card]]
    # Points each player scored. Can also be calculated by considering _trick_history.
    _points: dict[Player, int]
    _hand_available: bool
    # Contains the game result in GamePhase.WON or GamePhase.LOST. Can also be calculated by calling calculate_game_score().
    _game_result: int
    # Declarer, constant after game was bid. None if game is before GamePhase.BID or in GamePhase.PASSED.
    _declarer: Optional[int]
    _forehand: int
    _middlehand: int
    _backhand: int
    # The game declared (hand, schneider announced, schwarz announced, ouvert)
    _declaration: tuple[bool, bool, bool, bool]
    _log: bool

    def __init__(
        self,
        players: list[Player],
        rule_set: AbstractRuleSet,
        dealer: int,
        log: bool = False,
    ):
        """
        Initialize a game.

        Raises:
            InvalidGameStateError: If the number of players does not equal 3.
        """
        if len(players) != 3:
            raise InvalidGameStateError("A game must consist of 3 players.")
        self._players = players
        self._active_player = dealer
        self._forehand = (dealer + 1) % 3
        self._middlehand = (dealer + 2) % 3
        self._backhand = dealer
        self._trick = Trick()
        self._rule_set = rule_set
        self._game_type = GameType.PASS
        self._bid = None
        self._bidding_phase = BiddingPhase.ForehandMiddlehand
        self._action_history = []
        self._undo_stack = []
        self._trick_history = []
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

    @property
    def active_player(self) -> Player:
        return self._players[self._active_player]

    def calculate_game_score(self) -> int:
        """
        Calculates the points a player gained or lost according to his declaration.
        """
        if self._declarer is None or self._bid is None or self._skat is None:
            raise InvalidGameStateError(
                "Unable to calculate game score if no game has been declared."
            )
        return self._rule_set.calculate_game_score(
            self._players,
            self._declarer,
            self._points,
            self._trick_history,
            self._game_type,
            self._bid,
            self._skat,
            self._declaration[0],
            self._declaration[1],
            self._declaration[2],
            self._declaration[3],
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
                f"Action {action} is not possible during {self._phase.name}"
            )
        if isinstance(
            action, (DeclareBid, Listen, Pass)
        ) and not self._rule_set.is_valid_bid(
            player,
            action,
            self._get_previous_bids(),
            self._get_player_position(player),
            self._bidding_phase,
        ):
            raise InvalidActionError(f"Bid {action} is not possible.")
        if player != self._players[self._active_player]:
            raise InvalidActionError(
                f"Player {player} can not {action} because he is not active."
            )

        memento = {
            "phase": self._phase,
            "active_player": self._active_player,
            "bid": self._bid,
            "bidding_phase": self._bidding_phase,
            "declarer": self._declarer,
            "game_type": self._game_type,
            "hand_available": self._hand_available,
            "skat": self._skat,
            "game_result": self._game_result,
        }

        if self._log:
            print(f"Player {player} plays {action}.")

        match action:
            case DealCards():
                shuffled = shuffle_deck(create_deck())

                self._players[0].add_cards(shuffled[0:10])
                self._players[1].add_cards(shuffled[10:20])
                self._players[2].add_cards(shuffled[20:30])
                self._skat = (shuffled[30], shuffled[31])
            case PlayCard(card=played_card):
                if not self._rule_set.is_valid_card_play(
                    player, played_card, self._trick.first_card, self._game_type
                ):
                    raise InvalidPlayError(
                        f"Can not play {played_card}, because it is illegal."
                    )

                memento["trick_cards"] = self._trick.cards

                player.play_card(played_card)
                self._trick.add_card(played_card)

                if self._trick.is_complete():
                    memento["trick_winner"] = self._trick.get_winner(
                        self._rule_set, self._game_type
                    )
                    memento["points_snapshot"] = {
                        p: self._points[p] for p in self._players
                    }

                    points = self._trick.get_trick_points()
                    winner = self._trick.get_winner(
                        self._rule_set, self._game_type
                    )  # index in trick order
                    current_player = self._players.index(player)  # last to play
                    first_player = (current_player - 2) % 3
                    winner_player_index = (first_player + winner) % 3
                    winner_player = self._players[winner_player_index]
                    self._trick_history.append((self._trick, winner_player))
                    # Add points to winner
                    self._points[winner_player] += points
                    # Reset trick
                    self._trick = Trick()
            case DrawSkat():
                if self._skat is None:
                    return False
                assert len(self._skat) == 2
                assert self._declarer is not None

                memento["declarer_hand"] = list(self._players[self._declarer].hand)

                self._hand_available = False
                self._players[self._declarer].add_cards(list(self._skat))
                self._skat = None
            case BurySkat(cards):
                if self._skat is not None:
                    return False
                assert not self._hand_available
                assert len(cards) == 2
                assert self._declarer is not None

                memento["declarer_hand"] = list(self._players[self._declarer].hand)

                self._skat = cards
                for c in cards:
                    self._players[self._declarer].play_card(c)
            case DeclareBid(bid=value):
                self._bid = value
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
                    raise InvalidActionError("Game declaration not possible.")
                self._game_type = game_type
                self._declaration = (hand, schneider, schwarz, open)
            case GiveUp():
                self._game_result = self.calculate_game_score()

        self._undo_stack.append(memento)
        self._action_history.append((player, action))
        self._advance_turn(action)
        return True

    def undo_action(self):
        if not self._undo_stack:
            return

        m = self._undo_stack.pop()
        player, action = self._action_history.pop()

        if isinstance(action, PlayCard):
            # Was the trick finished?
            if self._trick.len == 0 and self._trick_history:
                last_trick, winner = self._trick_history.pop()
                self._trick = last_trick
                # Reset points
                self._points = m["points_snapshot"]

            # remove cards and get them back into hand
            self._trick.pop()
            player.undo_play_card(action.card)

        elif isinstance(action, DealCards):
            for p in self._players:
                p.clear_hand()

        elif isinstance(action, DrawSkat) or isinstance(action, BurySkat):
            self._players[self._declarer]._hand = m["declarer_hand"]

        self._phase = m["phase"]
        self._active_player = m["active_player"]
        self._bid = m["bid"]
        self._bidding_phase = m["bidding_phase"]
        self._declarer = m["declarer"]
        self._hand_available = m["hand_available"]
        self._skat = m["skat"]
        if "declaration" in m:
            self._declaration = m["declaration"]
        self._game_result = m["game_result"]

        if "game_type" in m:
            self._game_type = m["game_type"]

    def get_valid_actions(self, player: Player) -> Generator[Action, None, None]:
        """
        Yield all valid actions for a given player.
        """
        if self._players[self._active_player] != player:
            return

        allowed_types = self._rule_set.get_action_types_for_phase(self._phase)

        for action_type in allowed_types:
            if action_type is PlayCard:
                for card in player.hand:
                    if self._rule_set.is_valid_card_play(
                        player, card, self._trick.first_card, self._game_type
                    ):
                        yield PlayCard(card)

            elif action_type is DeclareBid:
                next_bid = self._rule_set.get_next_valid_bid(self._bid)
                if self._rule_set.is_valid_bid(
                    player,
                    DeclareBid(next_bid),
                    self._get_previous_bids(),
                    self._get_player_position(player),
                    self._bidding_phase,
                ):
                    yield DeclareBid(next_bid)

            elif action_type in (Pass, Listen, DrawSkat, DealCards):
                action = action_type()
                if action_type in (Pass, Listen):
                    if self._rule_set.is_valid_bid(
                        player,
                        action,
                        self._get_previous_bids(),
                        self._get_player_position(player),
                        self._bidding_phase,
                    ):
                        yield action
                else:
                    yield action

            elif action_type is BurySkat and self._skat is None:
                all_cards = player.hand
                for combo in itertools.combinations(all_cards, 2):
                    yield BurySkat(combo)

            elif action_type is DeclareGame and self._skat is not None:
                # TODO: also use hand, ouvert, etc.
                for gt in [
                    GameType.DIAMONDS,
                    GameType.HEARTS,
                    GameType.SPADES,
                    GameType.CLUBS,
                    GameType.GRAND,
                    GameType.NULL,
                ]:
                    if self._rule_set.is_valid_game_declaration(
                        player, self._bid or 0, gt, self._hand_available
                    ):
                        yield DeclareGame(gt, self._hand_available)

    def _advance_turn(self, action: Action):
        if isinstance(action, GiveUp):
            if self._game_result < 0:
                self._phase = GamePhase.LOST
            else:
                self._phase = GamePhase.WON
            return

        if self._phase == GamePhase.BID:
            self._advance_bidding(action)
            return

        if isinstance(action, PlayCard):
            self._active_player = (self._active_player + 1) % 3
            if len(self._trick_history) == 10:
                self._game_result = self.calculate_game_score()
                self._phase = GamePhase.WON if self._game_result > 0 else GamePhase.LOST
            return

        if isinstance(action, DealCards):
            self._phase = GamePhase.BID
            self._active_player = self._middlehand
            return

        if isinstance(action, DeclareGame):
            self._phase = GamePhase.PLAYING
            self._active_player = self._forehand
            return

    def _advance_bidding(self, action: Action):
        player = self._active_player

        passes = len([p for p, a in self._get_previous_bids() if isinstance(a, Pass)])

        # If 2 passes happened and third is now, set game to passed
        if passes == 3:
            self._game_type = GameType.PASS
            self._phase = GamePhase.PASSED
        # If others passed, bid implies declaration
        if passes == 2 and isinstance(action, DeclareBid):
            self._phase = GamePhase.DECLARATION
            self._declarer = self._active_player
            return

        if self._bidding_phase is BiddingPhase.ForehandMiddlehand:
            # Pass switch to other phase
            if isinstance(action, Pass):
                self._active_player = self._backhand
                if player == self._forehand:
                    self._bidding_phase = BiddingPhase.MiddlehandBackhand
                else:
                    self._bidding_phase = BiddingPhase.ForehandBackhand

            # If not passed, alternate between forehand and middlehand
            else:
                if player == self._forehand:
                    self._active_player = self._middlehand
                elif player == self._middlehand:
                    self._active_player = self._forehand
            return

        elif self._bidding_phase is BiddingPhase.ForehandBackhand:
            # Alternate between forehand and backhand
            if player == self._forehand:
                self._active_player = self._backhand
            else:
                self._active_player = self._forehand
        elif self._bidding_phase is BiddingPhase.MiddlehandBackhand:
            # Alternate between middlehand and backhand
            if player == self._middlehand:
                self._active_player = self._backhand
            else:
                self._active_player = self._middlehand

        other_has_bid = any(
            isinstance(a, (DeclareBid, Listen))
            for p, a in self._get_previous_bids()
            if p != player
        )

        if passes == 2 and other_has_bid:
            self._phase = GamePhase.DECLARATION
            self._declarer = self._active_player

    def serialize(self) -> dict[str, Any]:
        return {
            "phase": self._phase.value,
            "active_player": self._active_player,
            "bid": self._bid or 0,
            "game_type": self._game_type.value,
            "player_hands": [[c.uid for c in p.hand] for p in self._players],
            "trick": [c.uid for c in self._trick.cards],
            "skat": [c.uid for c in self._skat] if self._skat else [],
            "points": [self._points[p] for p in self._players],
            "declarer": self._declarer if self._declarer is not None else -1,
        }

    def _get_previous_bids(self) -> list[tuple[Player, DeclareBid | Listen | Pass]]:
        """
        Return the previous bids (filters _action_history).
        """
        bid_history: list[tuple[Player, DeclareBid | Listen | Pass]] = []
        for p, a in self._action_history:
            if (
                isinstance(a, DeclareBid)
                or isinstance(a, Listen)
                or isinstance(a, Pass)
            ):
                bid_history.append((p, a))
        return bid_history

    def _get_player_position(self, player: Player) -> PlayerPosition:
        """
        Return the player position during bidding.
        """
        if player == self._players[self._forehand]:
            return PlayerPosition.FOREHAND
        if player == self._players[self._middlehand]:
            return PlayerPosition.MIDDLEHAND
        return PlayerPosition.BACKHAND
