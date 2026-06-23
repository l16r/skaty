# Creating Rule Sets and Actions

Preread: Look at the frameworks [architecture](../architecture.md).

In this tutorial, we will implement simple card game with 3 tricks. Its _not_ full Skat (which you don't need to write, because you can just [extend](./extending-rule-sets.md) the implemented ISkO), just playing Cards in tricks with simple scoring.

## The Game

- cards are played in tricks of 3
- cards are ranked according to: clubs > spades > hearts > diamonds; Ace > 10 > King > Queen > 9 > 8 > 7 in each suit
- the winner of the trick gets points of the cards (same as ISkO suit game)
- winner is the player with most points after 10 tricks

We wont bother bidding or using the Skat.

## Looking at the Cards

Cards are a pair of Suit (diamonds, hearts, spades, clubs) and Rank (7, 8, 9, 10, Jack, Queen, King, Ace).
They are cached to save time, so every `Card(Rank.JACK, Suit.CLUBS)` will point to the same memory. This wont matter if the game is Skat-like, i.e. 32 cards with 3 player tricks plus some logic.
A deck is instantiated by:

```python
from skaty.cards import create_deck, shuffle_deck

deck = create_deck()
shuffled = shuffle_deck(deck)
```

However, for simplicity, we will use the class method `GameState.from_random_deal` that calls the functions under the hood.

Let's get to the game.

## The Game State

The game state contains every attribute of one game.

```python
from skaty.game_state import GameState

game = GameState.from_random_deal(RULE_SET, 2, True)
print(f"{game.active_player} is active")
print(f"history: {game.action_history}")
```

We can also extend the game state as shown [here](/docs/tutorials/extending-rule-sets.md#implementing-it).
However, the problem at hand, is the lack of rule set. We want to create a rule set, not extend one.

## The Rule Set

The rule set must implement the `AbstractRuleSet` class over a generic `GameState`.
The `AbstractRuleSet` defines basic methods for advancing the game state and checking game logic.
We will implement them later.

### Actions

Actions _act_ on `GameState` via a rule set. An `Action` is also an abstract base class over a generic `GameState` with the methods:

- `is_valid(state: TState, rule_set: AbstractRuleSet[TState]) -> bool`: check legality of action during state according to rule set
- `apply(state: TState, rule_set: AbstractRuleSet[TState]) -> None`: in place modify game state
- `undo(state: TState) -> None`: reverse action applied previously, restoring state exactly in place

For our game, we will need a `PlayCard` action.

#### Playing Cards

Now, we will need to implement the `apply` and `undo` method. `is_valid` is just a wrapper for `rule_set.is_valid_action`.

Playing a card means removing the card from hand, possibly advancing the trick and phase. Undoing is just the reverse.

```python
# exp/actions.py
# Define a new action on GameState.
from dataclasses import dataclass
from skaty.cards import Card
from skaty.game_state import GameState
from skaty.rules import AbstractRuleSet, Action


@dataclass(frozen=True)
class PlayCard(Action[GameState]):
    """Play specific card."""

    # Attributes for the action.
    card: Card

    # Core of action. Apply the action on a specific state and rule set. Can store memory for undoing.
    def apply(self, state: GameState, rule_set: AbstractRuleSet[GameState]) -> None:
        # Playing the third card finishes the trick.
        trick_finishes = len(state.current_trick.cards) == 2

        # Store previous state for undo().
        state.undo_memory.append(
            {
                "active_player": state.active_player,
                "points": state.points.copy(),
                "trick_finishes": trick_finishes,
                "phase": state.phase,
            }
        )

        # Remove card from hand
        state.hands[self.player_idx].remove(self.card)

        # Advance state via rule set. See below.
        rule_set.advance_state(state, self)

    # Restore the previous state exactly.
    def undo(self, state: GameState) -> None:
        # Get previously stored state.
        memory = state.undo_memory.pop()

        # Reset state.
        state.hands[self.player_idx].append(self.card)
        state.active_player = memory["active_player"]
        state.points = memory["points"]
        state.phase = memory["phase"]

        # Restore trick if it finished.
        if memory["trick_finishes"]:
            state.current_trick = state.trick_history.pop()

        # Remove card from trick.
        state.current_trick.pop()
```

With that finished, let's look at the rule set.

### Implementing Rules

A ruleset must implement the `AbstractRuleSet` base class over a generic game state with a few methods.
For reference look at the [docs](https://l16r.github.io/skaty/api/#skaty.rules.AbstractRuleSet).

```python
# exp/rules.py
```
