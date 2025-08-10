from itertools import chain, count
from pathlib import Path

from rich import print

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

        vocab = self.vocab
        print(f"\nOriginal (filtered) vocab size: {len(vocab)}")

        all_guessed_letter_results = set(
            flatten([guess_res.results for guess_res in past_guess_results])
        )

        # FIRST - get letters known to be in the gt (good letters)
        def letter_is_in_gt(lres: LetterResult) -> bool:
            return lres.status != LetterStatus.NOT_FOUND

        letters_in_gt = set(
            map(
                lambda res: res.letter,
                filter(letter_is_in_gt, all_guessed_letter_results),
            )
        )
        print(
            f"\nLetters known to be in the gt ({len(letters_in_gt)}): {letters_in_gt}"
        )

        # SECOND - get letters known *not* to be in the gt (bad letters)
        # NOTE: why second ? because a gt-letter may be identified first as a 'perfect-match',
        # and after that as 'not-found' in the same guess (if this letter is only present *once* on the gt).
        # -> We don't want this letter to be in *both* lists: only in 'letters_in_gt' (good letters)
        def letter_is_not_in_gt(lres: LetterResult) -> bool:
            return lres.status == LetterStatus.NOT_FOUND

        letters_not_in_gt = set(
            map(
                lambda res: res.letter,
                filter(letter_is_not_in_gt, all_guessed_letter_results),
            )
        )

        # check to remove good letters, cf note above
        letters_not_in_gt = set(
            filter(
                lambda bad_letter: bad_letter not in letters_in_gt,
                letters_not_in_gt,  # bad letter may actually be good
            )
        )
        print(
            f"\nLetters known to be non-present in the gt ({len(letters_not_in_gt)}): {letters_not_in_gt}"
        )

        ### filter the potential answers

        # remove if: *contains* letters that are known *not* to be present in the gt
        def not_a_single_bad_letter(word: str) -> bool:
            return all([letter not in letters_not_in_gt for letter in word])

        potential_answers = list(filter(not_a_single_bad_letter, vocab))
        print(
            f"Potential answers - after filter on 'bad' letters presence: {len(potential_answers)}\n"
        )
        self.vocab = potential_answers

        # remove if: does *not* contain letters that are known to be in the gt
        def contains_all_good_letters(word: str) -> bool:
            return all([good_letter in word for good_letter in letters_in_gt])

        potential_answers = list(filter(contains_all_good_letters, potential_answers))

        print(
            f"Potential answers - after filter on `good` letters abscence: {len(vocab)}"
        )

        self.potential_answers = potential_answers

        self.vocab = potential_answers

        ### compute 'scores'

        # compute each letter `entropy-reducing power', i.e. how many potential answer does it eliminates on average (expected value)
        scores_per_word = {w: self.compute_word_score(w) for w in self.vocab}

        # sort
        sorted_scores_per_word = dict(
            sorted(scores_per_word.items(), key=lambda item: item[1], reverse=True)
        )

        # save scores
        self.save_scores(sorted_scores_per_word)

        return list(sorted_scores_per_word.items())[0][0]

    def save_scores(self, scores: dict[str, float]):
        lines = ["{\n"]
        for word, score in scores.items():
            lines.append(f"  '{word}': {score}\n")
        lines.append("}")

        nb_files = len(list(self.save_dir.rglob("*.json")))
        filename = f"guess_{nb_files + 1}.json"
        with open(self.save_dir / filename, "w") as f:
            f.writelines(lines)
        f.close()

    def letter_probablity_at_idx(self, letter: str, idx: int) -> float:
        assert len(letter) == 1, "letter should be str of length 1"
        assert 0 <= idx < self.gt_length, (
            "Index should be between 0 (inclusive) and gt-length (exclusive)"
        )

        match_count = sum(1 for w in self.vocab if w[idx] == letter)
        p = match_count / len(self.vocab)

        assert 0 <= p <= 1, "probability should be in [0, 1]"
        return p

    def letter_probablity_not_in_gt(self, letter: str) -> float:
        assert len(letter) == 1, "letter should be str of length 1"

        match_count = sum(1 for w in self.vocab if letter not in w)
        p = match_count / len(self.vocab)

        assert 0 <= p <= 1, "probability should be in [0, 1]"
        return p

    def letter_probability_incorrect_position(self, letter: str, idx: int) -> float:
        match_count = sum(1 for w in self.vocab if letter in w and w[idx] != letter)
        p = match_count / len(self.vocab)
        return p

    # NOTE: could lru cache 'expensive' functions we may call many times with the same args. But careful of side effects
    def compute_expected_word_eliminated_by_letter_at_idx(
        self, letter: str, idx: int
    ) -> float:
        p = self.letter_probablity_at_idx(letter, idx)

        nb_words_different_letter_at_idx = len(
            [w for w in self.vocab if w[idx] != letter]
        )
        term_perfect_match = p * nb_words_different_letter_at_idx
        # print("Term perfect match: (1):", term_perfect_match)

        nb_words_with_letter = len([w for w in self.vocab if letter in w])
        term_not_in_gt = self.letter_probablity_not_in_gt(letter) * nb_words_with_letter
        # print("Term not in gt: (2):", term_not_in_gt)

        term_incorrect_position = self.letter_probability_incorrect_position(
            letter, idx
        ) * len([w for w in self.vocab if letter not in w or w[idx] == letter])
        # print("Term incorrect position (3):", term_incorrect_position)

        return term_perfect_match + term_not_in_gt + term_incorrect_position

    def compute_word_score(self, word: str) -> float:
        return sum(
            map(
                self.compute_expected_word_eliminated_by_letter_at_idx,
                word,
                count(),
            )
        )
