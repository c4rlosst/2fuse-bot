"""Turn a screen recording into a per-frame board timeline.

    python -m twofuse.replay video.mp4 states.txt [start_s] [end_s]

Each output line is "<frame> <seconds> <16 cells row by row>", e.g. "812 27.07 G1 R1 ...".
"""
from __future__ import annotations

import subprocess
import sys

import numpy as np
from PIL import Image

from twofuse.vision import read_board

W, H = 540, 1170


def frames(path: str, start: float = 0.0, end: float | None = None):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path]
    if end is not None:
        cmd += ["-t", str(end - start)]
    cmd += ["-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = W * H * 3
    i = 0
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield i, np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        i += 1
    proc.wait()


def main() -> None:
    path, out = sys.argv[1], sys.argv[2]
    start = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    end = float(sys.argv[4]) if len(sys.argv) > 4 else None
    fps = 30.0
    with open(out, "w") as fh:
        for i, arr in frames(path, start, end):
            board = read_board(Image.fromarray(arr))
            cells = " ".join(str(c) for row in board for c in row)
            fh.write(f"{i} {start + i / fps:.3f} {cells}\n")


if __name__ == "__main__":
    main()
