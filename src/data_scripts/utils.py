from pathlib import Path

import spacy
from tqdm import tqdm


def extract_french_nouns_from_file(
    filename: str, file_dir: Path, batch_size: int = 30_000
) -> set[str]:
    try:
        nlp = spacy.load(
            "fr_core_news_sm", disable=["parser", "ner", "attribute_ruler"]
        )
    except OSError:
        print("SpaCy French model 'fr_core_news_sm' not found.")
        print("Please download it by running: python -m spacy download fr_core_news_sm")
        return set()

    found_words: set[str] = set()
    filepath = file_dir / filename

    if not filepath.exists():
        print(f"Error: File not found at '{filepath}'")
        return set()

    try:
        print("Processing words with SpaCy in batches...")
        with open(filepath, "r", encoding="utf-8") as f:
            #  generator that yields one word per line
            # (efficient as it doesn't load the entire file into memory)
            words_generator = (line.strip() for line in f if line.strip())

            # npl.pipe processes an iterable of texts and yields Doc objects.
            for doc in tqdm(
                nlp.pipe(words_generator, batch_size=batch_size),
                unit="word",
                mininterval=0.1,
            ):
                for token in doc:
                    if token.pos_ == "NOUN" or token.pos_ == "VERB":
                        # token.lemma_ to get the base form
                        found_words.add(token.lemma_.lower())
    except Exception as e:
        print(f"An error occurred while reading or processing the file: {e}")

    return found_words
