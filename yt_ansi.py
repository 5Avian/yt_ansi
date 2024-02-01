#!/usr/bin/env python

import subprocess as sp
from argparse import ArgumentParser

# generate xterm-256color lookup
LOOKUP = {}
INTENSITIES = [0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff]
for i in range(216):
    color = bytes((
        INTENSITIES[i // 6 // 6],   # red
        INTENSITIES[i // 6 % 6],    # green
        INTENSITIES[i % 6],         # blue
    ))
    LOOKUP[color] = i + 16

# returns the closest intensity to the given value
def round_intensity(val: int) -> int:
    diff: int = 256
    result: int = -1
    for intensity in INTENSITIES:
        if val - intensity in range(diff):
            diff = val - intensity
            result = intensity
        elif intensity - val in range(diff):
            diff = intensity - val
            result = intensity
    return result

# returns a string containing the ansi code for the given rgb24 color
def rgb24_to_ansi(color: bytes) -> str:
    color = bytes((
        round_intensity(color[0]),  # red
        round_intensity(color[1]),  # green
        round_intensity(color[2]),  # blue
    ))
    return "\x1b[48;5;%im" % LOOKUP[color]

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("url", type=str, default="https://www.youtube.com/watch?v=dQw4w9WgXcQ", nargs="?")
    parser.add_argument("width", type=int, default=64, nargs="?")
    parser.add_argument("height", type=int, default=16, nargs="?")
    parser.add_argument("stderr", type=bool, default=False, nargs="?")
    args = parser.parse_args()

    stderr = None if args.stderr else sp.DEVNULL
    ytdl = sp.Popen(("yt-dlp", "-o", "-", args.url), stdout=sp.PIPE, stderr=stderr)
    ffmpeg = sp.Popen(("ffmpeg", "-i", "pipe:0", "-pix_fmt", "rgb24", "-f", "rawvideo", "-vf", "scale=%i:%i" % (args.width, args.height), "pipe:1"), stdin=ytdl.stdout, stdout=sp.PIPE, stderr=stderr)

    prev_ansi = ""
    while True:
        print("\x1b[1;1H", end="") # reset cursor
        for y in range(args.height):
            for x in range(args.width):
                data = ffmpeg.stdout.read(3)
                if len(data) != 3:
                    break
                ansi = rgb24_to_ansi(data)
                if ansi != prev_ansi:
                    print(ansi, end="")
                print(" ", end="")
                prev_ansi = ansi
            print("\n", end="")
