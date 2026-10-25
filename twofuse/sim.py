"""Stochastic model of one 2Fuse run, for comparing move policies.

The refill model and the tap-time model are ESTIMATES (from one recorded run and a guess at
hardware speed). Power-up effects are not modeled. Use the results to compare policies against
each other, not as a prediction of an exact combo.
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from twofuse.game import Board, Tile, dist, fuse
from twofuse.policy import POLICIES

COLORS = "RGB"


@dataclass
class Params:
    game_seconds: float = 60.0
    start_tiles: int = 9
    slow_refill: tuple[float, float] = (1.2, 3.5)  # seconds an empty cell waits before the first cycle
    fast_refill: float = 0.3  # seconds after the first cycle
    cycle_combo: int = 30  # combo at which the board starts refilling fast
    tap_s: float = 0.05  # fixed cost of one tap
    s_per_cell: float = 0.03  # pointer travel cost per cell of distance


def _new_tile(rng: random.Random) -> Tile:
    return Tile(rng.choice(COLORS), "1")


def play(policy_name: str, params: Params, seed: int) -> int:
    rng = random.Random(seed)
    policy = POLICIES[policy_name]
    board: Board = [None] * 16
    for i in rng.sample(range(16), params.start_tiles):
        board[i] = _new_tile(rng)
    respawn_at: dict[int, float] = {}
    t, combo, last = 0.0, 0, None

    def schedule(cell: int) -> None:
        delay = params.fast_refill if combo >= params.cycle_combo else rng.uniform(*params.slow_refill)
        respawn_at[cell] = t + delay

    while t < params.game_seconds:
        for cell, when in list(respawn_at.items()):
            if when <= t:
                board[cell] = _new_tile(rng)
                del respawn_at[cell]
        move = policy(board, last, rng)
        if move is None:
            t += 0.05  # nothing to fuse yet; wait for a refill
            continue
        a, b = move
        t += 2 * params.tap_s + params.s_per_cell * (dist(a, b) + (dist(last, a) if last is not None else 0.0))
        fuse(board, a, b)
        schedule(a)
        if board[b] is None:
            schedule(b)
        combo += 1
        last = b
    return combo


def evaluate(policy_name: str, params: Params, games: int = 300) -> dict[str, float]:
    results = sorted(play(policy_name, params, seed) for seed in range(games))
    return {
        "mean": statistics.mean(results),
        "median": results[len(results) // 2],
        "p95": results[int(0.95 * len(results))],
        "max": results[-1],
    }


if __name__ == "__main__":
    base = Params()
    print(f"tap_s={base.tap_s}  s_per_cell={base.s_per_cell}  (placeholders until measured on hardware)")
    for name in POLICIES:
        r = evaluate(name, base)
        print(f"{name:8s} mean {r['mean']:6.1f}  median {r['median']:4d}  p95 {r['p95']:4d}  max {r['max']:4d}")
