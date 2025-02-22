from abc import ABC, abstractmethod
import logging
from random import randint
from typing import Any, Dict, List


class Agent(ABC):
    @abstractmethod
    def select_move(self, state: Dict[str, Any], moves: List[str]) -> str:
        """Select a move from the list of valid moves given the current state"""
        pass


class RandomMoveAgent(Agent):
    """Agent that always selects the first available move"""

    def select_move(self, state: Dict[str, Any], moves: List[str]) -> str:
        return moves[randint(0, len(moves) - 1)]


class DeterministicAgent(Agent):
    def __init__(self, move_number: int):
        self.move_number = move_number

    def select_move(self, state: Dict[str, Any], moves: List[str]) -> str:
        return moves[self.move_number]
