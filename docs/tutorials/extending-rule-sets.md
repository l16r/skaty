# Extending Rule Sets

In this tutorial, we will extend the ISkO with basic Ramsch rules.

## The Rules

- The Ramsch will be triggered if all players pass.
- The cards are played like in a normal Grand, i.e. only Jacks are trump.
- The player with the most points is considered the loser. In case two or three players have equal points, all are losers.
- A player taking no tricks is considered Jungfrau.
- If a player takes all tricks, he makes a Durchmarsch.
- If a player makes a Durchmarsch, he has a score of +120
- The losers with p points will have a score of -p. If a player is Jungfrau, they will have a score of -2\*p.

## Implementing it

As said before, we will extend ISkO.

Let's first create the structure:

```
extensions/
  state.py # Contains the game type and state
  rules.py # Contains the modified game logic
```

The `state.py` is simple. ISkO does not specify a Ramsch `GameType`, so we need to create one.
We do not need to store additional attributes in the game state, but for good measure let's create a specific Ramsch game state.

`state.py` looks like this

```python linenums="1"
from skaty.isko.state import ISkOGameState, ISkOGameTypes
from skaty.rules import GameType


# Create new game types.
# Inherit the types provided by ISkO (all suits, grand and null).
class RamschGameTypes(ISkOGameTypes):
    # Cast the string as GameType for type checking
    RAMSCH = GameType("ext:ramsch")


# Inherit all additional state changes from ISkO.
# We do not need additional attributes.
class RamschGameState(ISkOGameState):
    pass
```

Now to the more complicated part.
We want to trigger switching `game.game_type` to `RamschGameTypes.RAMSCH` if a game is passed.

```python linenums="1"
from typing import TypeVar
from extensions.ramsch.state import RamschGameState, RamschGameTypes
from skaty.isko.rules import ISkO
from skaty.rules import Action, GameTypes, GamePhases

# Create a new generic for RamschGameState to allow further extension.
T_RamschGameState = TypeVar("T_RamschGameState", bound=RamschGameState)

# Create a custom rule set by extending the standard ISkO rules.
# By passing "T_RamschGameState" as a type argument, we bind the generic base class to our custom state.
# This guarantees strict type safety and full IDE autocomplete in all overridden methods.
# In this case, it makes no difference, because T_RamschGameState adds no attributes.
# You could also just pass RamschGameState, but then RamschRules will not be extensible with new game states.
class RamschRules(ISkO[T_RamschGameState]):
# Override the advance_state method called by every action on apply.
    def advance_state(self, state: T_RamschGameState, action: Action) -> None:
        # Let ISkO advance the state first. This will handle bidding, declaration and playing.
        super().advance_state(state, action)

        # If every player passes, game type will be set to PASS.
        if state.game_type == GameTypes.PASS:
            # Start the Ramsch
            state.phase = GamePhases.PLAYING
            state.game_type = RamschGameTypes.RAMSCH
            state.active_player = state._forehand
```

The playing phase will be handled by ISkO. We just need to change score calculation.

```python linenums="1"
from typing import TypeVar
from extensions.ramsch.state import RamschGameState, RamschGameTypes
from skaty.isko.rules import ISkO
from skaty.rules import Action, GameTypes, GamePhases

# Add InvalidGameStateError
from skaty.exceptions import InvalidGameStateError

T_RamschGameState = TypeVar("T_RamschGameState", bound=RamschGameState)

class RamschRules(ISkO[T_RamschGameState]):
    def calculate_game_score(self, state: T_RamschGameState) -> list[int]:
        # We can only calculate a score if the game is finished.
        # This is also handled by ISkO.calculate_game_score, but we can't call it now, but it would throw because there is no bid, no declaration and no tops.
        # So we will check it first.
        if state.phase != GamePhases.GAME_OVER:
            raise InvalidGameStateError("A game has no score if it is not finished.")

        # We only want to add score calculation for Ramsch.
        if state.game_type == RamschGameTypes.RAMSCH:
            # See rules
            jungfrauen = sum([1 for t in state.tricks_won if t == 0])
            # Two players taking no tricks is equivalent to one player taking all tricks.
            durchmarsch = jungfrauen == 2

            if durchmarsch:
                # If a player took all tricks, he must have 120 points and the others must have 0
                return state.points

            # jungfrauen can now only be one, because it can be either be 2 (Durchmarsch, handled above) or 1
            multiplier = jungfrauen + 1
            max_points = max(state.points)
            # Only keep the maximal points for the losers. Make them negative and multiply them by two if Jungfrau. Others get 0 points.
            scores = [
                -multiplier * max_points if i == max_points else 0 for i in state.points
            ]
            return scores

        # For every other game type, let ISkO handle it.
        return super().calculate_game_score(state)

    def advance_state(self, state: T_RamschGameState, action: Action) -> None:
        super().advance_state(state, action)

        if state.game_type == GameTypes.PASS:
            state.phase = GamePhases.PLAYING
            state.game_type = RamschGameTypes.RAMSCH
            state.active_player = state._forehand
```

## Using it

Using our new rule set is with the exception of using the new classes, the same as in the [Getting Started](../getting-started.md).

```python linenums="1"
import random

from extensions.ramsch.rules import RamschRules
from extensions.ramsch.state import RamschGameState
from skaty.isko.actions import DeclareBid, Pass
from skaty.rules import GamePhases

# Use our new Rules instead of ISkO
rule_set = RamschRules()
# For simplicity, set dealer to 0
dealer = 0
game = RamschGameState.from_random_deal(rule_set, dealer, log=True)

# Ramsch game
print("Start Ramsch game")

# We can still use ISkO's actions.
# All players pass to trigger a Ramsch game.
game.apply_action(Pass(2))
game.apply_action(Pass(0))
game.apply_action(Pass(1))

# We will play exactly 30 cards
for _ in range(30):
    active_p = game.active_player
    actions = list(game.get_valid_actions(active_p))

    action = random.choice(actions)

    game.apply_action(action)

# Print result
print(game.calculate_game_score())

print("-" * 20)
print("UNDOING")

# Now let's undo all actions and start a suit game.
for _ in range(33):
    game.undo_action()

print("-" * 20)
print("Start non-Ramsch game with the same rule set")

# Make at least one bid to force non-Ramsch game.
game.apply_action(DeclareBid(2, 18))

# This is the same as in Getting Started
while game.phase != GamePhases.GAME_OVER:
    active_p = game.active_player
    actions = list(game.get_valid_actions(active_p))

    action = random.choice(actions)

    game.apply_action(action)

print(
    f"Game ended with score {game.calculate_game_score()[game.declarer_idx]} for player {game.declarer_idx}"
)

```
