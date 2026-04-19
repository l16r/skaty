# Architecture

In order to achieve extensibility, skaty strictly separates the rule set from the game state.

Every game is represented by a [game state](#game-state) with an associated [rule set](#rule-set).
A game's state is modified by applying/undoing [actions](#actions) following the Command Pattern.

## Game State

The `GameState` class contains all state of a specific game instance.

It acts as a base class containing attributes used in any variation of Skat. It can be extended to contain more attributes if needed by the rule set (see tutorial [Creating Rule Sets and Actions](./tutorials/creating-rule-sets-actions.md)).

For example `ISkOGameState` extends `GameState` to contain, among others, information about the current bidding phase, the highest bid and last bid.

### State modification

The game state should **never** be directly mutated by the user. Instead, state changes are delegated to actions and the rule set.

For example:

```python
from skaty.isko.actions import Pass
from skaty.isko.rules import ISkO
from skaty.isko.state import ISkOGameState

game = ISkOGameState.from_random_deal(ISkO(), 0)
action = Pass(2)

# This will add the action to game.action_history, make sure it is reversible and advance the state.
game.apply_action(action)

# The action can also be undone easily
# Remove it from game.action_history, reverse state changes exactly.
game.undo_action()
```

## Rule Set

The rule set, along with [actions](#actions), formsw the core of the game logic. It acts as a static, stateless engine that defines h the game flows.

By default, skaty provides an `AbstractRuleSet` with the necessary interfaces (e.g. `is_valid_action`, `get_valid_actions`, `advance_state` etc.).

For usage in interanl methods, rule sets need no know about the game state it is applied to. Therefore, generics are used.

## Actions

Actions represent discrete choices made by the players (e.g. `PlayCard`, `DeclareBid`).

Actions are stateless and immutable. The previous state is pushed to the `GameState.undo_memory` stack.
