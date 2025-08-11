from src.play_sutom import play
from src.player import PlayerKind

PLAYER_KIND = PlayerKind.AI

if __name__ == "__main__":
    # ground_truth_word = "amour"
    ground_truth_word = "telephone"

    play(ground_truth_word, player_kind=PLAYER_KIND, max_iter=10)
