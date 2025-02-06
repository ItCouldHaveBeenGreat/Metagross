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
        # For now, just hardcode the actions to set up a random battle
        # TODO: Add cleanup function or just include it here?
        simulate_start = ['>start {"formatid":"gen7randombattle"}',
                          '>player p1 {"name":"Alice"}',
                          ]
        for command in simulate_start:
            self.__perform_action(command + '\n')

        # We don't currently care any output before the first newline!
        logging.debug("Discarding extraneous output...")
        while self.process.stdout.readline().strip():
            continue

        # Add in the second player, which triggers our first state dump
        self.__perform_action('>player p2 {"name":"Bob"}\n')
        return self.__collect_game_state()

    def make_move(self, p1_command, p2_command):
        self.__perform_action(p1_command)
        self.__perform_action(p2_command)
        return self.__collect_game_state()

    def __collect_game_state(self):
        new_lines = 0
        output_blocks = [[], [], []]
        while new_lines < 3:
            line = self.process.stdout.readline()
            if line == '\n':
                new_lines += 1
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
        logging.debug("Running command: " + command)
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()



def main():
    # Configure logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    pp = pprint.PrettyPrinter(indent=2)
    simulator = SimulatorWrapper()

    game_state = simulator.initialize_battle()
    pp.pprint(game_state)

    game_state = simulator.make_move(">p1 move 1", ">p2 move 1")
    pp.pprint(game_state)
    
    # TODO: How do we handle winning/losing/other terminal states?
    # TODO: What about doubles battles...

if __name__ == "__main__":
    main()
