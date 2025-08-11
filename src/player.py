from abc import ABC

from src.sutom import GuessResult


class Player(ABC):
    def guess(self, past_guess_results: list[GuessResult]) -> str: ...
