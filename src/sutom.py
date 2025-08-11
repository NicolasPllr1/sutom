from collections import Counter
from dataclasses import dataclass
from enum import Enum


class LetterStatus(Enum):
    PERFECT_MATCH = "perfect match"
    FOUND_BUT_WRONG_POSITION = "incorrect position"
    NOT_FOUND = "not found"


@dataclass(frozen=True)
class LetterResult:
    letter: str  # char
    position: int  # 0-indexed
    status: LetterStatus


@dataclass(frozen=True)
class GuessResult:
    guess: str
    results: list[LetterResult]  # letter, position (0-indexed), result


class SutomFSM:
    def __init__(self, ground_truth_word: str):
        # ground-truth
        self.gt_word = ground_truth_word

        # no prediction yet
        self.past_results: list[GuessResult] = []

        # current state of prediction
        _state_of_pred: list[LetterStatus] = [
            LetterStatus.NOT_FOUND for _letter in self.gt_word
        ]

    @property
    def gt_letters(self) -> list[str]:
        return [letter for letter in self.gt_word]

    @property
    def past_guesses(self) -> list[str]:
        return [past_res.guess for past_res in self.past_results]

    @property
    def state_of_prediction(
        self,
    ) -> list[tuple[str, LetterStatus]]:  # [{letter: status}]
        # init
        preds = [(letter, LetterStatus.NOT_FOUND) for letter in self.gt_word]

        # update
        for idx, letter in enumerate(self.gt_word):
            for past_res in self.past_results:
                past_res_for_l = past_res.results[idx]
                if past_res_for_l.status == LetterStatus.PERFECT_MATCH:
                    preds[idx] = (letter, LetterStatus.PERFECT_MATCH)
                else:
                    continue

        return preds

    def how_many_guess_left_for(
        self, letter_guess: str, current_turn_results: list[LetterResult]
    ) -> int:
        "Count how many letters 'letter' are left to guess in the ground-truth word"
        assert letter_guess in self.gt_word, "letter should be in gt word"

        raw_count = sum([letter_in_gt == letter_guess for letter_in_gt in self.gt_word])

        already_found = 0  # count how many times we already guessed 'letter_guess'
        for current_turn_res in current_turn_results:
            letter_guessed = current_turn_res.letter
            guess_status = current_turn_res.status
            if (
                letter_guessed == letter_guess
                and guess_status
                != LetterStatus.PERFECT_MATCH  # perfect + incorrectly positioned
            ):
                already_found += 1

        return raw_count - already_found

    def guess(self, guess: str) -> GuessResult:
        assert len(guess) == len(self.gt_word), (
            "Guess word must have the same length as the ground truth word"
        )

        results: list[LetterResult | None] = [None] * len(
            self.gt_word
        )  # Pre-fill with None

        # Create mutable lists of ground truth and guess letters for easier consumption
        gt_letters_list: list[str | None] = list(self.gt_word)
        guess_letters_list: list[str | None] = list(guess)

        # Step 1: Identify PERFECT_MATCHes
        # Mark perfect matches and "consume" letters from both lists
        for i in range(len(self.gt_word)):
            if guess_letters_list[i] == gt_letters_list[i]:
                letter_guessed = guess_letters_list[i]
                assert letter_guessed is not None, "should not be None"
                results[i] = LetterResult(
                    letter=letter_guessed,
                    position=i,
                    status=LetterStatus.PERFECT_MATCH,
                )
                gt_letters_list[i] = None  # Mark as consumed
                guess_letters_list[i] = None  # Mark as consumed

        # Step 2: Identify FOUND_BUT_WRONG_POSITION and NOT_FOUND
        # Iterate through guess_letters that haven't been perfectly matched
        gt_counts_remaining = Counter(
            letter for letter in gt_letters_list if letter is not None
        )

        for i in range(len(self.gt_word)):
            # Skip if already perfectly matched
            if results[i] is not None:
                continue

            current_guess_letter = guess_letters_list[i]

            if (
                current_guess_letter is not None
                and gt_counts_remaining[current_guess_letter] > 0
            ):
                results[i] = LetterResult(
                    letter=current_guess_letter,
                    position=i,
                    status=LetterStatus.FOUND_BUT_WRONG_POSITION,
                )
                gt_counts_remaining[current_guess_letter] -= 1  # Consume one instance
            elif current_guess_letter is not None:
                results[i] = LetterResult(
                    letter=current_guess_letter,
                    position=i,
                    status=LetterStatus.NOT_FOUND,
                )
            else:
                raise ValueError("Should not be none")

        # to help catch pblms early
        assert all(res is not None for res in results)
        res = GuessResult(guess=guess, results=results)  # pyright: ignore
        self.past_results.append(res)
        return res
