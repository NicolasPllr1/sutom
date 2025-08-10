from pathlib import Path

from rich import print
from rich.console import Console

from info_theoretical_player import InfoTheory
from sutom import GuessResult, LetterStatus, SutomFSM


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

    with open("data/fr-nouns_filtered.txt", "r") as f:
        vocab = [line.strip() for line in f if line.strip()]

    assert ground_truth_word in vocab, (
        "Bad setup: ground-truth word not in the starter vocab"
    )
    print("Vocab size:", len(vocab))

    player = InfoTheory(
        gt_length=len(ground_truth_word), vocab=vocab, save_dir=Path("save_tmp")
    )
    past_guess_results: list[GuessResult] = []

    MAX_ITER = 10
    iter = 1
    while iter <= MAX_ITER:
        print(f"\n----- ITERATION #{iter} -----\n")

        print_current_state(sutom_game, console)

        # guess = Prompt.ask(f"Enter your {len(ground_truth_word)}-letter guess").lower()
        guess = player.guess(past_guess_results)
        print(f"[blue]GUESS: {guess}[/blue]")
        print(f"With past guesses:\n{[res.guess for res in past_guess_results]}\n")

        if len(guess) != len(ground_truth_word):
            console.print(
                f"[bold red]Your guess must be {len(ground_truth_word)}"
                + " letters long. Please try again.[/bold red]"
            )
            continue

        guess_result = sutom_game.guess(guess)
        past_guess_results.append(guess_result)

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
        iter += 1


if __name__ == "__main__":
    main()
