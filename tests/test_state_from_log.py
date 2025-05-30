import json
import logging
import unittest
import signal
import functools
import sys

from metagross.showdown_engine import ShowdownEngine
from metagross.state_from_log import (
    MOVE_ID_TO_MOVE,
    parse_log,
    parse_log_with_speculation,
)
from tests.test_utils import configure_logging, timeout

PLACEHOLDER_ITEM = "unknown_item"
PLACEHOLDER_ABILITY = "unknown_ability"
PLACEHOLDER_MOVE = "unknown_move"


class TestStateFromLog(unittest.TestCase):
    def setUp(self):
        configure_logging()

    @timeout(10)  # 10 second timeout
    def test_parse_log(self):
        with open("tests/test_data/sample_input2.json", "r") as f:
            log_data = json.load(f)

        logs = log_data["logs"]
        # TODO: See parse_log_with_speculation's comment;
        # state = parse_log(logs)
        logging.debug(f"Parsing logs with speculation: {logs}")
        state = parse_log_with_speculation(logs)

        logging.debug(f"Parsed state: {json.dumps(state, indent=4)}")
        state_filename = "tests/test_data/test_parse_log_output.json"
        with open(state_filename, "w") as f:
            json.dump(state, f, indent=4)

        # TODO: actually enable this!
        # Define the expected state here
        # expected_state = {}
        # self.assertEqual(state, expected_state)

        # The ultimate test... is instantiating a showdown simulator instance and running a round!
        logging.debug("Initializing simulator...")
        simulator = ShowdownEngine()
        simulator.initialize_from_state(state_filename)

        logging.debug("Playing game to completion...")
        while not simulator.is_game_over():
            decisions = []
            logging.debug(
                "Collecting player decisions for {}...".format(
                    simulator.get_active_players()
                )
            )
            for player_id in simulator.get_active_players():
                logging.debug("Collecting game state...")
                game_state = simulator.get_state(player_id)
                logging.debug(
                    f"Game state for {player_id}: {json.dumps(game_state, indent=4)}"
                )

                logging.debug("Collecting move options...")
                options = simulator.get_move_options(player_id)
                logging.debug(f"{player_id} options: " + ", ".join(options))
                decisions.append(
                    options[0]
                )  # This is just a test runner; don't worry about complex decision making
            simulator.make_moves(decisions)

        logging.debug(f"Winner: {simulator.get_winner()}")


if __name__ == "__main__":
    unittest.main()
