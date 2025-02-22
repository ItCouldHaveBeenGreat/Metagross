from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set


class SimulationEngine(ABC):
    @abstractmethod
    def get_state(self, player_id: str) -> Dict[str, Any]:
        """Return current state of the simulation visible to the given player"""
        pass

    @abstractmethod
    def get_move_options(self, player_id: str) -> List[str]:
        """Return valid moves for the given player"""
        pass

    @abstractmethod
    def make_moves(self, moves: List[str]) -> None:
        """Execute a move and update the simulation state"""
        pass

    @abstractmethod
    def get_active_players(self) -> Set[str]:
        """Return set of players that need to provide input"""
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        """Return whether the simulation has reached an end state"""
        pass

    @abstractmethod
    def get_winner(self) -> Optional[str]:
        """Return the winner if game is over, None otherwise"""
        pass

    @abstractmethod
    def clone(self) -> 'SimulationEngine':
        """Return a deep copy of the simulation engine"""
        pass