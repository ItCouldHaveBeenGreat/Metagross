import json
import logging
import pprint
import select
import subprocess
from time import sleep
import time


class SimulatorWrapper:
    SHOWDOWN_EXECUTABLE_PATH = "pokemon-showdown-0.11.9/pokemon-showdown"
    SIMULATE_BATTLE_COMMAND = [SHOWDOWN_EXECUTABLE_PATH, "simulate-battle"]

    def __init__(self):
        # Create the subprocess when the object is instantiated
        self.process = subprocess.Popen(
            SimulatorWrapper.SIMULATE_BATTLE_COMMAND,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)
        logging.info("Initiated subprocess...")
        logging.info(f"Command: {' '.join(self.process.args)}")
        logging.info(f"Process ID (PID): {self.process.pid}")

    def initialize_battle(self):
        """
        Run commands to set up a random battle and collect the initial state of the game.
        """
        # For now, just hardcode the actions to set up a random battle
        # TODO: Add cleanup function or just include it here?
        simulate_start = ['>start {"formatid":"gen7randombattle"}',
                          '>player p1 {"name":"p1"}',
                          ]
        for command in simulate_start:
            self.__perform_action(command + '\n')

        # We don't currently care any output before the first newline!
        logging.debug("Discarding extraneous output...")
        while self.process.stdout.readline().strip():
            continue

        # Add in the second player, which triggers our first state dump
        self.__perform_action('>player p2 {"name":"p2"}\n')
        return self.__collect_game_state()

    def make_move(self, commands):
        """
        Executes a sequence of moves in the game. All commands required to advance to the next game state should be provided. e.g:
        - In the case of a normal round (where each player must make a decision for each of their pokemon simultaneously), 2 or 4 commands must be provided
        - In the case of a fainted pokemon, only one player is required to make a decision, namely the replacement of that pokemon

        Parameters:
        commands (List[str]): A list of commands to be executed. Each command is expected to be a string starting with > and followed by the player and action

        Returns:
        Dict[str, any]: The current state of the game after executing all the provided commands.
        """
        for command in commands:
            self.__perform_action(command)
        return self.__collect_game_state()

    def __collect_game_state(self):
        """
        Collects a dict representing the current state of the game from the simulator's stdout. The dict contains the following keys:
        """
        new_lines = 0
        output_blocks = [[], [], []]
        while new_lines < 3:
            line = self.process.stdout.readline()
            if line == '\n':
                new_lines += 1
            elif line.startswith('|win|'):
                return {"winner": line.strip().split('|win|')[1]}
            else:
                output_blocks[new_lines].append(line.strip())
        dict_output = {}
        dict_output['p1'] = json.loads(
            output_blocks[0][2].split('|request|')[1])
        dict_output['p2'] = json.loads(
            output_blocks[1][2].split('|request|')[1])

        # TODO: Further parse this block into a log and state
        dict_output['state'] = output_blocks[2]
        return dict_output

    def __perform_action(self, command):
        # Send the command to the subprocess's stdin
        logging.debug("Running command: " + command.strip())
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()

def get_options(player_identifier, side_data):
    options = []
    if 'active' in side_data:
        for move in side_data['active'][0]['moves']:
            if 'disabled' in move and move['disabled']:
                continue
            if 'pp' in move and move['pp'] == 0:
                continue
            # TODO: Also eliminate moves with no valid targets
            options.append(f">{player_identifier} move {move['id']}")
    for index, pokemon in enumerate(side_data['side']['pokemon']):
        if pokemon['active']:
            continue
        if pokemon['condition'] == '0 fnt':
            continue
        # Switches are 1-indexed
        options.append(f">{player_identifier} switch {index + 1}")
    return options


def main():
    # Configure logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    pp = pprint.PrettyPrinter(indent=2)
    simulator = SimulatorWrapper()

    game_state = simulator.initialize_battle()
    pp.pprint(game_state)

    while True:
        # All non-waiting players must make a decision
        decisions = []
        for player_id in ['p1', 'p2']:
            if 'wait' in game_state[player_id] and game_state[player_id]['wait']:
                continue
            options = get_options(player_id, game_state[player_id])
            logging.debug(f"{player_id} options: " + ', '.join(options))
            decisions.append(options[0]) # For now, just pick the first option
        game_state = simulator.make_move(decisions)
        pp.pprint(game_state['state'] if 'state' in game_state else game_state)
        if 'winner' in game_state:
            logging.info(f"Winner: {game_state['winner']}")
            break

    # TODO: How do we handle winning/losing/other terminal states?
    # TODO: What about doubles battles...


if __name__ == "__main__":
    main()
