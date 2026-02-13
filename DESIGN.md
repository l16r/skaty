## State-Machine

For `GameState._phase` with repeated `GameState.apply_action(...)`.

```
@startuml
state "PRE_DEAL" as predeal
state "BID" as bid
state "PASSED" as passed
state "DECLARATION" as declaration
state "PLAYING" as playing
state "LOST" as lost
state "WON" as won

predeal --> bid: Action.DEAL_CARDS
bid --> bid: Action.DECLARE_BID
bid -> passed: Action.DECLARE_BID
bid --> declaration: Action.DECLARE_BID
declaration --> declaration: Action.DRAW_SKAT
declaration --> declaration: Action.BURY_SKAT if Action.DRAW_SKAT
declaration --> playing: Action.DECLARE_GAME
declaration --> lost: Action.PASS
playing --> playing: Action.PLAY_CARD
playing --> lost: Action.GIVE_UP 2x
playing --> won: Action.GIVE_UP 2x
playing --> lost: Action.PLAY_CARD
playing --> won: Action.PLAY_CARD
@enduml
```

## Class Diagram

```
@startuml
enum Rank {
  SEVEN=7
  EIGHT=8
  NINE=9
  TEN=10
  JACK=11
  QUEEN=12
  KING=13
  ACE=14
  + @property points(): int
}

enum Suit {
  DIAMONDS=0
  HEARTS=1
  SPADES=2
  CLUBS=3
}

class Card {
  - rank: Rank
  - suit: Suit
  + @property rank(): Rank
  + @property suit(): Suit
  + @property points(): int
  + __init__(rank: Rank, suit: Suit)
  + __eq__(other: Card): bool
  + __str__(): str
  + __repr__(): str
  + __hash__(): int
}

class ComparableCard {
  + card: Card
  + rule_set: AbstractRuleSet
  + __lt__(other: object): bool
  + __eq__(other: object): bool
}

class Player {
  - name: str
  - hand: list[Card]
  - played_cards: list[Card]
  + @property name(): str
  + @property hand(): list[Card]
  + __init__(name: str, hand: Optional[list[Card]] = None)
  + __str__(): str
  + __repr__(): str
  + all_cards(): list[Card]
  + add_card(card: Card)
  + add_cards(cards: list[Card])
  + play_card(card: Card)
}

abstract class AbstractRuleSet {
  + {abstract} game_type(): GameType
  + {abstract} set_game_type(v: GameType)
  + {abstract} trump_suit(): Optional[Suit]
  + {abstract} is_card_trump(card: Card): bool
  + {abstract} tops(cards: list[Card]): int
  + {abstract} get_card_effective_rank_value(card: Card): int
  + {abstract} determine_trick_winner(trick: list[Card]): int
  + {abstract} calculate_game_score(players: list[Player], declarer: int, points: dict[Player, int], tricks: list[tuple[Trick, Player]], game_type: GameType, bid: int, skat: tuple[Card,Card], hand: bool=False, schneider_announced:bool=False, schwarz_announced:bool=False, ouvert:bool=False): int
  + {abstract} is_valid_action(action: Action, phase: GamePhase): bool
  + {abstract} get_action_types_for_phase(phase: GamePhase): list[type[Action]]
  + {abstract} get_next_valid_bid(current_bid: Optional[int]): int
  + {abstract} is_valid_bid(player: Player, bid: DeclareBid | Listen | Pass, previous_bids: list[tuple[Player, DeclareBid | Listen | Pass]], player_pos: PlayerPosition, bidding_phase: BiddingPhase): bool
  + {abstract} is_valid_card_play(player: Player, card: Card, first_card: Optional[Card]): bool
  + {abstract} is_valid_game_declaration(player: Player, bid: int, game_type: GameType, hand: bool, schneider: bool=False, schwarz: bool=False, open: bool=False, hand_available: bool=True): bool
}

class ISkO {
}

class GameState {
  - players: list[Player]
  - active_player: int
  - trick: Trick
  - rule_set: AbstractRuleSet
  - game_type: GameType
  - trick_history: list[tuple[Trick, Player]]
  - action_history: list[tuple[Player, Action]]
  - bid: Optional[int]
  - bidding_phase: BiddingPhase
  - phase: GamePhase
  - skat: Optional[tuple[Card, Card]]
  - points: dict[Player, int]
  - hand_available: bool
  - game_result: int
  - declarer: Optional[int]
  - declaration: tuple[bool, bool, bool, bool]
  - log: bool
  + __init__(players: list[Player], rule_set: AbstractRuleSet, dealer: int, log: bool=False)
  + @property active_player(): Player
  + calculate_game_score(): int
  + apply_action(player: Player, action: Action): bool
  + get_valid_actions(player: Player): list[Action]
  - advance_turn(action: Action)
  - advance_bidding(action: Action)
  - get_previous_bids() -> list[tuple[Player, DeclareBid | Listen | Pass]]
  - get_player_position(player: Player): PlayerPosition
}

class Trick {
  - cards: list[Card]
  + @property first_card(): Optional[Card]
  + add_card(card: Card)
  + is_complete(): bool
  + get_winner(rule_set: AbstractRuleSet): int
  + get_trick_points(): int
}

enum PlayerPosition {
  FOREHAND
  MIDDLEHAND
  BACKHAND
}

enum BiddingPhase {
  ForehandMiddlehand
  ForehandBackhand
  MiddlehandBackhand
}

enum GamePhase {
  PRE_DEAL
  BID
  PASSED
  DECLARATION
  PLAYING
  LOST
  WON
}

enum ActionType {
  DEAL_CARDS
  PLAY_CARD
  DRAW_SKAT
  BURY_SKAT
  DECLARE_BID
  LISTEN
  PASS
  DECLARE_GAME
  GIVE_UP
}

class Action {
  + @property type(): ActionType
}

class PlayCard {
  + card: Card
}
class BurySkat {
  + cards: tuple[Card, Card]
}
class DeclareBid {
  + bid: int
}
class Listen {
}
class Pass {
}
class DeclareGame {
  + game_type: GameType
  + hand: bool
  + schneider: bool=False
  + schwarz: bool=False
  + open: bool=False
}
class GiveUp {
}

enum GameType {
  PASS=0
  DIAMONDS=9
  HEARTS=10
  SPADES=11
  CLUBS=12
  NULL=23
  GRAND=24
}

Player "1" -- "1" GameState : active player
Player "0..*" -- "1" GameState : controls
Player "1" *-- "0..10*" Card : has
Card "1" -- "1" Rank : contains
Card "1" -- "1" Suit : contains
Trick "1" *-- "0..3" Card : contains
Trick "1" -- "1" Player : led by
GameState "1" *-- "3" Player : has
GameState "1" *-- "1" AbstractRuleSet : uses
GameState "1" *-- "0..1" Trick : current
GameState "1" *-- "0..*" Trick : history
GameState "1" -- "0..*" Action: consists of
GameState "0..*" -- "1" GamePhase: is in

ISkO ..|> AbstractRuleSet

Action "0..*" -- "1" ActionType: type
PlayCard  --|> Action
BurySkat  --|> Action
DeclareBid  --|> Action
Listen  --|> Action
Pass  --|> Action
DeclareGame  --|> Action
GiveUp  --|> Action

ComparableCard ..> Card

AbstractRuleSet ..> Card
AbstractRuleSet ..> Player
AbstractRuleSet ..> GameType
AbstractRuleSet ..> Trick
@enduml
```
