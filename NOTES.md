# 2Fuse bot — findings and status

Goal: beat a personal best combo of 262 in 2Fuse (Mojo Forest, iOS, v2.7.5) with a bot.

## Rules, as observed from one recorded run (`b_bYSH1L.mp4`, 87 s, 540x1170 @ 30 fps)

| Rule | Confidence |
| --- | --- |
| 4x4 board, tiles are red / green / blue only (yellow/orange seen on screen is glow tint) | high |
| Any two tiles with the same color and value fuse; they do **not** have to be adjacent | high |
| 1+1 -> 2, 2+2 -> star; one cell keeps the result, the other goes empty | high |
| Two stars (same color) are consumed and trigger a power-up | medium |
| Empty cells refill with new "1" tiles of a random color | high |
| First ~25 s: board is sparse (5-7 empty), refill is slow (~2 s per tile) | medium |
| After the first cycle (combo ~30): board is full, refill is near-instant | medium |
| Combo +1 per successful fuse (153 upgrades detected vs 162 combo gained between combo 16 and 178) | high |
| A **mismatched tap resets the combo** (two tiles of different colors were highlighted just before the reset; gaps of up to ~1 s between fuses did *not* reset it) | **low, one observation** |
| Time slows during some power-ups (timer ran at ~0.75x) so a run lasts ~65 s of real time | medium |

Fuse rate in the recorded run: ~2.3/s in the sparse opening, 3.3-4.3/s once the board is full.

## What actually limits the combo

* A full board has ~25 legal pairs at any moment (never zero in the recording), so there is no strategic
  starvation. The only tight phase is the sparse opening (min 1 pair).
* So the combo is `fuses per second x ~65 s`, provided there are **zero mismatched taps**.
  262 needs about 4.0 fuses/s sustained; the simulator (`python -m twofuse.sim`) says roughly
  **150-160 ms per fuse** (about 6 fuses/s, ~75 ms per tap including pointer travel) puts the median above 262.
* Policy value: never mis-tap, pick the cheapest pointer path between taps, clear 2s/stars so they do not
  clutter the board. The sim's absolute numbers depend on placeholder tap timings, so trust the ordering
  of policies and the required-speed table, not the exact combo.

## Code

* `twofuse/vision.py` — reads the 4x4 board from a frame (color, value 1/2/star, empty). Verified by eye on
  frames at 20 s, 40 s, 80 s, including glow and burst effects. Returns `?` for color when an effect hides it.
* `twofuse/replay.py` — `python -m twofuse.replay video.mp4 states.txt [start] [end]` writes a per-frame timeline.
* `twofuse/game.py` — rules model. `twofuse/policy.py` — random / nearest / smart move pickers.
* `twofuse/sim.py` — stochastic run simulator with tunable `tap_s` and `s_per_cell`.
* `twofuse/debug_overlay.py` — draws the reader's labels on a frame to spot classifier mistakes.

Setup: `python -m venv .venv`, then `.venv/Scripts/python -m pip install -r requirements.txt`.

## Not done yet

1. **Tapper hardware.** iOS blocks software taps. Plan: an ESP32 acting as a Bluetooth mouse with iOS
   AssistiveTouch pointer control, driven from the PC over serial. Open risk: iOS pointer acceleration
   makes relative positioning unreliable, and it is unproven that it can reach ~75 ms per tap.
2. **Live screen capture** from the iPhone to the PC (AirPlay/QuickTime mirroring) feeding `vision.py`.
3. **Confirm the mismatch rule** with a deliberate wrong tap before trusting the "never mis-tap" assumption.
4. **Power-ups** (star colors, Tile Burn, time slow) are not modeled; the blue star slowing the timer is the
   one most likely to add fuses.
5. Vision still guesses on heavily flashed frames; a bot should vote across 2-3 frames before tapping.
