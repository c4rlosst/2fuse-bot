"""Draw the board reader's labels on a frame, for eyeballing classifier errors."""
import sys

from PIL import Image, ImageDraw

from twofuse.vision import cell_boxes, read_board


def overlay(src: str, out: str) -> None:
    img = Image.open(src).convert("RGB")
    board, boxes = read_board(img), cell_boxes(*img.size)
    d = ImageDraw.Draw(img)
    for r in range(4):
        for c in range(4):
            x0, y0, x1, y1 = boxes[r][c]
            d.rectangle((x0, y0, x1, y1), outline=(255, 255, 255))
            d.rectangle((x0 + 4, y0 + 4, x0 + 40, y0 + 22), fill=(0, 0, 0))
            d.text((x0 + 8, y0 + 8), str(board[r][c]), fill=(255, 255, 0))
    img.crop((0, 380, img.width, 930)).save(out)


if __name__ == "__main__":
    overlay(sys.argv[1], sys.argv[2])
