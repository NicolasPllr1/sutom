from abc import ABC
from enum import Enum

from src.sutom_engine import GuessResult


class Player(ABC):
    def guess(self, past_guess_results: list[GuessResult]) -> str: ...


class PlayerKind(Enum):
    HUMAN = "human"
    AI = "ai"
