from abc import ABC
import json
import logging
import re
from shutil import move
import typing

UNKNOWN_SPECIES = "unknown_species"
UNKNOWN_ITEM = "unknown_item"
UNKNOWN_ABILITY = "unknown_ability"
UNKNOWN_MOVE = "unknown_move"
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
                player_id, pokemon_entries = __parse_request_to_pokemon_array(log)
                # TODO: Instead of straight assignment, this needs to be structured so it doesn't overwrite boosts, move pp, etc
                for pokemon_entry in pokemon_entries:
                    pokemon_data[pokemon_entry.get_ident()] = pokemon_entry
                continue

            if "player" == log_type:
                state["sides"][player_id]["name"] = parts[3]

            # Boosts AREN'T captured by the request object, so we still need to record them
            if "-boost" == log_type:
                stat = parts[3]
                amount = int(parts[4])
                pokemon_data[ident].add_boost(stat, amount)

            if "-damage" == log_type or "-heal" == log_type:
                # EXAMPLE: |-damage|p1a: Skeledirge|206/294
                # EXAMPLE: |-damage|p2a: Mimikyu|66/100|[from] item: Life Orb
                # TODO: Damage gives us an opportunity to infer the stats of the away team pokemon; add some calcs!
                condition = parts[3]
                pokemon_data[ident].set_condition(condition)

            if "move" == log_type:
                # EXAMPLE: |move|p2a: Mimikyu|Shadow Sneak|p1a: Skeledirge
                move_name = parts[3]
                pokemon_data[ident].record_move_from_name(move_name)

            # The |request log supersedes most of the other logs, but we only have them for the home player
            if player_id != HOME_PLAYER:
                if "-item" == log_type:
                    item = parts[3]  # TODO: Is this item name or item id?
                    pokemon_data[ident].set_item(item)

                if "-ability" == log_type:
                    ability = parts[3]  # TODO: Is this ability name or ability id?
                    pokemon_data[ident].set_ability(ability)

                if "-enditem" == log_type:
                    pokemon_data[ident].set_item(NONE_ITEM)

                if "faint" == log_type:
                    # EXAMPLE: |faint|p2a: Mimikyu
                    pokemon_data[ident].mark_fainted()

                if "detailschange" == log_type:
                    details = parts[3]
                    pokemon_data[ident].set_details(details)

                if "switch" == log_type or "drag" == log_type:
                    # EXAMPLE: |switch|p2a: Crabominable|Crabominable, L90, M|100/100
                    # First, figure out if we need to initialize a new pokemon!
                    if ident not in pokemon_data:
                        pokemon_data[ident] = PokemonSimulatorState()
                        pokemon_data[ident].set_ident(ident)
                        pokemon_data[ident].set_details(parts[3])
                    # Otherwise, we have a condition string
                    condition = parts[4]
                    pokemon_data[ident].set_condition(condition)
                    # TODO: Increment activeTurns ?

    # Load all of the finalized pokemon into the state arrays
    for pokemon in pokemon_data.values():
        player_id = pokemon.get_player_id()
        state["sides"][player_id]["pokemon"].append(pokemon.get_state())

    return state


def __parse_request_to_pokemon_array(log: str) -> typing.Tuple[int, list]:
    parts = log.split("|", 2)
    request_data = json.loads(parts[2])
    side_data = request_data.get("side", {})
    player_id = int(side_data.get("id", "p1")[1]) - 1

    pokemon_entries = []
    for pokemon in side_data.get("pokemon", []):
        ident = pokemon["ident"]
        stats = pokemon.get("stats", {})

        pokemon_entry = PokemonSimulatorState()
        pokemon_entry.set_ident(ident)
        pokemon_entry.set_details(pokemon["details"])
        pokemon_entry.set_ability(pokemon.get("ability", UNKNOWN_ABILITY))
        pokemon_entry.set_item(pokemon.get("item", NONE_ITEM))
        pokemon_entry.set_condition(pokemon.get("condition"))
        pokemon_entry.set_stats(pokemon.get("stats"))
        pokemon_entry.set_tera_type(pokemon.get("teraType"))
        # TODO: Set if it's terastallized!
        for move_id in pokemon.get("moves", []):
            pokemon_entry.add_move_from_id(move_id)
        pokemon_entries.append(pokemon_entry)
    return player_id, pokemon_entries


