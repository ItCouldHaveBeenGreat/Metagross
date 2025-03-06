import json
import logging
import re
import typing

PLACEHOLDER_ITEM = "unknown_item"
PLACEHOLDER_ABILITY = "unknown_ability"
PLACEHOLDER_MOVE = "unknown_move"
NONE_ITEM = ""  # This is how the |request json represents it :shrug:
HOME_PLAYER = 0  # Which player id we are; this is whatever player id the request objects show up for


MOVE_ID_TO_MOVE = json.load(open("metagross/export/moves_export.json", "r"))
MOVE_NAME_TO_ID = {
    move_data["name"]: move_id for move_id, move_data in MOVE_ID_TO_MOVE.items()
}


def parse_log(log_lines: list[str]) -> dict:
    state = {
        "sides": [
            {
                "name": "",
                "pokemon": [],
                "team": "123456",  # TODO: this probably needs to be different for doubles
            },
            {
                "name": "",
                "pokemon": [],
                "team": "123456",  # TODO: this probably needs to be different for doubles
            },
        ]
    }

    # It's easier to deal with the pokemon when they're keyed ident -> pokemon dict
    # At the end of the process, we'll convert them into the arrays required by state
    pokemon_data = {}

    for log_group in log_lines:
        # Logs can be grouped; split them!
        for log in log_group.split("\n"):
            # Not all logs contain state information; skip them!
            if not "|" in log:
                continue

            parts = log.split("|")
            # logging.warning(parts)

            log_type = parts[1]
            if log_type in ["", "start", "upkeep"]:
                # No-op lines can show up
                continue

            # TODO: This is a lot of hassle... maybe add an allow list on log_type?
            ident = __get_ident(parts[2])
            player_id = __get_player_id_from_ident_or_default(parts[2], -1)
            # The request log is specially formatted and needs to be parsed differently
            if "request" == log_type:
                player_id, pokemon_array = __parse_request_to_pokemon_array(log)
                # TODO: Instead of straight assignment, this needs to be structured so it doesn't overwrite boosts, move pp, etc
                for pokemon in pokemon_array:
                    pokemon_data[pokemon["ident"]] = pokemon
                continue

            if "player" == log_type:
                state["sides"][player_id]["name"] = parts[3]

            # Boosts AREN'T captured by the request object, so we still need to record them
            if "-boost" == log_type:
                stat = parts[3]
                amount = int(parts[4])
                if "boosts" not in pokemon_data[ident]:
                    pokemon_data[ident]["boosts"] = {}
                if stat not in pokemon_data[ident]["boosts"]:
                    pokemon_data[ident]["boosts"][stat] = 0
                pokemon_data[ident]["boosts"][stat] += amount

            if "-damage" == log_type:
                # TODO: Damage gives us an opportunity to infer the stats of the away team pokemon; add some calcs!
                condition = parts[3]
                pokemon_data[ident]["condition"] = condition
                pokemon_data[ident]["hp"] = __get_hp_from_condition(condition)

            if "move" == log_type:
                move = parts[3]
                # TODO: Add a lookup for PP here and then track it, assuming maxpp
                # TODO: We still need to track pp for the home player
                if move not in pokemon_data[ident]["moves"]:
                    pokemon_data[ident]["moves"].append(move)

            # The |request log supersedes most of the other logs, but we only have them for the home player
            if player_id != HOME_PLAYER:
                if "-item" == log_type:
                    item = parts[3]
                    pokemon_data[ident]["item"] = item

                if "-ability" == log_type:
                    ability = parts[3]
                    pokemon_data[ident]["ability"] = ability

                if "-enditem" == log_type:
                    pokemon_data[ident]["item"] = NONE_ITEM

                if "-heal" == log_type:
                    condition = parts[3]
                    pokemon_data[ident]["condition"] = condition
                    pokemon_data[ident]["hp"] = int(condition.split("/")[0])

                if "faint" == log_type:
                    # TODO: Zero out the boosts, and maybe other state?
                    if ident in pokemon_data:
                        pokemon_data[ident]["condition"] = "0 fnt"
                        pokemon_data[ident]["hp"] = 0

                if "detailschange" == log_type:
                    details = parts[3]
                    if ident in pokemon_data:
                        pokemon_data[ident]["details"] = details

                if "switch" == log_type or "drag" == log_type:
                    details = parts[3].split(", ")
                    species = details[0]
                    level = int(details[1][1:])
                    gender = details[2] if len(details) > 2 else ""
                    condition = parts[4]
                    hp, max_hp = map(int, condition.split("/"))

                    # TODO: There's a lot of common code/schema between this and request!
                    pokemon = {
                        "ident": ident,
                        "species": species,
                        "level": level,
                        "gender": gender,
                        "condition": condition,
                        "hp": hp,
                        "max_hp": max_hp,
                        "item": PLACEHOLDER_ITEM,
                        "ability": PLACEHOLDER_ABILITY,
                        "moves": [],
                        "baseStoredStats": {},
                        "storedStats": {},
                        "boosts": {
                            "atk": 0,
                            "def": 0,
                            "spa": 0,
                            "spd": 0,
                            "spe": 0,
                            "accuracy": 0,
                            "evasion": 0,
                        },
                        "details": "",
                    }
                    pokemon_data[ident] = pokemon

    # Load all of the finalized pokemon into the state arrays
    for pokemon in pokemon_data.values():
        player_id = int(pokemon["ident"][1]) - 1
        state["sides"][player_id]["pokemon"].append(pokemon)

    return state


