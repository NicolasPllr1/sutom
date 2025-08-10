from abc import ABC

from sutom import GuessResult


class player(ABC):
    def guess(self, past_guess_results: list[GuessResult]) -> str: ...
