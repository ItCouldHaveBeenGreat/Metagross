import logging
import pytest
from typing import Any, Dict, List, Optional, Set
from metagross.simulation_engine import SimulationEngine
from metagross.monte_carlo_runner import run_monte_carlo
from metagross.agent import Agent, DeterministicAgent, RandomMoveAgent


class RockPaperScissorsEngine(SimulationEngine):
    MOVES = ['rock', 'paper', 'scissors']
    WINS_REQUIRED = 2

    player_win_counts = {'p1': 0, 'p2': 0}

    def __init__(self):
        self.moves_made = []

    def get_state(self, player_id: str) -> Dict[str, Any]:
        return {
            'moves_made': self.moves_made.copy(),
        }

    def get_move_options(self, player_id: str) -> List[str]:
        # Prefix each move with the player id and return it
        return [f">{player_id} {move}" for move in self.MOVES]

    def make_moves(self, moves: List[str]) -> None:
        self.moves_made.extend(moves)
        move1 = next(move for move in moves if move.startswith(
            '>p1 ')).split(' ')[1]
        move2 = next(move for move in moves if move.startswith(
            '>p2 ')).split(' ')[1]
        if move1 == None or move2 == None:
            raise ValueError("Move from both players are required")

        winning_moves = {
            'rock': 'scissors',
            'paper': 'rock',
            'scissors': 'paper'
        }
        if move1 == move2:
            return  # Draw
        if winning_moves[move1] == move2:
            self.player_win_counts['p1'] += 1
        else:
            self.player_win_counts['p2'] += 1

    def get_active_players(self) -> Set[str]:
        return {'p1', 'p2'}

    def is_game_over(self) -> bool:
        return self.get_winner() is not None

    def get_winner(self) -> Optional[str]:
        if self.player_win_counts['p1'] >= self.WINS_REQUIRED:
            return 'p1'
        elif self.player_win_counts['p2'] >= self.WINS_REQUIRED:
            return 'p2'
        else:
            return None

    def clone(self) -> 'SimulationEngine':
        new_engine = RockPaperScissorsEngine()
        new_engine.moves_made = self.moves_made.copy()
        new_engine.player_win_counts = self.player_win_counts.copy()
        return new_engine


def test_monte_carlo_rock_paper_scissors():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    # Create a simulation engine
    engine = RockPaperScissorsEngine()

    # Create agents that will play in a predictable way for testing
    agents = {
        'p1': RandomMoveAgent(),  # p1 makes random moves
        'p2': DeterministicAgent(1)  # p2 always plays paper
    }

    # Run monte carlo simulation
    results = run_monte_carlo(
        engine=engine,
        player_id='p1',
        agents=agents,
        num_simulations=100,
        num_processes=1
    )
    logging.warning(f"Simulation results: {results}")
    
    assert len(results) == 3

    rock_result = next(r for r in results if r.initial_move == '>p1 rock')
    paper_result = next(r for r in results if r.initial_move == '>p1 paper')
    scissors_result = next(r for r in results if r.initial_move == '>p1 scissors')

    # Rock should be the worst opening move
    # Paper should be the intermediate option
    # Scissors should be the best option
    assert rock_result.wins < paper_result.wins
    assert paper_result.wins < scissors_result.wins