def __parse_request_to_pokemon_array(log: str) -> typing.Tuple[int, list]:
    parts = log.split("|", 2)
    request_data = json.loads(parts[2])
    side_data = request_data.get("side", {})
    player_id = int(side_data.get("id", "p1")[1]) - 1

    pokemons = []
    for pokemon in side_data.get("pokemon", []):
        ident = pokemon["ident"]
        stats = pokemon.get("stats", {})
        pokemon_entry = {
            "ident": ident,
            "species": pokemon["details"].split(", ")[0],
            "level": int(pokemon["details"].split(", ")[1][1:]),
            "gender": (
                pokemon["details"].split(", ")[2]
                if len(pokemon["details"].split(", ")) > 2
                else ""
            ),
            "condition": pokemon["condition"],
            "hp": __get_hp_from_condition(pokemon["condition"]),
            "max_hp": __get_max_hp_from_condition(pokemon["condition"]),
            "item": pokemon.get("item", NONE_ITEM),
            "ability": pokemon.get("ability", PLACEHOLDER_ABILITY),
            "moves": pokemon.get("moves", []),
            "baseStoredStats": stats,
            "storedStats": stats,
            "boosts": {
                "atk": 0,
                "def": 0,
                "spa": 0,
                "spd": 0,
                "spe": 0,
                "accuracy": 0,
                "evasion": 0,
            },
            "details": pokemon["details"],
        }
        pokemons.append(pokemon_entry)
    return player_id, pokemons


def __get_ident(ident_string) -> str:
    # The idents either come in the form of 'p1a: Skarmory' or 'p1: Skarmory'. The 'a' denotes battlefield position
    if ident_string != None and len(ident_string) > 2:
        if ident_string[2] == ":":
            return ident_string
        else:
            return ident_string[:2] + ident_string[3:]
    return ""


def __get_position(ident_string) -> str:
    return "TODO: implement me!"


def __get_player_id_from_ident_or_default(ident: str, default: int) -> int:
    if ident != None and len(ident) >= 2:
        return int(ident[1]) - 1 if ident[1].isdecimal() else default
    return default


def __get_hp_from_condition(condition: str) -> int:
    return 0 if condition == "0 fnt" else int(condition.split("/")[0])


def __get_max_hp_from_condition(condition: str) -> int:
    # NOTE: I don't think it'll matter, but 100 isn't actually correct for p1's pokemon
    return 100 if condition == "0 fnt" else int(condition.split("/")[0])
