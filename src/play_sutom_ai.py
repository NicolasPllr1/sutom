from pathlib import Path

from rich.console import Console

from src.info_theoretic_player_2 import InfoTheory
from src.play_utils import (
    bad_guess_length,
    check_success,
    check_vocab,
    load_input_vocab,
    print_current_state,
    print_guess,
    print_guess_outcome,
)
from src.sutom import SutomFSM

VOCAB_PATH = Path("data") / "fr-nouns_filtered_normalized.txt"
MAX_ITER = 10
SAVE_DIR = Path("save_tmp")


def play(
    ground_truth_word: str,
    *,
    vocab_path: Path = VOCAB_PATH,
    max_iter: int = MAX_ITER,
    save_dir: Path = SAVE_DIR,
):
    console = Console()
    sutom_game = SutomFSM(ground_truth_word)

    vocab = load_input_vocab(vocab_path)
    check_vocab(ground_truth_word, vocab)

    gt_length = len(ground_truth_word)

    # NOTE: the player does *not* know 'ground_truth_word' value !
    player = InfoTheory(gt_length=gt_length, vocab=vocab, save_dir=save_dir)

    for iter in range(1, max_iter + 1):
        print_current_state(iter, sutom_game, console)

        guess = player.guess(sutom_game.past_results)
        print_guess(guess, sutom_game.past_results, console)

        if bad_guess_length(guess, ground_truth_word, console):
            break

        guess_result = sutom_game.guess(guess)

        print_guess_outcome(iter, guess_result, sutom_game, console)

        if check_success(ground_truth_word, guess, console):
            break