class PokemonSimulatorState(ABC):
    def __init__(self):
        self.ident = ""
        self.state = {
            "m": {},
            "dynamaxLevel": 10,
            "gigantamax": False,
            "moveSlots": [],
            "position": 0,
            "status": "",
            "statusState": {},
            "volatiles": {},
            "hpPower": 60,
            "baseHpPower": 60,
            # TODO: Replace the stats with a special range, e.g: {"min": 100, "max": 200}
            "baseStoredStats": {
                "atk": 404,
                "def": 404,
                "spa": 404,
                "spd": 404,
                "spe": 404,
                "hp": 404,
            },
            "storedStats": {"atk": 404, "def": 404, "spa": 404, "spd": 404, "spe": 404},
            "boosts": {
                "atk": 0,
                "def": 0,
                "spa": 0,
                "spd": 0,
                "spe": 0,
                "accuracy": 0,
                "evasion": 0,
            },
            "lastItem": "",
            "usedItemThisTurn": False,
            "ateBerry": False,
            "trapped": False,
            "maybeTrapped": False,
            "maybeDisabled": False,
            "illusion": None,
            "transformed": False,
            "fainted": False,
            "faintQueued": False,
            "subFainted": None,
            "addedType": "",
            "knownType": True,
            "switchFlag": False,
            "forceSwitchFlag": False,
            "skipBeforeSwitchOutEventFlag": False,
            "draggedIn": None,
            "newlySwitched": True,
            "beingCalledBack": False,
            "lastMove": None,
            "lastMoveUsed": None,
            "moveThisTurn": "",
            "statsRaisedThisTurn": False,
            "statsLoweredThisTurn": False,
            "hurtThisTurn": None,
            "lastDamage": 0,
            "attackedBy": [],
            "timesAttacked": 0,
            "isActive": False,
            "activeTurns": 0,
            "activeMoveActions": 0,
            "previouslySwitchedIn": 0,
            "truantTurn": False,
            "isStarted": False,
            "duringMove": False,
            "speed": 404,
            "abilityOrder": 0,
            "canMegaEvo": None,
            "canUltraBurst": None,
            "canGigantamax": None,
            "maxhp": 404,
            "baseMaxhp": 404,
            "hp": 404,
            "set": {
                "shiny": False,
                "moves": [],
                "evs": {
                    "hp": 85,
                    "atk": 85,
                    "def": 85,
                    "spa": 85,
                    "spd": 85,
                    "spe": 85,
                },
                "ivs": {
                    "hp": 31,
                    "atk": 31,
                    "def": 31,
                    "spa": 31,
                    "spd": 31,
                    "spe": 31,
                },
                "role": "Stone Cold Killer",
            },
        }
        self.set_ability(UNKNOWN_ABILITY)
        self.set_item(UNKNOWN_ITEM)

    def __init(self, full_block):
        raise NotImplementedError

    def get_state(self):
        return self.state

    def get_ident(self):
        return self.ident

    def get_player_id(self):
        return int(self.get_ident()[1]) - 1

    def set_ident(self, ident: str):
        self.ident = ident

    def set_position(self, position: int):
        self.state["position"] = position

    def set_details(self, details: str):
        parts = details.split(", ")
        species = parts[0]
        level = int(parts[1][1:])
        gender = parts[2] if len(parts) >= 3 else ""  # TODO: Right genderless value?
        self.state["baseSpecies"] = f"[Species:{species.lower()}]"
        self.state["species"] = f"[Species:{species.lower()}]"
        self.state["speciesState"] = {"id": species}
        self.state["gender"] = gender
        self.state["details"] = details
        self.state["set"]["name"] = species
        self.state["set"]["species"] = species
        self.state["set"]["gender"] = gender
        self.state["set"]["level"] = level

        # Some attributes are keyed solely off of species; do a lookup!
        # TODO: Actually do the lookup...
        self.state["types"] = ["Fire", "Psychic"]
        self.state["baseTypes"] = ["Fire", "Psychic"]
        self.state["apparentType"] = "Fire/Psychic"
        self.state["weighthg"] = 500

    def set_ability(self, ability_id: str):
        # TODO: Look up the ability name based on its id
        ability_name = "Infiltrator"
        self.state["baseAbility"] = ability_id
        self.state["ability"] = ability_id
        self.state["abilityState"] = {"id": ability_id}
        self.state["set"]["ability"] = ability_name

    def set_item(self, item_id: str):
        # TODO: Look up the item name based on its id
        item_name = "Life Orb"
        self.state["item"] = item_id
        self.state["itemState"] = {"id": item_id}
        self.state["set"]["item"] = item_name

    def set_hidden_power_type(self, hp_type: str):
        """NOTE: In more recent gens, hidden power hasn't been a thing!"""
        self.state["hpType"] = hp_type
        self.state["baseHpType"] = {"id": hp_type}

    def set_tera_type(self, tera_type: str):
        self.state["teraType"] = tera_type
        self.state["canTerastallize"] = tera_type
        self.state["set"]["teraType"] = tera_type

    def set_condition(self, condition_string: str):
        """Set attributes based off of a condition string that we see in the showdown log"""
        hp = self.__get_hp_from_condition(condition_string)
        max_hp = self.__get_max_hp_from_condition(condition_string)
        self.state["hp"] = hp
        self.state["maxhp"] = max_hp
        self.state["baseMaxhp"] = max_hp
        # TODO: We need to estimate the HP when we don't actually know it. This should record the hp based stats as ranges
        # TODO: What about the baseStoredStats of hp?

    def set_stats(self, stats_dict):
        self.state["baseStoredStats"] = stats_dict
        self.state["storedStats"] = stats_dict

    def add_boost(self, stat, amount):
        self.state["boosts"][stat] += amount

    def mark_fainted(self):
        self.state["hp"] = 0

    def record_move_from_name(self, move_name):
        """Note that a move has been used. Will:
        1. Add the move to the list of moves if it isn't already present
        2. Decrement PP from the move
        """
        move_id = MOVE_NAME_TO_ID[move_name]
        move_slots = self.state.get("moveSlots", [])
        move_dict = next((move for move in move_slots if move["id"] == move_id), None)
        if move_dict is None:
            move_dict = self.add_move_from_id(move_id)
        move_dict["pp"] = move_dict["pp"] - 1

    def add_move_from_id(self, move_id: str) -> typing.Dict:
        move_slots = self.state.get("moveSlots", [])
        move_data = MOVE_ID_TO_MOVE[move_id]
        move_dict = {
            "move": move_id,
            "id": move_data["name"],
            "pp": move_data["pp"],
            "maxpp": move_data["pp"],
            "target": move_data["target"],
            "disabled": False,
            "disabledSource": "",
            "used": False,
        }
        move_slots.append(move_dict)
        self.state["moveSlots"] = move_slots
        return move_dict

    def __get_hp_from_condition(self, condition: str) -> int:
        return 0 if condition == "0 fnt" else int(condition.split("/")[0])

    def __get_max_hp_from_condition(self, condition: str) -> int:
        # NOTE: I don't think it'll matter, but 100 isn't actually correct for p1's pokemon
        return 100 if condition == "0 fnt" else int(condition.split("/")[0])


def __get_ident(ident_string) -> str:
    # The idents either come in the form of 'p1a: Skarmory' or 'p1: Skarmory'. The 'a' denotes battlefield position
    if ident_string != None and len(ident_string) > 2:
        if ident_string[2] == ":":
            return ident_string
        else:
            return ident_string[:2] + ident_string[3:]
    return ""


def __get_player_id_from_ident_or_default(ident: str, default: int) -> int:
    if ident != None and len(ident) >= 2:
        return int(ident[1]) - 1 if ident[1].isdecimal() else default
    return default


def __get_hp_from_condition(condition: str) -> int:
    return 0 if condition == "0 fnt" else int(condition.split("/")[0])


def __get_max_hp_from_condition(condition: str) -> int:
    # NOTE: I don't think it'll matter, but 100 isn't actually correct for p1's pokemon
    return 100 if condition == "0 fnt" else int(condition.split("/")[0])
