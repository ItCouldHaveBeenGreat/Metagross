import json
import logging
import subprocess
from time import sleep
from typing import Any, Dict, List, Optional, Set

from metagross.simulation_engine import SimulationEngine


# TODO: This interface is very annoyying to debug because it hides the simulator output
#       and has very strong expectations of what it should look like. When those expectations
#       arent met, it hangs and the caller has to timeout. The refactor should...
#       1. If there's an error, we want to know about it
#       2. If we get output we aren't expecting, we want to know about it
#       3. We should be able to still use convience functions to access schema'ed data
#
#       It seems like we either want to debug everything we get from the simulator... actually
#       that's so fast lets just do that now
class ShowdownEngine(SimulationEngine):
    SHOWDOWN_EXECUTABLE_PATH = "lib/pokemon-showdown-0.11.9/pokemon-showdown"
    SIMULATE_BATTLE_COMMAND = [SHOWDOWN_EXECUTABLE_PATH, "simulate-battle"]
    game_state = {}

    def __init__(self):
        # Create the subprocess when the object is instantiated
        self.process = subprocess.Popen(
            ShowdownEngine.SIMULATE_BATTLE_COMMAND,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logging.info("Initiated subprocess...")
        logging.info(f"Command: {' '.join(map(str, self.process.args))}")
        logging.info(f"Process ID (PID): {self.process.pid}")

    def initialize_from_state(self, state_filename):
        simulate_start = [
            f">loadstate {state_filename}",
        ]
        for command in simulate_start:
            self.__perform_action(command + "\n")
        # We need to force hydration of state so

    def clone(self) -> "SimulationEngine":
        """Return a deep copy of the simulation engine"""
        # Note: Currently not implemented as it requires special handling of subprocess
        raise NotImplementedError(
            "Clone operation not yet supported for ShowdownEngine"
        )

    # TODO: This should be parameterized to do multiple types of battles
    def initialize_battle(self):
        """
        Run commands to set up a random battle and collect the initial state of the game.
        """
        # For now, just hardcode the actions to set up a random battle
        # TODO: Add cleanup function or just include it here?
        # 		'gen9customgame', 'gen9doublescustomgame',
        simulate_start = [
            '>start {"formatid":"gen9customgame"}',
            '>player p1 {"name":"p1"}',
        ]
        for command in simulate_start:
            self.__perform_action(command + "\n")

        # We don't currently care any output before the first newline!
        logging.debug("Discarding extraneous output...")
        if self.process.stdout:
            while self.process.stdout.readline().strip():
                continue
        # Add in the second player, which triggers our first state dump
        self.__perform_action('>player p2 {"name":"p2"}\n')
        self.game_state = self.__collect_game_state()

    def get_state(self, player_id: str) -> Dict[str, Any]:
        """Return current state of the simulation visible to the given player"""
        if player_id not in ["p1", "p2"]:
            raise ValueError("Invalid player_id. Must be 'p1' or 'p2'")

        # TODO: Right now there's only one, non-player specific game state!
        return self.game_state

    def get_move_options(self, player_id: str) -> List[str]:
        """Return valid moves for the given player"""
        if player_id not in ["p1", "p2"]:
            raise ValueError("Invalid player_id. Must be 'p1' or 'p2'")

        options = []
        game_state = self.get_state(player_id)[player_id]
        if "active" in game_state:
            for move in game_state["active"][0]["moves"]:
                if "disabled" in move and move["disabled"]:
                    continue
                if "pp" in move and move["pp"] == 0:
                    continue
                # TODO: Also eliminate moves with no valid targets
                options.append(f">{player_id} move {move['id']}")
        for index, pokemon in enumerate(game_state["side"]["pokemon"]):
            if pokemon["active"]:
                continue
            if pokemon["condition"] == "0 fnt":
                continue
            # Switches are 1-indexed
            options.append(f">{player_id} switch {index + 1}")
        return options

    def make_moves(self, moves: List[str]) -> None:
        """Execute a move and update the simulation state"""
        for move in moves:
            self.__perform_action(move)
        self.game_state = self.__collect_game_state()

    def get_active_players(self) -> Set[str]:
        """Return set of players that need to provide input"""
        active_players = set()
        for player_id in ["p1", "p2"]:
            if player_id in self.game_state and not (
                "wait" in self.game_state[player_id]
                and self.game_state[player_id]["wait"]
            ):
                active_players.add(player_id)
        return active_players

    def is_game_over(self) -> bool:
        """Return whether the simulation has reached an end state"""
        return "log" in self.game_state

    def get_winner(self) -> Optional[str]:
        """Return the winner if game is over, None otherwise"""
        if self.is_game_over():
            return self.game_state["log"]["winner"]
        return None

    def __collect_game_state(self):
        """
        Collects a dict representing the current state of the game from the simulator's stdout. The dict contains the following keys:
        """
        new_lines = 0
        output_blocks = [[], [], []]
        while new_lines < 3:
            line = self.process.stdout.readline()
            if line == "\n":
                new_lines += 1
            elif line.strip() == "end":
                # The game has ended; handle the different format
                logging.debug("Handling end of game...")
                log = json.loads(self.process.stdout.readline())
                return {"state": output_blocks[0], "log": log}
            elif line.strip():
                logging.debug("[sim output]: {}".format(line))
                output_blocks[new_lines].append(line.strip())
        # Otherwise, assume we have a standard p1/p2/state block
        dict_output = {}
        dict_output["p1"] = json.loads(output_blocks[0][2].split("|request|")[1])
        dict_output["p2"] = json.loads(output_blocks[1][2].split("|request|")[1])

        # TODO: Further parse this block into a log and state
        dict_output["state"] = output_blocks[2]
        return dict_output

    def __perform_action(self, command):
        # Send the command to the subprocess's stdin
        logging.debug("Running command: " + command.strip())
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
