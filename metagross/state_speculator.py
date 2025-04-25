import json
import random


FILLER_POKEMON = json.load(open("metagross/export/filler_pokemon.json", "r"))


def speculate(game_state):
    """Accepts a gamestate object and then populates unknown elements. Specifically:
    1. If not all pokemon on a team are known, new random pokemon will be added.
    2. If not all moves on a pokemon are known, moves will be added using the random sets as reference.
    3. If not all EVs/IVs/stats are known, they will be populated using random sets as reference.
    4. If a stat is estimated, it will be given a random value at either extreme of the estimate (?)
    """

    return add_unknown_pokemon(game_state)


def add_unknown_pokemon(game_state):
    for side in game_state:
        current_pokemon_count = len(side["pokemon"])
        if current_pokemon_count < 6:
            needed_pokemon = 6 - current_pokemon_count
            additional_pokemon = random.sample(FILLER_POKEMON, needed_pokemon)
            side["pokemon"].extend(additional_pokemon)
    return game_state
