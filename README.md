# skaty

An extensible, high-performance [Skat](<https://en.wikipedia.org/wiki/Skat_(card_game)>) implementation in Python.

It provides a robust core engine and includes a reference implementation of the [International Skat Order (ISkO)](https://ispacanada.org/docs/rules/505fc8_e561984976a345bc8404e4474ce066ef.pdf).

## Features

- **ISkO compliant**: strict adherence to official rules
- **Extensible**: easily implement house rules
- **AI-Ready**: built with fast, allocation-friendly `apply`/`undo` architecture, making it perfectly suited for reinforcement learning
- **Type Safe**: Fully typed and designed for modern Python

## Documentation

A comprehensive documentation covering architecture, tutorials and API references can be found [here](https://l16r.github.io/skaty/).

## Quickstart

### Installation

skaty is on PyPI. Install it with your favorite package manager. For example:

```
pip install skaty
```

### Usage - Random game

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

For more information about ISkO or implementing your own rules, consult the [documentation](#documentation).

## Testing

Tests are written with pytest.

Run them with:

```
poetry run pytest
```

## Contributing

Contributions are welcome! If you find a bug or want to improve performance, feel free to open an issue or submit a pull request.

## License

MIT License, see [License](/LICENSE) file.
