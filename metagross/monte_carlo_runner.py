import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from metagross.agent import Agent
from metagross.simulation_engine import SimulationEngine


@dataclass
class SimulationResult:
    initial_move: str
    wins: int
    total_games: int

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_games if self.total_games > 0 else 0


def run_single_simulation(
    engine: SimulationEngine,
    first_move: str,
    player_id: str,
    agents: Dict[str, Agent]
) -> bool:
    """Run a single simulation starting with the given move"""
    sim = engine.clone()

    iteration_count = 0
    while not sim.is_game_over():
        active_players = sim.get_active_players()
        decisions = []
        for current_player in active_players:
            if iteration_count == 0 and current_player == player_id:
               decisions.append(first_move)
            else:
                move_options = sim.get_move_options(current_player)
                state = sim.get_state(current_player)
                agent = agents[current_player]
                selected_move = agent.select_move(state, move_options)
                decisions.append(selected_move)
        sim.make_moves(decisions)
        iteration_count += 1
    return sim.get_winner() == player_id


def simulate_move(args) -> SimulationResult:
    """Run simulations for a single move.

    Args:
        args: Tuple of (engine, move, player_id, agents, num_simulations)
    """
    engine, move, player_id, agents, num_simulations = args
    wins = 0
    for _ in range(num_simulations):
        if run_single_simulation(engine, move, player_id, agents):
            wins += 1
    return SimulationResult(move, wins, num_simulations)


def run_monte_carlo(
    engine: SimulationEngine,
    player_id: str,
    agents: dict[str, Agent],
    num_simulations: int = 1000,
    num_processes: int = -1,
    iterations: int = 3,
    initial_simulations: int = 100
) -> List[SimulationResult]:
    """
    Run Monte Carlo simulation to find the best initial move

    Args:
        engine: The simulation engine to use
        player_id: ID of the player making the move
        agents: Dictionary mapping player IDs to their respective agents
        num_simulations: Total number of simulations to run
        num_processes: Number of processes to use for parallel execution
        iterations: Number of iterations to refine the simulation results
        initial_simulations: Number of simulations to run in the first iteration

    Returns:
        List of SimulationResult objects for each initial move
    """
    if num_processes == -1:
        num_processes = mp.cpu_count()

    move_options = engine.get_move_options(player_id)
    remaining_simulations = num_simulations
    results = []

    for iteration in range(iterations):
        if iteration == 0:
            sims_per_move = initial_simulations
        else:
            sims_per_move = remaining_simulations // len(move_options)

        simulation_args = [(engine, move, player_id, agents, sims_per_move)
                           for move in move_options]

        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            iteration_results = list(executor.map(
                simulate_move, simulation_args))

        if iteration == 0:
            results = iteration_results
        else:
            for i, result in enumerate(iteration_results):
                results[i].wins += result.wins
                results[i].total_games += result.total_games

        # Sort the move options by their win rates, take the top half, invest more simulations into them
        results = sorted(results, key=lambda x: x.win_rate, reverse=True)
        move_options = [
            result.initial_move for result in results[:max(1, len(move_options)//2)]]
        remaining_simulations -= sims_per_move * len(move_options)

    return results
