from pathlib import Path
from functools import lru_cache
import json

from rich import print

from itertools import chain, count

from player import player
from sutom import GuessResult, LetterResult, LetterStatus


def filter_vocab_on_size(gt_length: int, vocab: list[str]) -> list[str]:
    return [w for w in vocab if len(w) == gt_length]


def flatten(list_of_lists):
    "Flatten one level of nesting."
    return chain.from_iterable(list_of_lists)


class InfoTheory(player):
    def __init__(self, gt_length: int, vocab: list[str], save_dir: Path):
        self.gt_length = gt_length
        self.vocab = filter_vocab_on_size(gt_length, vocab)

        self.potential_answers = self.vocab

        save_dir.mkdir(exist_ok=True, parents=True)
        self.save_dir = save_dir

    def guess(self, past_guess_results: list[GuessResult]) -> str:
        ### identify *good* and *bad* letters from past guesses

        all_guessed_letter_results = set(
            flatten([guess_res.results for guess_res in past_guess_results])
        )

        # FIRST - get letters known to be in the gt (good letters)
        def letter_is_in_gt(lres: LetterResult) -> bool:
            return lres.status != LetterStatus.NOT_FOUND

        letters_in_gt = set(
            filter(letter_is_in_gt, all_guessed_letter_results),
        )

        good_letters = [good_res.letter for good_res in letters_in_gt]
        print(
            f"\nLetters known to be in the gt ({len(letters_in_gt)}): {letters_in_gt}"
        )

        # TODO: proper handling of multiplicity

        # SECOND - get letters known *not* to be in the gt (bad letters)
        def letter_is_not_in_gt(lres: LetterResult) -> bool:
            return (
                lres.status == LetterStatus.NOT_FOUND
                and lres.letter not in good_letters
            )

        letters_not_in_gt = set(
            filter(letter_is_not_in_gt, all_guessed_letter_results),
        )

        print(
            f"Letters known to be non-present in the gt ({len(letters_not_in_gt)}): {letters_not_in_gt}"
        )

        ### filter the potential answers

        # 1) remove if: *contains* letters that are known *not* to be present in the gt
        bad_letters = [bad_res.letter for bad_res in letters_not_in_gt]

        def not_a_single_bad_letter(word: str) -> bool:
            return all([letter not in bad_letters for letter in word])

        potential_answers = list(
            filter(not_a_single_bad_letter, self.potential_answers)
        )
        print(
            f"\nPotential answers - after filter on 'bad' letters presence: {len(potential_answers)}"
        )
        print(f"bad letters: {[res.letter for res in letters_not_in_gt]}\n")

        # 2) remove if: does *not* contain letters that are known to be in the gt and at the correct position if it was a perfect match
        def contains_all_good_letters_at_the_right_position(word: str) -> bool:
            return all(
                [
                    good_letter.letter == word[good_letter.position]
                    if good_letter.status == LetterStatus.PERFECT_MATCH
                    else good_letter.letter in word
                    for good_letter in letters_in_gt
                ]
            )

        potential_answers = list(
            filter(contains_all_good_letters_at_the_right_position, potential_answers)
        )

        print(
            f"Potential answers - after filter on `good` letters abscence: {len(potential_answers)}"
        )
        print(f"good letters: {[res.letter for res in letters_in_gt]}")

        self.potential_answers = potential_answers

        if len(potential_answers) == 1:
            return potential_answers[0]

        ### compute 'scores'

        # compute each letter `entropy-reducing power', i.e. how many potential answer does it eliminates on average (expected value)
        guess_nb = len(past_guess_results)
        scores_per_word = {w: self.compute_word_score(w, guess_nb) for w in self.vocab}

        # sort
        sorted_scores_per_word = dict(
            sorted(scores_per_word.items(), key=lambda item: item[1], reverse=True)
        )

        # save scores
        self.save_scores(sorted_scores_per_word)

        return list(sorted_scores_per_word.items())[0][0]

    def save_scores(self, scores: dict[str, float]):
        data = {
            "potential_answer_pool_size": self.potential_answers,
            "scores": {word: score for word, score in scores.items()},
        }

        nb_files = len(list(self.save_dir.rglob("*.json")))
        filename = f"guess_{nb_files + 1}_v2.json"
        with open(self.save_dir / filename, "w") as f:
            f.write(json.dumps(data, indent=2))
        f.close()

    ### start term 1
    @lru_cache()
    def letter_probablity_at_idx(self, letter: str, idx: int, guess_nb: int) -> float:
        """Compute P(gt[idx] == letter | gt in potential-answers)

        This boils down to looking at the frequency of the `letter`
        in the current pool of 'self.potential_answers'.

        The current pool of potential answers is a sub-set of the
        initial vocabulary. As guesses are made and information is
        gained, this pool size gets smaller and smaller!
        """

        # some guards to catch bugs early
        assert len(letter) == 1, "letter should be str of length 1"
        assert 0 <= idx < self.gt_length, (
            "Index should be between 0 (inclusive) and gt-length (exclusive)"
        )

        match_count = sum(1 for w in self.potential_answers if w[idx] == letter)
        p = match_count / len(self.potential_answers)

        # more guards
        assert 0 <= p <= 1, "probability should be in [0, 1]"
        return p

    @lru_cache
    def nb_words_different_letter_at_idx(
        self, letter: str, idx: int, guess_nb: int
    ) -> int:
        return len([w for w in self.potential_answers if w[idx] != letter])

    ### end term 1

    ### start term 2
    @lru_cache
    def letter_probablity_not_in_gt(self, letter: str, guess_nb: int) -> float:
        assert len(letter) == 1, "letter should be str of length 1"

        match_count = sum(1 for w in self.potential_answers if letter not in w)
        p = match_count / len(self.potential_answers)

        assert 0 <= p <= 1, "probability should be in [0, 1]"
        return p

    @lru_cache
    def nb_words_with_letter(self, letter: str, guess_nb: int) -> int:
        return len([w for w in self.potential_answers if letter in w])

    ### end term 2

    ### start term 3
    @lru_cache
    def letter_probability_incorrect_position(
        self, letter: str, idx: int, guess_nb: int
    ) -> float:
        match_count = sum(
            1 for w in self.potential_answers if letter in w and w[idx] != letter
        )
        p = match_count / len(self.vocab)
        return p

    ### end term 3
    @lru_cache
    def nb_words_without_letter_or_perfect_match(
        self, letter: str, idx: int, guess_nb: int
    ) -> int:
        return len(
            [w for w in self.potential_answers if letter not in w or w[idx] == letter]
        )

    @lru_cache
    def compute_expected_word_eliminated_by_letter_at_idx(
        self, letter: str, idx: int, guess_nb: int
    ) -> float:
        ### term 1
        term_perfect_match = self.letter_probablity_at_idx(
            letter, idx, guess_nb
        ) * self.nb_words_different_letter_at_idx(letter, idx, guess_nb)

        ### term 2
        term_not_in_gt = self.letter_probablity_not_in_gt(
            letter, guess_nb
        ) * self.nb_words_with_letter(letter, guess_nb)

        ### term 3
        term_incorrect_position = self.letter_probability_incorrect_position(
            letter, idx, guess_nb
        ) * self.nb_words_without_letter_or_perfect_match(letter, idx, guess_nb)

        return term_perfect_match + term_not_in_gt + term_incorrect_position

    def compute_word_score(self, word: str, guess_nb: int) -> float:
        return sum(
            map(
                lambda letter,
                idx: self.compute_expected_word_eliminated_by_letter_at_idx(
                    letter, idx, guess_nb
                ),
                word,
                count(),
            )
        )
