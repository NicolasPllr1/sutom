import json
from functools import lru_cache
from itertools import chain
from pathlib import Path

from rich import print

from src.player import Player
from src.sutom_engine import GuessResult, LetterResult, LetterStatus


def filter_vocab_on_size(gt_length: int, vocab: list[str]) -> list[str]:
    "Filter the input vocab for words matching the 'ground-truth' word length"
    return [w for w in vocab if len(w) == gt_length]


def flatten(list_of_lists):
    """Flatten one level of nesting.
    see: https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    return chain.from_iterable(list_of_lists)


class InfoTheory(Player):
    def __init__(self, gt_length: int, vocab: list[str], save_dir: Path):
        self.gt_length = gt_length
        self.vocab = filter_vocab_on_size(gt_length, vocab)

        self.potential_answers = self.vocab

        save_dir.mkdir(exist_ok=True, parents=True)
        self.save_dir = save_dir

    def guess(self, past_guess_results: list[GuessResult]) -> str:
        ### Identify _good_ and _bad_ letters from past guesses

        # 1. Get good letters (letters known to be in the gt)
        letters_in_gt, good_letters = self.get_good_letters(past_guess_results)

        # 2. Get bad letters (letters known _not_ to be in the gt)
        # Note that this needs to be done _second_  as it uses the 'good_letters' information
        # to deal with 'multiplicity'
        _, bad_letters = self.get_bad_letters(past_guess_results, good_letters)

        ### filter the pool of potential answers

        # Remove a candidate if it:

        # 1) contains any _bad_ letters
        self.filter_on_bad_letter(bad_letters)

        # 2) does not contain all _good_ letters OR does not contain them at the correct positions if they were perfect matches
        self.filter_on_good_letters(letters_in_gt)

        # Early return if the pool of candidates has been reduced to a single word!
        if len(self.potential_answers) == 1:
            return self.potential_answers[0]

        ### Compute 'scores' (approximation of the expected #candidates a guess will eliminate)

        guess_nb = len(past_guess_results)  # for caching purposes
        # compute each letter `entropy-reducing power', i.e. how many potential answer does it eliminates on average (expected value)
        scores_per_word = {w: self.compute_word_score(w, guess_nb) for w in self.vocab}

        # sort
        sorted_scores_per_word = dict(
            sorted(scores_per_word.items(), key=lambda item: item[1], reverse=True)
        )
        self.save_scores(sorted_scores_per_word)

        return list(sorted_scores_per_word.items())[0][0]

    def get_good_letters(
        self, past_guess_results: list[GuessResult], debug: bool = False
    ) -> tuple[set[LetterResult], list[str]]:
        def letter_is_in_gt(lres: LetterResult) -> bool:
            return lres.status != LetterStatus.NOT_FOUND

        all_guessed_letter_results = flatten(
            guess_res.results for guess_res in past_guess_results
        )

        letters_in_gt = set(
            filter(letter_is_in_gt, all_guessed_letter_results),
        )

        good_letters = [good_res.letter for good_res in letters_in_gt]

        if debug:
            print(
                "\n"
                + f"Letters known to be in the gt ({len(letters_in_gt)}): {letters_in_gt}"
                + "\n"
            )
        return letters_in_gt, good_letters

    def get_bad_letters(
        self,
        past_guess_results: list[GuessResult],
        good_letters: list[str],
        debug: bool = False,
    ) -> tuple[set[LetterResult], list[str]]:
        all_guessed_letter_results = flatten(
            guess_res.results for guess_res in past_guess_results
        )

        def letter_is_not_in_gt(lres: LetterResult) -> bool:
            return (
                lres.status == LetterStatus.NOT_FOUND
                and lres.letter not in good_letters
            )

        letters_not_in_gt = set(
            filter(letter_is_not_in_gt, all_guessed_letter_results),
        )

        bad_letters = [bad_res.letter for bad_res in letters_not_in_gt]

        if debug:
            print(
                "\n"
                + f"Letters known to be non-present in the gt ({len(letters_not_in_gt)}): {letters_not_in_gt}"
                + "\n"
            )
        return letters_not_in_gt, bad_letters

    def filter_on_bad_letter(self, bad_letters: list[str], debug: bool = False):
        """
        Filter the pool of potential answers by removing candidates which contain
        at least one known _bad_ letter.
        """

        def not_a_single_bad_letter(word: str) -> bool:
            return all([letter not in bad_letters for letter in word])

        self.potential_answers = list(
            filter(not_a_single_bad_letter, self.potential_answers)
        )  # NOTE: side-effect, change potential_answers in-place

        if debug:
            print(
                "\n"
                + f"Potential answers - after filter on 'bad' letters presence: {len(self.potential_answers)}"
                + "\n"
            )

    def filter_on_good_letters(
        self, letters_in_gt: set[LetterResult], debug: bool = False
    ):
        """
        Filter the pool of potential answers by removing candidates which either:

        - do not contain all the known _good_ letters
        - OR do not contain them at the correct positions if they were a perfect matches.
        """

        def contains_all_good_letters_at_the_right_position(word: str) -> bool:
            return all(
                [
                    good_letter.letter == word[good_letter.position]
                    if good_letter.status == LetterStatus.PERFECT_MATCH
                    else good_letter.letter in word
                    for good_letter in letters_in_gt
                ]
            )

        self.potential_answers = list(
            filter(
                contains_all_good_letters_at_the_right_position, self.potential_answers
            )
        )  # NOTE: side-effect, change potential_answers in-place

        if debug:
            print(
                "\n"
                + f"Potential answers - after filter on `good` letters absence: {len(self.potential_answers)}"
                + "\n"
            )

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
    def letter_probability_at_idx(self, letter: str, idx: int, guess_nb: int) -> float:
        """Compute P(gt[idx] == letter | gt in potential-answers),
        where 'gt' is the ground-truth word.

        This boils down to looking at the frequency of the `letter`
        being at position 'idx' in the current pool of 'self.potential_answers'.

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
    def letter_probability_not_in_gt(self, letter: str, guess_nb: int) -> float:
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
        p = match_count / len(self.potential_answers)
        return p

    ### end term 3
    @lru_cache
    def nb_words_without_letter_or_perfect_match(
        self, letter: str, idx: int, guess_nb: int
    ) -> int:
        return len(
            [w for w in self.potential_answers if letter not in w or w[idx] == letter]
        )  # TODO: which is faster/better, len([]) or sum() ? probably len() as its O(1) : https://wiki.python.org/moin/TimeComplexity

    @lru_cache
    def compute_expected_word_eliminated_by_letter_at_idx(
        self, letter: str, idx: int, guess_nb: int
    ) -> float:
        """
        Expected number of words eliminated by a single letter at
        position "idx". This expectation is the sum of 3 terms
        corresponding to the 3 possible situations:
        - the letter at 'idx' is a perfect match
        - the letter is not found in the ground-truth word
        - the letter is in the ground-truth word, but not at
        position 'idx'

        See the accompanying info_theoretic_player.md for more information.
        """
        term_perfect_match = self.letter_probability_at_idx(
            letter, idx, guess_nb
        ) * self.nb_words_different_letter_at_idx(letter, idx, guess_nb)

        term_not_in_gt = self.letter_probability_not_in_gt(
            letter, guess_nb
        ) * self.nb_words_with_letter(letter, guess_nb)

        term_incorrect_position = self.letter_probability_incorrect_position(
            letter, idx, guess_nb
        ) * self.nb_words_without_letter_or_perfect_match(letter, idx, guess_nb)

        return term_perfect_match + term_not_in_gt + term_incorrect_position

    def compute_word_score(self, word: str, guess_nb: int) -> float:
        return sum(
            self.compute_expected_word_eliminated_by_letter_at_idx(
                letter, idx, guess_nb
            )
            for idx, letter in enumerate(word)
        )
