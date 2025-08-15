# Change log

## v1

- v1: was implicitely using potential_answers = orignal_vocab

## v2

- v2
  - what changed ? introduced `potential_answers`. Although we compute the scores
    of all words in the original vocab, we compute their "entropy reducing
    power" on the pool of potential answers, not the entire vocab.
  - too slow, gt = "telephone" can't be processed in reasonable time. What's the
    current complexity ?

### Complexity

Identifying good/bad letters from past guesses is O(#guess) = O(1) as we limit
the #guess to say, 10.

Then, how many pass over the vocab ? Over potential answers ? This is what costs.

Filtering potential answers:

- Filter-out words which contains at least one bad letter

O(#potential_answers * #mean_word_length) = O(#potential_answers)

- Filter-out words which either do not contain all the good letters or do not
 contain them at the right position

O(#potential_answers * #good_letters) = O(#potential_answers)

Computing the 'score' of every word in the vocab:

- map over the word letters to compute a single letter score : #word_length

For a letter at some index:

- get its probability of being a perfect match: O(#potential_snwers)
- nb_words_different_letter_at_idx: O(#potential_snwers)

- letter_probablity_not_in_gt: O(#potential_answers)
- nb_words_with_letter: O(#potential_snwers)

- letter_probability_incorrect_position: O(#potential_snwers)
- len of the set of words either not contening the letter or contenining it at
 the exact index: O(#potential_snwers)

 --> 6 * #potential_snwers # #word_length
Conclusion: a guess complexity is proportional to the size of the answer pool.

--> We do that for *every* word in the vocab, so we are in the
O(#vocab*#potential_answers) territory.


Big O notation is not necessarily the most appropriate tool here as 6x is very
 different than x here. We care about the constants.

Optimization: we should cache every intermediary computation that is O(#potential_answers):

- letter_probablity_at_idx
- nb_words_different_letter_at_idx

- letter_probablity_not_in_gt
- nb_words_with_letter

- letter_probability_incorrect_position
- another set length


### Performance optimizations

- LRU cache: even though self was passed to methods and self 'changed' because
 self.potential_answers changed with each round, the methods did seem to be cached
  successfully. [Context from python faq](https://docs.python.org/3/faq/programming.html#id70)

- next: // with threads. But is it possible (GIL issues? ok in 3.13 ?)
- better maths ?


