from pathlib import Path

from rich import print

from player import player
from sutom import GuessResult, LetterStatus


def filter_vocab_on_size(gt_length: int, vocab: list[str]) -> list[str]:
    return [w for w in vocab if len(w) == gt_length]


class InfoTheory(player):
    def __init__(self, gt_length: int, vocab: list[str], save_dir: Path):
        self.gt_length = gt_length
        self.vocab = filter_vocab_on_size(gt_length, vocab)
        self.save_dir = save_dir
        save_dir.mkdir(exist_ok=True, parents=True)

    def guess(self, past_guess_results: list[GuessResult]) -> str:
        ### filter vocab
        vocab = self.vocab
        print(f"\nOriginal (filtered) vocab size: {len(vocab)}")

        # FIRST - get letters known to be in the gt (good letters)
        letters_in_gt = set()
        for past_guess in past_guess_results:
            results = past_guess.results
            for letter_result in results:
                if (
                    letter_result.status != LetterStatus.NOT_FOUND
                ):  # i.e., perfect match or incorrect position
                    letters_in_gt.add(letter_result.letter)

        # SECOND - get letters known *not* to be in the gt (bad letters)
        # note: second as a letter may be tagged perfect-match once, and then 'not-found'
        # as it is present say just once in the gt. We don't want to have it in both lists. ONly in the letters_in_gt list of good letters
        letters_not_in_gt = set()
        for past_guess in past_guess_results:
            results = past_guess.results
            for letter_result in results:
                if letter_result.status == LetterStatus.NOT_FOUND:
                    letters_not_in_gt.add(letter_result.letter)
        # check to remove good letters, cf note above
        letters_not_in_gt = {
            letter for letter in letters_not_in_gt if letter not in letters_in_gt
        }

        # remove if: *contains* letters that are known *not* to be present in the gt
        vocab = [
            w
            for w in vocab
            if all([guess_letter not in letters_not_in_gt for guess_letter in w])
        ]
        print(
            f"\nLetters known to be non-present in the gt ({len(letters_not_in_gt)}): {letters_not_in_gt}"
        )
        print(
            f"vocab size - after filter on known bad letters presence: {len(vocab)}\n"
        )

        # remove if: does *not* contain letters that are known to be in the gt
        vocab = [
            w for w in vocab if all([gt_letter in w for gt_letter in letters_in_gt])
        ]
        self.vocab = vocab

        print(
            f"\nLetters known to be in the gt ({len(letters_in_gt)}): {letters_in_gt}"
        )
        print(f"vocab-size - after filter on non-present good letters: {len(vocab)}")

        self.vocab = vocab

        ### compute each letter `entropy-reducing power', i.e. how many words it eliminates on average (expected value)
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
            [
                self.compute_expected_word_eliminated_by_letter_at_idx(letter, idx)
                for idx, letter in enumerate(word)
            ]
        )
