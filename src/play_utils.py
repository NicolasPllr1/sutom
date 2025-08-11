from pathlib import Path

from rich.console import Console

from src.sutom_engine import GuessResult, LetterResult, LetterStatus, SutomFSM


def load_input_vocab(vocab_path: Path) -> list[str]:
    "load vocab and return it as a list of words (str)"

    print("Loading vocab...")
    with open(vocab_path, "r") as f:
        vocab = list(set([line.strip() for line in f if line.strip()]))
    print("Vocab size:", len(vocab))
    return vocab


def check_vocab(ground_truth_word: str, vocab: list[str]):
    assert ground_truth_word in vocab, (
        "Bad setup: ground-truth word not in the starter vocab"
    )
    return


def bad_guess_length(guess: str, ground_truth_word: str, console: Console) -> bool:
    "Returns True if the guess has an invalid length"
    if len(guess) != len(ground_truth_word):
        console.print(
            "[red]" + f"Guess must be {len(ground_truth_word)} letters long." + "[/red]"
        )
        return True
    else:
        return False


def print_current_state(iter: int, sutom: SutomFSM, console: Console):
    console.print("\n\n")
    print(f"----- ROUND #{iter} -----")

    for letter, letter_status in sutom.state_of_prediction:
        match letter_status:
            case LetterStatus.PERFECT_MATCH:
                console.print(letter, style="green", end="")
                console.print(" ", end="")  # last one is in excess but that's ok
            case _:
                console.print(" ", style="u", end="")
                console.print(" ", end="")
    console.print("\n\n")
    return


def print_guess(guess: str, past_guess_results: list[GuessResult], console: Console):
    console.print(f"\n[blue]Guess: {guess}[/blue]")
    console.print(f"Past guesses: {[res.guess for res in past_guess_results]}\n")
    return


def print_single_letter_result(letter_result: LetterResult, console: Console):
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
    return


def print_guess_outcome(
    iter: int, guess_result: GuessResult, sutom_game: SutomFSM, console: Console
):
    for letter_result in guess_result.results:
        print_single_letter_result(letter_result, console)

    print_current_state(iter, sutom_game, console)
    return


def check_success(gt: str, guess: str, console: Console) -> bool:
    if guess == gt:
        console.print(
            "[bold green]Congratulations! You guessed the word"
            + f" '{gt}'![/bold green]"
        )
        return True
    else:
        return False
