import random
from pathlib import Path

if __name__ == "__main__":
    data_dir = Path("data")
    file = "fr-nouns_filtered.txt"

    SIZE = 200
    output_file = "fr-nouns_subset.txt"

    with open(data_dir / file, "r") as f:
        nouns = [line.strip() for line in f if line.strip()]
        print("Nouns:", len(nouns))

    nouns = [w for w in nouns if len(w) == 5]

    subset = random.sample(nouns, SIZE)
    print("Subset:", len(subset))

    print("saving subset ...")
    with open(data_dir / output_file, "w") as f:
        for w in subset:
            _res = f.write(f"{w}\n")
    print("done saving")
