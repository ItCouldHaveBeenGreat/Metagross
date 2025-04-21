import unittest
import pprint
import signal
import functools
import sys
from metagross.showdown_engine import ShowdownEngine
import logging
from tests.test_utils import configure_logging, timeout


def timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Test timed out after {seconds} seconds")

            # Set the signal handler and a 10-second alarm
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)

            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            return result

        return wrapper

    return decorator


class TestShowdownEngine(unittest.TestCase):
    def setUp(self):
        """Configure logging for the test"""
        configure_logging()

    @timeout(10)  # 10 second timeout
    def test_happy_path(self):
        """Test that the simulator can be initialized and run a basic battle"""
        # Create simulator instance
        simulator = ShowdownEngine()

        # Initialize battle
        simulator.initialize_battle()
        game_state = simulator.get_state("p1")

        # Verify we got a valid initial state
        self.assertIn("p1", game_state)
        self.assertIn("p2", game_state)
        self.assertIn("state", game_state)

        # Not strictly necessary for this test, but it breaks often enough it's useful
        pp = pprint.PrettyPrinter(indent=2)

        # TODO: Add some assertions for correctnes
        while not simulator.is_game_over():
            logging.debug("TESTING")
            print("TESTING")
            decisions = []
            for player_id in simulator.get_active_players():
                game_state = simulator.get_state(player_id)
                options = simulator.get_move_options(player_id)
                logging.debug(f"{player_id} options: " + ", ".join(options))
                decisions.append(
                    options[0]
                )  # This is just a test runner; don't worry about complex decision making
            simulator.make_moves(decisions)

        logging.info(f"Winner: {simulator.get_winner()}")


if __name__ == "__main__":
    unittest.main()
