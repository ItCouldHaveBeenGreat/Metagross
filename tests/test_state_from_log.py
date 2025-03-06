import json
import logging
import pytest

from metagross.showdown_engine import ShowdownEngine
from metagross.state_from_log import MOVE_ID_TO_MOVE, parse_log

PLACEHOLDER_ITEM = "unknown_item"
PLACEHOLDER_ABILITY = "unknown_ability"
PLACEHOLDER_MOVE = "unknown_move"


def test_parse_log():
    with open("tests/test_data/sample_input2.json", "r") as f:
        log_data = json.load(f)

    logs = log_data["logs"]
    state = parse_log(logs)

    logging.warning(MOVE_ID_TO_MOVE)

    # Define the expected state here
    expected_state = {}

    logging.warning(f"STATE: {json.dumps(state, indent=4)}")
    state_filename = "tests/test_data/test_parse_log_output.json"
    json.dump(state, open(state_filename, "w"), indent=4)
    # assert state == expected_state

    # the ultimate test... is instantiating a showdown simulator instance
    simulator = ShowdownEngine()
    simulator.initialize_from_state(state_filename)
