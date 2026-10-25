"""2Fuse rules as observed from a recorded run.

Observed (see NOTES.md for how):
  * Any two tiles with the same color and the same value fuse. They do NOT need to be adjacent.
  * 1+1 -> 2 and 2+2 -> star. The fused tile keeps one cell, the other cell goes empty.
  * Two stars of the same color are consumed and trigger a power-up.
  * Empty cells are refilled with new "1" tiles of a random color.
  * The combo counts consecutive successful fuses; a mismatched tap is what we believe resets it.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

CELL_PX = 130  # board cell pitch in the 540-wide recording; only used for distances
N = 4

NEXT_VALUE = {"1": "2", "2": "S"}


@dataclass(frozen=True)
class Tile:
    color: str  # R, G or B
    value: str  # "1", "2" or "S"


Board = list[Tile | None]  # 16 cells, row-major


def rc(i: int) -> tuple[int, int]:
    return divmod(i, N)


def dist(i: int, j: int) -> float:
    (r1, c1), (r2, c2) = rc(i), rc(j)
    return ((r1 - r2) ** 2 + (c1 - c2) ** 2) ** 0.5


def legal_pairs(board: Board) -> list[tuple[int, int]]:
    return [
        (i, j)
        for i, j in combinations(range(len(board)), 2)
        if board[i] is not None and board[i] == board[j]
    ]


def fuse(board: Board, first: int, second: int) -> str:
    """Apply a fuse in place. The survivor stays on `second`. Returns 'upgrade' or 'star'."""
    a, b = board[first], board[second]
    assert a is not None and a == b, "fuse needs two identical tiles"
    board[first] = None
    if a.value == "S":
        board[second] = None
        return "star"
    board[second] = Tile(a.color, NEXT_VALUE[a.value])
    return "upgrade"


def parse(tokens: list[str]) -> Board:
    """Build a Board from vision tokens such as 'R1', 'GS', '..', '?2'."""
    out: Board = []
    for tok in tokens:
        out.append(None if tok == ".." or tok[0] == "?" else Tile(tok[0], tok[1]))
    return out
