from rich.console import Console
from rich.prompt import Prompt

from sutom import LetterStatus, SutomFSM


def print_current_state(sutom: SutomFSM, console: Console):
    for letter, letter_status in sutom.state_of_prediction:
        match letter_status:
            case LetterStatus.PERFECT_MATCH:
                console.print(letter, style="green", end="")
                console.print(" ", end="")  # last one is in excess but that's ok
            case _:
                console.print(" ", style="u", end="")
                console.print(" ", end="")
    console.print("\n\n")


def main():
    console = Console()
    ground_truth_word = "amour"

    sutom_game = SutomFSM(ground_truth_word)

    while True:
        guess = Prompt.ask(f"Enter your {len(ground_truth_word)}-letter guess").lower()

        if len(guess) != len(ground_truth_word):
            console.print(
                f"[bold red]Your guess must be {len(ground_truth_word)}"
                + " letters long. Please try again.[/bold red]"
            )
            continue

        guess_result = sutom_game.guess(guess)

        for letter_result in guess_result.results:
            match letter_result.status:
                case LetterStatus.PERFECT_MATCH:
                    status_color = "green"
                case LetterStatus.FOUND_BUT_WRONG_POSITION:
                    status_color = "yellow"
                case _:
                    status_color = "red"

            console.print(
                f"Letter '{letter_result.letter}' at position"
                + f" {letter_result.position}: [{status_color}]"
                + f"{letter_result.status.value}[/{status_color}]"
            )

        print_current_state(sutom_game, console)

        if guess == ground_truth_word:
            console.print(
                "[bold green]Congratulations! You guessed the word"
                + f" '{ground_truth_word}'![/bold green]"
            )
            break


if __name__ == "__main__":
    main()
