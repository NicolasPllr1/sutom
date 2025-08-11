from pathlib import Path

if __name__ == "__main__":
    data_dir = Path("data")
    file = "fr-nouns_filtered.txt"

    with open(data_dir / file, "r") as f:
        nouns = [line.strip() for line in f if line.strip()]
        print("Nouns:", len(nouns))

    SIZES = [2, 3, 4, 5, 6, 7, 8]

    for size in SIZES:
        subset: list[str] = []
        for w in nouns:
            if len(w) == size:
                subset.append(w)
        print(f"Size {size}: {len(subset)} nouns")
