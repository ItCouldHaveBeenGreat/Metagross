import json
import logging
import pytest

from metagross.state_from_log import parse_log

PLACEHOLDER_ITEM = "unknown_item"
PLACEHOLDER_ABILITY = "unknown_ability"
PLACEHOLDER_MOVE = "unknown_move"

def test_parse_log():
    with open('tests/test_data/sample_input2.json', 'r') as f:
        log_data = json.load(f)

    logs = log_data['logs']
    state = parse_log(logs)

    # Define the expected state here
    expected_state = {}
    
    logging.warning(f"STATE: {json.dumps(state, indent=4)}")
    assert state == expected_state