# Basic information theoretic algorithm

## The problem

Let's say the word to guess `w_truth` is 3-letter long : '\_ _ \_'. All 3-letter
lon words in our vocabulary `V` could be `w_truth`.

Our goal for our first guess is to choose the word `w_guess` which will
_eliminate_ the most words out of the pool of potential answers. For now, this
pool is equal to the entire vocab `V`. After guessing `w_guess`, this pool will
be reduced thanks to the information the sutom game will give us:

- perfect match letters
- letters present in `w_truth` but in the incorrect position in `w_guess`
- and letters which are not found in `w_truth`.

Note 1: our guess `w_guess` will eliminate letters from the pool of potential
answers on a letter-by-letter basis.

More precisely, a letter `l_guess` in our guess at position `idx` can be one of
three things:

- **Not found**: `l_guess` is _not_ in `w_truth` => all words in our pool of
  potential answers which _do contain_ `l_guess` are eliminated
- **Good match but incorrect position**: `l_guess` is in `w_truth` but _not_ at
  position `idx` => all words in our pool of potential answers which _do
  contain_ the `l_guess` at position `idx` are eliminated, AND all words which
  _do not_ contain `l_guess` are also eliminated
- **Perfect match**: `l_guess` is in `w_truth` at the position `idx` => all
  words which do _not_ contain `l_guess` at position `idx` are eliminated, AND
  all words which _do not_ contain `l_guess` are also eliminated

For a given `l_guess` at `idx`, we can't know in advance which situation will
arise as we don't know `w_truth`. We can model the problem using probabilities,
as the only information we know is that `w_truth` was 'drawn' from the
vocabulary `V`. Following this interpretation, we can compute, for any letter
`l_guess` guessed at position `idx`, the expected number of words it will
eliminate.

To do so, we have to compute how many words are eliminated in each cases, and
sum them up ponderating each term by the probability the cases will arise.

'Expected number of words eliminated by `l_guess` at position `idx`' = P('Not
found' situation) * |{w in V, `l_guess` is in w}|

- P('Good match but incorrect position' situation) * |{w in V, `l_guess` is not
  in w OR `w[idx] == l_guess` }|
- P('Perfect match' situation) * |{w in V, `l_guess` is not in w OR
  `w[idx] != l_guess`}|

Okay! But how do we use this expectation, which we can compute for a given
letter and position, to choose the next 'best' word ?

We have to find the between how many words _letters at certain index_ can
eliminate, and how many words _a whole word_ can eliminate.

First, we have 'Number words eliminated by `w_guess`' = _sum_ of words
eliminated by its letters at their respective positions

NOTE: this is actually an over-estimation! Some potential answers may be
eliminated by multiple letters. Our sum would count this eliminated word twice!
But let's roll with it to get started.

(As a first approximation, we can assume that the number of words eliminated by
a given letter is independent from the same number for the other letters. Wait!
This is not needed, is it?)

Then, by linearity of the expectation, we have the number of words eliminated by
`w_guess` (its expectation) is simply the sum of words eliminated by its
individual letters at their respective position (their expectations)!

Computing each probability term is only a matter of counting frequencies in the
vocabulary `V` assuming `w_truth` was drawn uniformily from this vocab.

## Implementation change log

### v1

- v1: was implicitly using potential_answers = original_vocab

### v2

- v2
  - what changed ? introduced `potential_answers`. Although we compute the
    scores of all words in the original vocab, we compute their "entropy
    reducing power" on the pool of potential answers, not the entire vocab.
  - too slow, gt = "telephone" can't be processed in reasonable time. What's the
    current complexity ?

#### Complexity

Identifying good/bad letters from past guesses is O(#guess) = O(1) as we limit
the #guess to say, 10.

Then, how many pass over the vocab ? Over potential answers ? This is what
costs.

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

- letter_probability_not_in_gt: O(#potential_answers)

- nb_words_with_letter: O(#potential_snwers)

- letter_probability_incorrect_position: O(#potential_snwers)

- len of the set of words either not contening the letter or contenining it at
  the exact index: O(#potential_snwers)

--> 6 * #potential_snwers # #word_length Conclusion: a guess complexity is
proportional to the size of the answer pool.

--> We do that for *every* word in the vocab, so we are in the
O(#vocab\*#potential_answers) territory.

Big O notation is not necessarily the most appropriate tool here as 6x is very
different than x here. We care about the constants.

Optimization: we should cache every intermediary computation that is
O(#potential_answers):

- letter_probability_at_idx

- nb_words_different_letter_at_idx

- letter_probability_not_in_gt

- nb_words_with_letter

- letter_probability_incorrect_position

- another set length

#### Performance optimizations

- LRU cache: even though self was passed to methods and self 'changed' because
  self.potential_answers changed with each round, the methods did seem to be
  cached successfully.
  [Context from python faq](https://docs.python.org/3/faq/programming.html#id70)

- next: // with threads. But is it possible (GIL issues? ok in 3.13 ?)

- better maths ?
