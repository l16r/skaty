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
class Card {
  - rank: Rank
  - suit: Suit
  + @property rank(): Rank
  + @property suit(): Suit
  + @property points(): int
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
  + role: Role
  - name: str
  - hand: list[Card]
  + @property name(): str
  + @property hand(): list[Card]
  + add_card(card: Card)
  + add_cards(cards: list[Card])
  + remove_card(card: Card)
}
enum Role {
  OPPOSITION
  DECLARER
}
abstract class AbstractRuleSet {
  + {abstract} game_type(): GameType
  + {abstract} set_game_type(v: GameType)
  + {abstract} trump_suit(): Optional[Suit]
  + {abstract} is_card_trump(card: Card): bool
  + {abstract} get_card_effective_rank_value(card: Card): int
  + {abstract} determine_trick_winner(cards_in_trick: list[Card]): Player
  + {abstract} calculate_game_score(players: list[Player], tricks: list[Trick]): int
  + {abstract} is_valid_action(player: Player, action: Action): bool
  + {abstract} is_valid_bid(player: Player, bid: int): bool
  + {abstract} is_valid_card_play(player: Player, card: Card, first_card: Optional[Card]): bool
  + {abstract} is_valid_game_declaration(player: Player, bid: int, game_type: GameType, hand: bool, schneider: bool, schwarz: bool, open: bool): bool
}
class StandardSkatRuleSet {
}
class GameState {
  - players: list[Player]
  - active_player: int
  - trick: Trick
  - rule_set: AbstractRuleSet
  - trick_history: list[Trick]
  - action_history: list[tuple[Player, Action]]
  - bid: int
  - phase: GamePhase
  - skat: Optional[tuple[Card, Card]]
  - points: dict[Player, int]
  - hand_available: bool
  + is_game_over(): bool
  + possible_actions(player: Player): list[ActionType]
  + calculate_game_score(): int
  + apply_action(player: Player, action: Action, phase: GamePhase): bool
  + reverse_last_action()
  - advance_turn()
}
class Trick {
  - cards: list[Card]
  + @property first_card(): Optional[Card]
  + add_card(card: Card)
  + is_complete(): bool
  + get_winner(rule_set: AbstractRuleSet): int
  + get_trick_points(): int
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
enum GamePhase {
  PRE_DEAL
  BID
  PASSED
  DECLARATION
  PLAYING
  LOST
  WON
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
  + schneider: bool
  + schwarz: bool
  + open: bool
}
class GiveUp {
}
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
enum GameType {
  DIAMONDS
  HEARTS
  SPADES
  CLUBS
  NULL
  GRAND
  RAMSCH
  PASS
}
Player "0..*" *-- "1" Role: is
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

StandardSkatRuleSet ..|> AbstractRuleSet

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
