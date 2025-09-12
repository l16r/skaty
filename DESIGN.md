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
class Player {
  - name: str
  - hand: list[Card]
  + getName(): str
  + getHand(): list[Card]
  + addCard(card: Card)
  + removeCard(card: Card): Card
}
abstract class AbstractRuleSet {
  + {abstract} game_type(): GameType
  + {abstract} trump_suit(): Optional[Suit]
  + {abstract} is_card_trump(card: Card): bool
  + {abstract} get_card_effective_rank_value(card: Card): int
  + {abstract} determine_trick_winner(cards_in_trick: list[tuple[Card, Player]]): Player
  + {abstract} calculate_game_score(players: list[Player], tricks: list[Trick]): int
  + {abstract} isValidAction(player: Player, action: Action): bool
  + {abstract} isValidBid(player: Player, action: Action, bid: int): bool
  + {abstract} isValidCardPlay(player: Player, card: Card): bool
  + {abstract} isValidGameDeclaration(player: Player, action: Action, bid: int, game_type: GameType, hand: bool, schneider: bool, schwarz: bool, open: bool): bool
}
class StandardSkatRuleSet {
}
class GameState {
  - players: list[Player]
  - rule_set: AbstractRuleSet
  - current_trick: Optional[Trick]
  - trick_history: list[Trick]
  - action_history: list[tuple[int, Player, Action]]
  + startGame()
  + apply_action(player: Player, action: Action): bool
  + isGameOver(): bool
  + calculateFinalScore(): int
  + possibleActions(player: Player): list[Action]
  + reverseLastAction()
}
class Trick {
  - cards: list[tuple[Card, Player]]
  + addCard(card: Card, player: Player)
  + isComplete(): bool
  + getWinner(rule_set: AbstractRuleSet): Player
  + getTrickPoints(): int
}
enum Action {
  PLAY_CARD
  DRAW_SKAT
  BURY_SKAT
  DECLARE_BID
  LISTEN
  PASS
  DECLARE_GAME
  GIVE_UP
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
GameState "1" -- "0..*" Action: consists of
Player "0..*" -- "1" GameState : controls
Card "1" -- "1" Rank : contains
Card "1" -- "1" Suit : contains
Player "1" *-- "0..10*" Card : has
Trick "1" *-- "0..3" Card : contains
Trick "1" -- "1" Player : led by
GameState "1" *-- "3" Player : has
GameState "1" *-- "1" AbstractRuleSet : uses
GameState "1" *-- "0..1" Trick : current
GameState "1" *-- "0..*" Trick : history

StandardSkatRuleSet ..|> AbstractRuleSet

AbstractRuleSet ..> Card
AbstractRuleSet ..> Player
AbstractRuleSet ..> GameType
AbstractRuleSet ..> Trick
@enduml
```
