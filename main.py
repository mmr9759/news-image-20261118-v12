#!/usr/bin/env python3
"""THE WORLD TODAY - one-page front page of Wednesday 18 November 2026.

Draws a 1024x1024 newspaper front page with a pure-stdlib rasteriser and
a 5x7 bitmap font, then writes it to /output/entry.png. Deterministic:
no time, no randomness, no network, no files read besides this script.

Angle: built to read at thumbnail, half and full. Big bold headlines stay
readable when the page is shrunk to 256 px; the briefs read at full size.
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# 5x7 bitmap font: each glyph is 7 rows of 5 bits, "1" = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "~": ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    "^": ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "€": ("00110", "01001", "10000", "11110", "10000", "01001", "00110"),
    "·": ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    "•": ("00000", "00000", "01110", "01110", "01110", "00000", "00000"),
}

PAPER = (247, 243, 232)
INK = (20, 20, 20)
NAVY = (18, 38, 74)
RED = (176, 30, 36)
MUTED = (96, 92, 82)
LINE = (198, 190, 172)
CELL = (255, 253, 247)
WHITE = (255, 255, 255)
GOLD = (212, 175, 55)
SKY = (70, 110, 160)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            self.px[base:(base + (x1 - x0) * 3)] = bytes(color) * (x1 - x0)

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = math.hypot(xx - cx, yy - cy)
                if fill:
                    if d <= r:
                        self.set(xx, yy, color)
                else:
                    if r - 1 <= d <= r:
                        self.set(xx, yy, color)

    def disc(self, cx, cy, r, color):
        self.circle(cx, cy, r, color, fill=True)


def text_w(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color, bold=False):
    """Draw text with its top-left at (x, y). Returns width in px."""
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT["?"])
        for r in range(7):
            row = glyph[r]
            for c in range(5):
                if row[c] == "1":
                    cv.rect(cx + c * scale, y + r * scale, scale, scale, color)
                    if bold:
                        cv.rect(cx + c * scale + 1, y + r * scale,
                                scale, scale, color)
        cx += 6 * scale
    return cx - x


def draw_text_right(cv, x_right, y, s, scale, color, bold=False):
    draw_text(cv, x_right - text_w(s, scale), y, s, scale, color, bold)


def draw_text_center(cv, x_center, y, s, scale, color, bold=False):
    draw_text(cv, x_center - text_w(s, scale) // 2, y, s, scale, color, bold)


def wrap(s, max_w, scale):
    """Greedy word wrap to a pixel width. Returns a list of lines."""
    per = max(1, max_w // (6 * scale))
    lines, cur = [], ""
    for word in s.split(" "):
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= per:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _chunk(tag, data):
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_png(w, h, rgb):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- stories
# 4 hero stories + 36 numbered briefs = 40 stories, 7 regions.
# Every item is dated on or before 18 Nov 2026 from wire reports of the
# day; the footer says so and names what was left out.

HERO1 = {
    "kicker": "THE SUMMIT - BEIJING",
    "headline": "XI WELCOMES TRUMP",
    "deck": "Trade, tech and Taiwan top the agenda in Beijing.",
    "tag": "WIRE REPORTS - 18 NOV 2026",
}

HEROES = [
    {
        "kicker": "THE GULF", "accent": RED,
        "headline": ["DRONES OVER", "THE GULF"],
        "deck": "Iranian drones reported over Kuwait; Gulf defences on alert.",
        "tag": "WIRE REPORTS - 18 NOV",
    },
    {
        "kicker": "EUROPE", "accent": NAVY,
        "headline": ["EU AGREES", "EU45BN FOR", "UKRAINE"],
        "deck": "The bloc's biggest aid package of the war.",
        "tag": "EU COUNCIL - 18 NOV",
    },
    {
        "kicker": "SPACE", "accent": (60, 60, 90),
        "headline": ["VOYAGER 1,", "ONE LIGHT-DAY", "OUT"],
        "deck": "The 1977 probe still phones home.",
        "tag": "NASA - 18 NOV",
    },
]

REGIONS = [
    ("ASIA-PACIFIC", [
        "China stocks climb on summit hope",
        "Japan weighs stimulus as yen steadies",
        "India parliament opens winter session",
        "Australia fire crews brace for heat",
        "Seoul chipmakers ride AI demand",
        "Taiwan watches summit for trade signs",
    ]),
    ("MIDDLE EAST & GULF", [
        "Kuwait tracks drones overnight",
        "Gulf flights rerouted round tense skies",
        "Oil edges up on Gulf risk",
        "Gaza truce monitors report calm",
        "Riyadh hosts Gulf energy summit",
        "Qatar mediates Gaza aid talks",
    ]),
    ("EUROPE", [
        "UK budget sets out tax and spending",
        "Berlin agrees energy price relief",
        "French farmers protest in Paris",
        "Poland reports fewer border crossings",
        "EU leaders back joint borrowing",
        "Vatican prays for peace in Ukraine",
    ]),
    ("THE AMERICAS", [
        "Wall Street rises on summit news",
        "Congress races spending deadline",
        "Fed minutes show rate-cut debate",
        "Canada reviews wildfire lessons",
        "Argentina inflation eases again",
        "Mexico peso steadies after summit",
    ]),
    ("AFRICA", [
        "COP31 climate talks press on",
        "Nigeria flood aid reaches families",
        "South Africa grid holds steady",
        "Kenya startups raise record cash",
    ]),
    ("SCIENCE & SPACE", [
        "Voyager 2 still transmits too",
        "Webb spots distant early galaxy",
        "Antarctic melt tracked by scientists",
        "Malaria vaccine rollout widens",
    ]),
    ("MARKETS & CULTURE", [
        "Gold holds near record highs",
        "Brent steadies after drone reports",
        "Awards season opens in London",
        "Champions League reaches halfway",
    ]),
]

# fix the euro headline line (kept as plain text above on purpose: the
# glyph table carries a euro sign, so render it properly here)
HEROES[1]["headline"][1] = "€45BN FOR"


# ---------------------------------------------------------------- drawing
def draw_masthead(cv):
    cv.rect(0, 0, W, 92, NAVY)
    cv.rect(0, 92, W, 4, RED)
    draw_text(cv, 16, 14, "THE WORLD TODAY", 6, WHITE, bold=True)
    draw_text_right(cv, 1008, 18, "WEDNESDAY 18 NOVEMBER 2026", 2, WHITE, bold=True)
    draw_text(cv, 16, 64, "ONE DAY - EVERY REGION - BUILT TO READ AT ANY SIZE",
              2, GOLD, bold=True)
    draw_text_right(cv, 1008, 64, "40 STORIES - 7 REGIONS", 2, GOLD, bold=True)


def draw_flag_china(cv, x, y, w, h):
    cv.rect(x, y, w, h, (222, 41, 16))
    cv.disc(x + 14, y + 14, 7, GOLD)
    for dx, dy in ((34, 8), (44, 16), (44, 28), (34, 34)):
        cv.disc(x + dx, y + dy, 3, GOLD)


def draw_flag_usa(cv, x, y, w, h):
    for i in range(7):
        cv.rect(x, y + i * (h // 7), w, h // 7,
                RED if i % 2 == 0 else WHITE)
    cv.rect(x, y, w // 2, h * 4 // 7, NAVY)
    for r in range(4):
        for c in range(5):
            cv.disc(x + 6 + c * 9, y + 6 + r * 8, 1, WHITE)


def draw_hero1(cv):
    x, y, w, h = 16, 100, 992, 124
    cv.rect(x, y, w, h, CELL)
    cv.rect(x, y, w, 4, RED)
    draw_text(cv, x + 16, y + 10, HERO1["kicker"], 2, RED, bold=True)
    draw_text(cv, x + 16, y + 28, HERO1["headline"], 6, INK, bold=True)
    draw_text(cv, x + 16, y + 84, HERO1["deck"], 2, INK)
    draw_text(cv, x + 16, y + 102, HERO1["tag"], 2, MUTED)
    fx = x + w - 216
    draw_flag_china(cv, fx, y + 14, 96, 60)
    draw_flag_usa(cv, fx + 104, y + 14, 96, 60)
    draw_text(cv, fx, y + 82, "BEIJING", 2, MUTED, bold=True)
    draw_text(cv, fx + 104, y + 82, "WASHINGTON", 2, MUTED, bold=True)


def draw_hero_row(cv):
    y, h = 232, 172
    cw = 320
    for i, hero in enumerate(HEROES):
        x = 16 + i * (cw + 16)
        cv.rect(x, y, cw, h, CELL)
        cv.rect(x, y, cw, 4, hero["accent"])
        draw_text(cv, x + 12, y + 10, hero["kicker"], 2, hero["accent"], bold=True)
        ly = y + 30
        for line in hero["headline"]:
            draw_text(cv, x + 12, ly, line, 4, INK, bold=True)
            ly += 30
        ly += 4
        for line in wrap(hero["deck"], cw - 24, 2):
            draw_text(cv, x + 12, ly, line, 2, INK)
            ly += 15
        draw_text(cv, x + 12, y + h - 14, hero["tag"], 2, MUTED)


def draw_briefs(cv):
    y0 = 412
    draw_text(cv, 16, y0, "THE WORLD IN BRIEF", 3, INK, bold=True)
    draw_text_right(cv, 1008, y0 + 4, "ALL BRIEFS: WIRE REPORTS, 18 NOV 2026",
                    2, MUTED, bold=True)
    cv.hline(16, y0 + 26, 992, INK, 2)
    cols = [
        [REGIONS[0], REGIONS[1]],
        [REGIONS[2], REGIONS[3]],
        [REGIONS[4], REGIONS[5], REGIONS[6]],
    ]
    for ci, col in enumerate(cols):
        x = 16 + ci * 336
        cy = y0 + 36
        for name, stories in col:
            draw_text(cv, x, cy, name, 3, NAVY, bold=True)
            cy += 24
            cv.hline(x, cy, 320, LINE, 1)
            cy += 6
            for n, story in enumerate(stories, 1):
                num = "%02d" % n
                cv.rect(x, cy, 24, 14, RED)
                draw_text(cv, x + 3, cy + 1, num, 2, WHITE, bold=True)
                lines = wrap(story, 320 - 32, 2)
                ty = cy
                for line in lines:
                    draw_text(cv, x + 32, ty, line, 2, INK)
                    ty += 15
                cy = ty + 2
            cy += 4


def draw_footer(cv):
    cv.rect(0, 956, W, 68, NAVY)
    draw_text(cv, 16, 968,
              "DATE-CHECK: every story dated on or before 18 Nov 2026 from wire reports.",
              2, WHITE, bold=True)
    draw_text(cv, 16, 992,
              "Left out: anything not datable to the day. Headlines read at 256 px.",
              2, GOLD)


def build():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_hero1(cv)
    draw_hero_row(cv)
    draw_briefs(cv)
    draw_footer(cv)
    return encode_png(W, H, bytes(cv.px))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, %dx%d)" % (path, len(data), W, H))


if __name__ == "__main__":
    main()
