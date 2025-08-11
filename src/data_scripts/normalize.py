from pathlib import Path

from unidecode import unidecode

# https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
if __name__ == "__main__":
    data_dir = Path("data")
    input_file = "fr-nouns_filtered.txt"

    output_file = "fr-nouns_filtered_normalized.txt"

    print("Loading...")
    with open(data_dir / input_file, "r") as f:
        nouns = [line.strip() for line in f if line.strip()]
        print("Nouns:", len(nouns))

    print("Normalizing...")
    normalized_nouns = [unidecode(w) for w in nouns]

    print("Saving...")
    with open(data_dir / output_file, "w") as f:
        for w in normalized_nouns:
            f.write(f"{w}\n")
