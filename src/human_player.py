from rich.console import Console
from rich.prompt import Prompt

from src.player import Player
from src.sutom_engine import GuessResult


class HumanPlayer(Player):
    def __init__(self, gt_length: int):
        self.gt_length = gt_length

        self.console = Console()

    def guess(self, past_guess_results: list[GuessResult]) -> str:
        while True:
            guess = Prompt.ask(f"Enter your {self.gt_length}-letter guess").lower()

            if len(guess) != self.gt_length:
                self.console.print(
                    f"[bold red]Your guess must be {self.gt_length}"
                    + " letters long. Please try again.[/bold red]",
                    style="bold red",
                )
                continue
            else:
                return guess
