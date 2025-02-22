import pytest
import pprint
from metagross.showdown_engine import ShowdownEngine
import logging

def test_happy_path():
    """Test that the simulator can be initialized and run a basic battle"""
    # Configure logging for the test
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create simulator instance
    simulator = ShowdownEngine()
    
    # Initialize battle
    simulator.initialize_battle()
    game_state = simulator.get_state('p1')
    
    # Verify we got a valid initial state
    assert 'p1' in game_state
    assert 'p2' in game_state
    assert 'state' in game_state
    
    # Not strictly necessary for this test, but it breaks often enough it's useful
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    pp = pprint.PrettyPrinter(indent=2)

    # TODO: Add some assertions for correctnes
    while not simulator.is_game_over():
        logging.debug("TESTING")
        print("TESTING")
        decisions = []
        for player_id in simulator.get_active_players():
            game_state = simulator.get_state(player_id)
            options = simulator.get_move_options(player_id)
            logging.debug(f"{player_id} options: " + ', '.join(options))
            decisions.append(options[0])  # This is just a test runner; don't worry about complex decision making
        simulator.make_moves(decisions)
        
    logging.info(f"Winner: {simulator.get_winner()}")