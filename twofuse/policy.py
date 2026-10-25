"""Move selection. Each policy returns (first_tap, second_tap) cell indices, or None."""
from __future__ import annotations

import random

from twofuse.game import Board, dist, fuse, legal_pairs


def _ordered(board: Board, last: int | None):
    """Every legal pair in both tap orders with its pointer travel cost in cells."""
    for i, j in legal_pairs(board):
        for a, b in ((i, j), (j, i)):
            travel = dist(a, b) + (dist(last, a) if last is not None else 0.0)
            yield a, b, travel


def random_policy(board: Board, last: int | None, rng: random.Random):
    pairs = legal_pairs(board)
    if not pairs:
        return None
    i, j = rng.choice(pairs)
    return (i, j) if rng.random() < 0.5 else (j, i)


def nearest_policy(board: Board, last: int | None, rng: random.Random):
    """Cheapest pointer path, ignoring what the fuse does to the board."""
    best = min(_ordered(board, last), key=lambda x: x[2], default=None)
    return None if best is None else best[:2]


def smart_policy(board: Board, last: int | None, rng: random.Random):
    """Cheap pointer path, but also keep the board healthy.

    * Prefer fusing 2s and stars: leftover high-value tiles can only pair with their own kind,
      so they clutter the board and eventually starve it of pairs.
    * When the board is sparse, never pick a fuse that leaves no pair for the next move.
    """
    tiles = sum(t is not None for t in board)
    best, best_cost = None, float("inf")
    for a, b, travel in _ordered(board, last):
        cost = travel
        if board[a].value != "1":
            cost -= 1.5
        if tiles <= 11:
            after = list(board)
            fuse(after, a, b)
            remaining = len(legal_pairs(after))
            if remaining == 0:
                cost += 100
            else:
                cost -= 0.4 * min(remaining, 4)
        if cost < best_cost:
            best, best_cost = (a, b), cost
    return best


POLICIES = {"random": random_policy, "nearest": nearest_policy, "smart": smart_policy}
