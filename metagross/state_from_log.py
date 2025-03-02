import json
import logging
import re

PLACEHOLDER_ITEM = "unknown_item"
PLACEHOLDER_ABILITY = "unknown_ability"
PLACEHOLDER_MOVE = "unknown_move"
NONE_ITEM = "" # This is how the |request json represents it :shrug:


def parse_log(log_lines):
    state = {
        "sides": [
            {
                "name": "",
                "pokemon": []
            },
            {
                "name": "",
                "pokemon": []
            }
        ]
    }

    pokemon_data = {}

    for log_group in log_lines:
        # Logs can be grouped; split them!
        for log in log_group.split("\n"):
            # logging.warning(f"LOG: {log}")
            if "player|" in log:
                parts = log.split("|")
                player_id = int(parts[2][1]) - 1
                state["sides"][player_id]["name"] = parts[3]

            if "|switch|" in log or "|drag|" in log:
                parts = log.split("|")
                player_id = int(parts[2][1]) - 1
                details = parts[3].split(", ")
                ident = parts[2]
                species = details[0]
                level = int(details[1][1:])
                gender = details[2] if len(details) > 2 else ""
                condition = parts[4]
                hp, max_hp = map(int, condition.split("/"))

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
                    "storedStats": {}
                }

                pokemon_data[ident] = pokemon
                state["sides"][player_id]["pokemon"].append(pokemon)

            if "|move|" in log:
                parts = log.split("|")
                ident = parts[2]
                move = parts[3]
                if ident in pokemon_data:
                    if move not in pokemon_data[ident]["moves"]:
                        pokemon_data[ident]["moves"].append(move)

            if "|-item|" in log:
                parts = log.split("|")
                ident = parts[2]
                item = parts[3]
                if ident in pokemon_data:
                    pokemon_data[ident]["item"] = item

            if "|-ability|" in log:
                parts = log.split("|")
                ident = parts[2]
                ability = parts[3]
                if ident in pokemon_data:
                    pokemon_data[ident]["ability"] = ability

            if "|-enditem|" in log:
                parts = log.split("|")
                ident = parts[2]
                if ident in pokemon_data:
                    pokemon_data[ident]["item"] = NONE_ITEM

            if "|request|" in log:
                parts = log.split("|", 2)
                request_data = json.loads(parts[2])
                side_data = request_data.get("side", {})
                player_id = int(side_data.get("id", "p1")[1]) - 1
                state["sides"][player_id]["name"] = side_data.get("name", "")
                for pokemon in side_data.get("pokemon", []):
                    ident = pokemon["ident"]
                    stats = pokemon.get("stats", {})
                    logging.warning(pokemon["condition"])
                    pokemon_entry = {
                        "ident": ident,
                        "species": pokemon["details"].split(", ")[0],
                        "level": int(pokemon["details"].split(", ")[1][1:]),
                        "gender": pokemon["details"].split(", ")[2] if len(pokemon["details"].split(", ")) > 2 else "",
                        "condition": pokemon["condition"],
                        "hp": 0 if pokemon["condition"] == "0 fnt" else int(pokemon["condition"].split("/")[0]),
                        "max_hp": 100 if pokemon["condition"] == "0 fnt" else int(pokemon["condition"].split("/")[1]), # TODO: This is wrong; max_hp should be whatever this struct had previously
                        "item": pokemon.get("item", NONE_ITEM),
                        "ability": pokemon.get("ability", PLACEHOLDER_ABILITY),
                        "moves": pokemon.get("moves", []),
                        "baseStoredStats": stats,
                        "storedStats": stats
                    }
                    pokemon_data[ident] = pokemon_entry

                    # Overwrite entries in the pokemon array
                    existing_pokemon = next(
                        (p for p in state["sides"][player_id]["pokemon"] if p["ident"] == ident), None)
                    if existing_pokemon:
                        state["sides"][player_id]["pokemon"].remove(
                            existing_pokemon)
                    state["sides"][player_id]["pokemon"].append(pokemon_entry)

            if "|-damage|" in log:
                logging.warning(f"TODO: Unimplemented function")
                # parts = log.logging.warning(f"TODO: Unimplemented function")
                # split("|")
                # ident = part# s[2]
                # condition = # parts[3]
                # if ident in # pokemon_data:
                #     pokemon_data#     [ident]["condition"] = condition
                #     pokemon_data[ide#     nt]["hp"] = int(condition.split("/")[0])

    return state
