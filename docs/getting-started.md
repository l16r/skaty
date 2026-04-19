# Getting Started

## Installation

skaty is on PyPI. Install it with your favorite package manager. For example:

```
pip install skaty
```

## Usage: Random Game

skaty separates the rule set from the game state. First instantiate a rule set (e.g. the International Skat Order defined by skaty) and then pass it to the game state.

The `from_random_deal` method requires the dealer index (either 0,1, 2) to determine player positions. Setting `log=True` will print information to the console.

```python
import random

from skaty.isko.rules import ISkO
from skaty.isko.state import ISkOGameState

rule_set = ISkO()
dealer = random.randint(0,2)
game = ISkOGameState.from_random_deal(rule_set, dealer, log=True)
```

The `GameState.get_valid_actions(player_idx)` iterator method yields all legal actions for a given player in the current game state.

Below is a complete example of simulating a random game until it reaches game over.

```python
import random

from skaty.isko.rules import ISkO
from skaty.isko.state import ISkOGameState
from skaty.rules import GamePhases, GameTypes

rule_set = ISkO()
dealer = random.randint(0,2)
game = ISkOGameState.from_random_deal(rule_set, dealer, log=True)

print(f"Player {dealer} deals.")

while game.phase != GamePhases.GAME_OVER:
    active_p = game.active_player
    actions = list(game.get_valid_actions(active_p))

    action = random.choice(actions)

    game.apply_action(action)

if game.game_type == GameTypes.PASS:
    print("Game was passed")
else:
    # If an ISkO game is not passed, it needs to have a declarer.
    print(f"Game ended in phase {game.phase} with score {game.calculate_game_score()[game.declarer_idx]} for player {game.declarer_idx}")
```
