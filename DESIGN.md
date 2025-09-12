```
@startuml
class Card {
  - _rank: Rank
  - _suit: Suit
  + @property rank(): Rank
  + @property suit(): Suit
  + @property points(): int
  + __eq__(other: Card): bool
  + __str__(self): str
  + __repr__(self): str
  + __hash__(self): int
}
class Player {
  - _name: str
  - _hand: List<Card>
  + getName(): str
  + getHand(): List<Card>
  + addCard(card: Card)
  + removeCard(card: Card): Card
}
abstract class AbstractRuleSet {
  + {abstract} game_type(): GameType
  + {abstract} trump_suit(): Optional[Suit]
  + {abstract} is_card_trump(card: Card): bool
  + {abstract} get_card_effective_rank_value(card: Card): int
  + {abstract} determine_trick_winner(cards_in_trick: List<(Card, Player)>, leading_card: Card): Player
  + {abstract} calculate_game_score(list[Player], list[Trick]): int
  + {abstract} isValidAction(Player, Action): bool
  + {abstract} isValidBid(Player, Action, int): bool
  + {abstract} isValidCardPlay(Player, Action, Card): bool
  + {abstract} isValidGameDeclaration(Player, Action, int, GameType, bool, bool, bool, bool): bool
}
class StandardSkatRuleSet {
}
class GameState {
  - _players: list[Player]
  - _rule_set: AbstractRuleSet
  - _current_trick: Optional[Trick]
  - _trick_history: list[Trick]
  - _action_history: list[tuple[int, Player, Action]]
  + startGame()
  + apply_action(Player, Action): bool
  + isGameOver(): bool
  + calculateFinalScore(): int
  + possibleActions(Player): list[Action]
  + reverseLastAction()
}
class Trick {
  - _cards_played: list[tuple[Card, Player]]
  - _leading_player: Player
  - _leading_card: Optional<Card>
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
  CLUBS
  SPADES
  HEARTS
  DIAMONDS
  GRAND
  NULL
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
