#!/usr/bin/env python3
"""The World in One Day - Friday 20 November 2026.

Draws a one-page broadsheet that sums up the world news of Friday
20 November 2026 as a single 1024x1024 PNG: a hero panel for the day's
biggest story, fifteen drawn story panels and a regional headlines
strip.  Pure Python 3.13 standard library: its own raster canvas, its
own bitmap font and its own PNG encoder.  Deterministic - two runs
produce byte-identical output.  On any drawing failure the bundled
fallback.png is copied to the output instead.
"""

import os
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (243, 236, 219)
PAPER_DK = (232, 222, 196)
INK = (18, 22, 38)
NAVY = (22, 33, 64)
NAVY_DK = (13, 20, 42)
NAVY_LT = (38, 54, 96)
RED = (196, 38, 42)
RED_DK = (158, 28, 34)
GOLD = (233, 178, 45)
GOLD_DK = (196, 142, 30)
TEAL = (22, 128, 134)
TEAL_DK = (14, 84, 94)
SEA = (26, 96, 110)
GREEN = (46, 138, 72)
GREEN_DK = (32, 102, 54)
LEAF = (64, 166, 84)
SKY = (168, 204, 228)
SKY_DK = (120, 164, 200)
SAND = (232, 205, 150)
GREY = (118, 122, 132)
GREY_LT = (178, 182, 190)
GREY_DK = (74, 78, 88)
WHITE = (250, 248, 240)
BROWN = (146, 96, 52)
ORANGE = (240, 128, 40)
YELLOW = (250, 208, 74)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)
        self.clip = (0, 0, w, h)

    def set_clip(self, x, y, w, h):
        self.clip = (max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h))

    def reset_clip(self):
        self.clip = (0, 0, self.w, self.h)

    def set(self, x, y, c):
        cx0, cy0, cx1, cy1 = self.clip
        if cx0 <= x < cx1 and cy0 <= y < cy1:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        cx0, cy0, cx1, cy1 = self.clip
        x0 = max(x, cx0)
        y0 = max(y, cy0)
        x1 = min(x + w, cx1)
        y1 = min(y + h, cy1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        n = (x1 - x0) * 3
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + n] = row

    def rect_outline(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def circle(self, cx, cy, r, c):
        r2 = r * r
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            for xx in range(cx - r, cx + r + 1):
                dx = xx - cx
                if dx * dx + dy * dy <= r2:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, t, c):
        ro = r + t
        ro2 = ro * ro
        ri2 = r * r
        for yy in range(cy - ro, cy + ro + 1):
            dy = yy - cy
            for xx in range(cx - ro, cx + ro + 1):
                dx = xx - cx
                d2 = dx * dx + dy * dy
                if ri2 < d2 <= ro2:
                    self.set(xx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        if rx <= 0 or ry <= 0:
            return
        for yy in range(cy - ry, cy + ry + 1):
            dy = (yy - cy) / ry
            for xx in range(cx - rx, cx + rx + 1):
                dx = (xx - cx) / rx
                if dx * dx + dy * dy <= 1.0:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=2):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(0, t // 2)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            if r == 0:
                self.set(x, y, c)
            else:
                self.circle(x, y, r, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        y0 = max(min(ys), self.clip[1])
        y1 = min(max(ys), self.clip[3] - 1)
        n = len(pts)
        for yy in range(y0, y1 + 1):
            nodes = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if (ya <= yy < yb) or (yb <= yy < ya):
                    nodes.append(xa + (yy - ya) * (xb - xa) // (yb - ya))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                self.rect(nodes[i], yy, nodes[i + 1] - nodes[i] + 1, 1, c)


# ---------------------------------------------------------------- png out
def encode_png(cv):
    w, h = cv.w, cv.h
    raw = bytearray()
    prev = bytearray(w * 3)
    px = cv.px
    for y in range(h):
        row = bytes(px[y * w * 3:(y + 1) * w * 3])
        best = None
        for ftype in (0, 1, 2):
            if ftype == 0:
                data = row
            elif ftype == 1:
                data = bytearray(len(row))
                for i in range(len(row)):
                    left = row[i - 3] if i >= 3 else 0
                    data[i] = (row[i] - left) & 0xFF
                data = bytes(data)
            else:
                data = bytes((row[i] - prev[i]) & 0xFF for i in range(len(row)))
            score = sum(b if b < 128 else 256 - b for b in data[::7])
            if best is None or score < best[0]:
                best = (score, ftype, data)
        raw.append(best[1])
        raw.extend(best[2])
        prev = bytearray(row)

    def chunk(tag, data):
        out = len(data).to_bytes(4, "big") + tag + data
        return out + zlib.crc32(tag + data).to_bytes(4, "big")

    ihdr = w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 2, 0, 0, 0])
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- font
# 5x7 bitmap glyphs, rows top to bottom, '1' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "?": ("01110", "10001", "00001", "00100", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    "\u00b7": ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
}


def text_width(s, scale, tracking=1, bold=False):
    if not s:
        return 0
    adv = (5 + tracking) * scale
    w = len(s) * adv - tracking * scale
    if bold:
        w += max(1, scale // 2)
    return w


def draw_text(cv, x, y, s, scale, color, tracking=1, bold=False):
    adv = (5 + tracking) * scale
    extra = max(1, scale // 2) if bold else 0
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    cv.rect(x + gx * scale, y + gy * scale, scale, scale, color)
                    if extra:
                        cv.rect(x + gx * scale + extra, y + gy * scale,
                                scale, scale, color)
        x += adv
    return x


def draw_text_centered(cv, cx, y, s, scale, color, tracking=1, bold=False):
    w = text_width(s, scale, tracking, bold)
    return draw_text(cv, cx - w // 2, y, s, scale, color, tracking, bold)


# ---------------------------------------------------------------- hero
def draw_hero(cv, x, y, w, h):
    cv.set_clip(x, y, w, h)
    cv.rect(x, y, w, h, NAVY)
    base = y + 196  # skyline baseline / river top
    # skyline silhouette with lit windows
    widths = [64, 48, 80, 56, 72, 44, 88, 60, 52, 76, 68, 58, 84, 50, 70, 62]
    heights = [92, 130, 76, 148, 104, 168, 88, 140, 118, 158, 96, 136, 110, 150, 84, 122]
    bx = x + 6
    for bi, (bw, bh) in enumerate(zip(widths, heights)):
        if bx + bw > x + w - 4:
            break
        top = base - bh
        cv.rect(bx, top, bw, bh, NAVY_DK)
        for wy in range(top + 8, base - 10, 13):
            for wx in range(bx + 6, bx + bw - 8, 11):
                if (bi * 13 + (wx // 11) * 7 + (wy // 13) * 3) % 5 < 2:
                    cv.rect(wx, wy, 4, 5, GOLD)
        bx += bw + 4
    # smoke puffs over two rooftops
    for cx, cy, r in ((x + 250, y + 148, 15), (x + 266, y + 140, 11),
                      (x + 236, y + 142, 9), (x + 606, y + 138, 13),
                      (x + 620, y + 131, 9)):
        cv.circle(cx, cy, r, GREY)
    cv.circle(x + 254, y + 144, 8, GREY_DK)
    cv.circle(x + 610, y + 134, 6, GREY_DK)
    # river with reflection dashes
    cv.rect(x, base, w, h - 196, SEA)
    for ry, step, off in ((base + 14, 46, 0), (base + 27, 58, 22), (base + 40, 52, 8)):
        for rx in range(x + 18 + off, x + w - 30, step):
            cv.rect(rx, ry, 16, 3, TEAL)
            cv.rect(rx + 22, ry, 7, 3, GOLD_DK)
    # cable bridge
    deck_y = y + 186
    cv.rect(x + 30, deck_y, w - 60, 6, GREY_LT)
    for px in (x + 300, x + 644):
        cv.rect(px, y + 96, 9, deck_y - (y + 96) + 6, GREY_LT)
        for dx in (-160, -96, -32, 32, 96, 160):
            cv.line(px + 4, y + 100, px + 4 + dx, deck_y, GREY, 2)
    # missile trails with burst heads
    trails = [((60, 0), (170, 96)), ((250, 0), (356, 64)), ((470, 0), (540, 110)),
              ((640, 0), (716, 58)), ((920, 0), (862, 100))]
    for (sx, sy), (ex, ey) in trails:
        cv.line(x + sx, y + sy, x + ex, y + ey, GREY, 6)
        cv.line(x + sx, y + sy, x + ex, y + ey, WHITE, 2)
    for ex, ey in ((170, 96), (356, 64), (540, 110), (716, 58), (862, 100)):
        cv.circle(x + ex, y + ey, 17, ORANGE)
        cv.circle(x + ex, y + ey, 12, YELLOW)
        cv.circle(x + ex, y + ey, 6, WHITE)
    # drones
    for dx, dy in ((452, 36), (788, 30), (96, 44)):
        cv.line(x + dx - 9, y + dy - 9, x + dx + 9, y + dy + 9, GREY_LT, 3)
        cv.line(x + dx - 9, y + dy + 9, x + dx + 9, y + dy - 9, GREY_LT, 3)
        cv.circle(x + dx, y + dy, 3, RED)
    cv.reset_clip()


# ---------------------------------------------------------------- panels
def scene_peace(cv, x, y):
    cv.rect(x, y, 180, 46, SKY)
    cv.rect(x, y + 46, 180, 24, PAPER_DK)
    for fx, fc in ((10, RED), (80, NAVY), (150, GOLD)):
        cv.rect(x + fx, y + 5, 20, 13, fc)
        cv.rect(x + fx + 9, y + 18, 2, 9, INK)
    cv.ellipse(x + 90, y + 57, 42, 9, BROWN)
    cv.rect(x + 86, y + 60, 8, 7, BROWN)
    cv.poly([(x + 64, y + 25), (x + 88, y + 9), (x + 99, y + 25)], WHITE)
    cv.ellipse(x + 90, y + 27, 25, 10, WHITE)
    cv.poly([(x + 68, y + 30), (x + 54, y + 38), (x + 70, y + 36)], WHITE)
    cv.circle(x + 112, y + 21, 6, WHITE)
    cv.poly([(x + 116, y + 21), (x + 125, y + 23), (x + 116, y + 26)], GOLD)


def scene_court(cv, x, y):
    cv.rect(x, y, 180, 56, SKY)
    cv.rect(x, y + 56, 180, 14, PAPER_DK)
    cv.poly([(x + 30, y + 18), (x + 150, y + 18), (x + 90, y + 5)], WHITE)
    cv.rect(x + 28, y + 19, 124, 6, WHITE)
    for cx in (40, 68, 104, 132):
        cv.rect(x + cx, y + 27, 9, 26, WHITE)
    cv.rect(x + 26, y + 53, 128, 5, WHITE)
    cv.line(x + 90, y + 30, x + 90, y + 55, GOLD_DK, 3)
    cv.line(x + 68, y + 32, x + 112, y + 32, GOLD_DK, 3)
    cv.line(x + 68, y + 32, x + 68, y + 41, GOLD_DK, 2)
    cv.line(x + 112, y + 32, x + 112, y + 41, GOLD_DK, 2)
    cv.ellipse(x + 68, y + 43, 11, 3, GOLD)
    cv.ellipse(x + 112, y + 43, 11, 3, GOLD)
    cv.circle(x + 90, y + 27, 3, GOLD_DK)


def scene_markets(cv, x, y):
    cv.rect(x, y, 180, 70, NAVY)
    cv.circle(x + 50, y + 33, 23, TEAL)
    cv.circle(x + 42, y + 25, 7, LEAF)
    cv.circle(x + 60, y + 42, 6, LEAF)
    cv.circle(x + 38, y + 44, 5, LEAF)
    cv.circle(x + 58, y + 20, 4, LEAF)
    pts = [(16, 12), (58, 20), (90, 15), (122, 32), (158, 54)]
    for i in range(len(pts) - 1):
        cv.line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0], y + pts[i + 1][1], RED, 5)
    cv.poly([(x + 146, y + 46), (x + 168, y + 62), (x + 170, y + 42)], RED)
    for cx, cy, ch, cc in ((86, 52, 13, GREEN), (104, 57, 9, RED), (122, 50, 15, GREEN)):
        cv.line(x + cx + 4, y + cy - 3, x + cx + 4, y + cy + ch + 3, cc, 2)
        cv.rect(x + cx, y + cy, 8, ch, cc)


def scene_ipo(cv, x, y):
    cv.rect(x, y, 180, 70, SKY)
    cv.circle(x + 44, y + 20, 13, GOLD)
    cv.poly([(x + 30, y + 24), (x + 58, y + 24), (x + 65, y + 38), (x + 23, y + 38)], GOLD)
    cv.rect(x + 23, y + 38, 42, 4, GOLD_DK)
    cv.circle(x + 44, y + 45, 4, GOLD_DK)
    pts = [(14, 60), (50, 55), (84, 22), (108, 13)]
    for i in range(len(pts) - 1):
        cv.line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0], y + pts[i + 1][1], GREEN_DK, 4)
    pts2 = [(108, 13), (132, 25), (160, 49)]
    for i in range(len(pts2) - 1):
        cv.line(x + pts2[i][0], y + pts2[i][1], x + pts2[i + 1][0], y + pts2[i + 1][1], RED, 4)
    cv.poly([(x + 148, y + 42), (x + 168, y + 56), (x + 170, y + 38)], RED)
    cv.circle(x + 108, y + 13, 4, YELLOW)
    cv.ring(x + 108, y + 13, 5, 1, INK)


def scene_kerch(cv, x, y):
    cv.rect(x, y, 180, 40, SKY)
    cv.rect(x, y + 40, 180, 30, SEA)
    cv.rect(x, y + 33, 30, 10, GREY_DK)
    cv.rect(x, y + 35, 82, 5, GREY_DK)
    cv.line(x + 80, y + 38, x + 128, y + 57, GREY_DK, 7)
    cv.line(x + 128, y + 57, x + 138, y + 67, GREY_DK, 5)
    cv.rect(x + 148, y + 33, 32, 10, GREY_DK)
    cv.rect(x + 140, y + 35, 40, 5, GREY_DK)
    for sx, sy in ((108, 60), (118, 64), (128, 59), (138, 63)):
        cv.rect(x + sx, y + sy, 3, 6, WHITE)
    cv.circle(x + 113, y + 58, 2, WHITE)
    cv.circle(x + 124, y + 62, 2, WHITE)
    cv.circle(x + 134, y + 60, 2, WHITE)
    cv.line(x + 132, y + 6, x + 144, y + 18, INK, 3)
    cv.line(x + 132, y + 18, x + 144, y + 6, INK, 3)


def scene_microsoft(cv, x, y):
    cv.rect(x, y, 180, 70, NAVY_DK)
    cv.rect(x + 46, y + 7, 112, 48, NAVY_LT)
    cv.rect_outline(x + 46, y + 7, 112, 48, GREY_LT, 2)
    cv.rect(x + 52, y + 13, 100, 36, NAVY_DK)
    cv.line(x + 64, y + 19, x + 140, y + 43, RED, 6)
    cv.line(x + 140, y + 19, x + 64, y + 43, RED, 6)
    cv.rect(x + 94, y + 55, 16, 5, GREY_LT)
    cv.rect(x + 82, y + 60, 40, 4, GREY_LT)
    cv.rect(x + 8, y + 44, 27, 17, WHITE)
    cv.poly([(x + 8, y + 44), (x + 35, y + 44), (x + 21, y + 54)], GREY_LT)


def scene_hormuz(cv, x, y):
    cv.rect(x, y, 180, 42, SKY)
    cv.rect(x, y + 42, 180, 28, SEA)
    cv.poly([(x + 6, y + 50), (x + 88, y + 50), (x + 76, y + 61), (x + 18, y + 61)], GREY_DK)
    cv.rect(x + 24, y + 44, 44, 6, GREY)
    cv.rect(x + 40, y + 32, 12, 12, GREY)
    cv.line(x + 46, y + 32, x + 46, y + 24, GREY_DK, 2)
    cv.line(x + 62, y + 42, x + 80, y + 35, GREY_DK, 3)
    cv.rect(x + 108, y + 52, 66, 9, RED_DK)
    for bx in (114, 134, 154):
        cv.rect(x + bx, y + 45, 14, 7, GREY_LT)
    cv.rect(x + 162, y + 38, 10, 14, GREY_LT)
    for wx in range(8, 172, 20):
        cv.rect(x + wx, y + 66, 9, 2, (150, 210, 215))


def scene_cop31(cv, x, y):
    cv.rect(x, y, 180, 60, PAPER_DK)
    cv.rect(x, y + 60, 180, 10, GREEN_DK)
    cv.rect(x + 16, y + 22, 16, 38, GREY_DK)
    cv.rect(x + 40, y + 30, 13, 30, GREY)
    cv.rect(x + 14, y + 19, 20, 4, GREY_DK)
    cv.rect(x + 38, y + 27, 17, 4, GREY)
    cv.circle(x + 24, y + 12, 7, GREY)
    cv.circle(x + 33, y + 7, 5, GREY)
    cv.circle(x + 47, y + 20, 6, GREY)
    cv.poly([(x + 118, y + 58), (x + 148, y + 14), (x + 168, y + 10),
             (x + 167, y + 42), (x + 142, y + 62)], LEAF)
    cv.line(x + 124, y + 54, x + 160, y + 18, GREEN_DK, 2)
    cv.ring(x + 90, y + 38, 6, 3, BROWN)
    cv.line(x + 84, y + 38, x + 62, y + 38, BROWN, 2)
    cv.line(x + 96, y + 38, x + 116, y + 38, BROWN, 2)


def scene_haiti(cv, x, y):
    cv.rect(x, y, 180, 70, SEA)
    cv.ellipse(x + 66, y + 57, 54, 12, SAND)
    cv.line(x + 54, y + 56, x + 63, y + 30, BROWN, 4)
    for ex, ey in ((40, 17), (52, 11), (68, 11), (82, 17), (46, 23)):
        cv.line(x + 63, y + 29, x + ex, y + ey, GREEN_DK, 3)
    cv.circle(x + 59, y + 33, 3, BROWN)
    cv.circle(x + 67, y + 34, 3, BROWN)
    cv.poly([(x + 126, y + 13), (x + 158, y + 13), (x + 158, y + 35),
             (x + 142, y + 57), (x + 126, y + 35)], TEAL_DK)
    cv.poly([(x + 142, y + 24), (x + 147, y + 33), (x + 142, y + 42),
             (x + 137, y + 33)], GOLD)
    cv.circle(x + 142, y + 33, 2, GOLD)


def scene_ukeu(cv, x, y):
    cv.rect(x, y, 180, 70, SKY)
    cv.rect(x + 22, y + 17, 58, 38, NAVY)
    cv.circle(x + 80, y + 36, 9, NAVY)
    cv.rect_outline(x + 22, y + 17, 58, 38, INK, 2)
    cv.circle(x + 80, y + 36, 9, NAVY)
    for sx, sy in ((46, 24), (58, 29), (58, 43), (46, 48), (34, 43), (34, 29)):
        cv.circle(x + sx, y + sy, 3, GOLD)
    cv.rect(x + 96, y + 17, 60, 38, WHITE)
    cv.rect(x + 121, y + 17, 10, 38, RED)
    cv.rect(x + 96, y + 31, 60, 10, RED)
    cv.rect_outline(x + 96, y + 17, 60, 38, INK, 2)
    cv.circle(x + 96, y + 36, 9, SKY)


def scene_saudi(cv, x, y):
    cv.rect(x, y, 180, 70, NAVY)
    for bx, bh in ((6, 18), (30, 26), (58, 14), (120, 22), (146, 30), (164, 16)):
        cv.rect(x + bx, y + 70 - bh, 20, bh, NAVY_DK)
    cv.poly([(x + 74, y + 6), (x + 106, y + 6), (x + 106, y + 28),
             (x + 90, y + 48), (x + 74, y + 28)], GOLD)
    cv.poly([(x + 79, y + 11), (x + 101, y + 11), (x + 101, y + 27),
             (x + 90, y + 41), (x + 79, y + 27)], GOLD_DK)
    cv.circle(x + 90, y + 22, 4, WHITE)
    for i in range(9):
        t = i / 8
        ax = int(8 + (66 - 8) * t)
        ay = int(4 + 26 * (t * t) + 14 * t)
        cv.circle(x + ax, y + ay, 2, RED)
    for i in range(9):
        t = i / 8
        ax = int(172 - (172 - 114) * t)
        ay = int(2 + 26 * (t * t) + 16 * t)
        cv.circle(x + ax, y + ay, 2, RED)
    for sx, sy in ((70, 22), (110, 20)):
        cv.line(x + sx - 5, y + sy, x + sx + 5, y + sy, YELLOW, 2)
        cv.line(x + sx, y + sy - 5, x + sx, y + sy + 5, YELLOW, 2)


def scene_greenland(cv, x, y):
    cv.rect(x, y, 180, 70, SEA)
    cv.poly([(x + 26, y + 52), (x + 58, y + 38), (x + 108, y + 35),
             (x + 146, y + 45), (x + 150, y + 59), (x + 32, y + 61)], WHITE)
    cv.poly([(x + 108, y + 35), (x + 146, y + 45), (x + 150, y + 59),
             (x + 112, y + 56)], SKY_DK)
    cv.line(x + 86, y + 38, x + 86, y + 11, INK, 2)
    cv.rect(x + 86, y + 11, 27, 8, WHITE)
    cv.rect(x + 86, y + 19, 27, 8, RED)
    cv.circle(x + 95, y + 19, 5, RED)
    cv.rect(x + 90, y + 14, 10, 5, WHITE)
    cv.poly([(x + 128, y + 38), (x + 148, y + 38), (x + 148, y + 50),
             (x + 138, y + 60), (x + 128, y + 50)], TEAL)
    cv.rect(x + 136, y + 42, 4, 10, WHITE)
    cv.rect(x + 133, y + 45, 10, 4, WHITE)


def scene_vietnam(cv, x, y):
    cv.rect(x, y, 180, 70, PAPER_DK)
    cv.rect(x + 34, y + 6, 6, 56, BROWN)
    cv.rect(x + 34, y + 6, 54, 6, BROWN)
    cv.line(x + 84, y + 12, x + 84, y + 25, BROWN, 3)
    cv.ring(x + 84, y + 35, 9, 3, BROWN)
    cv.ring(x + 88, y + 36, 26, 6, RED)
    cv.line(x + 69, y + 17, x + 107, y + 55, RED, 6)


def scene_cyber(cv, x, y):
    cv.rect(x, y, 180, 70, NAVY)
    cv.poly([(x + 24, y + 9), (x + 62, y + 9), (x + 62, y + 33),
             (x + 43, y + 61), (x + 24, y + 33)], NAVY_LT)
    cv.rect_outline(x + 24, y + 9, 38, 24, GREY_LT, 2)
    pts = [(43, 13), (37, 25), (46, 31), (39, 43), (44, 55)]
    for i in range(len(pts) - 1):
        cv.line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0], y + pts[i + 1][1], WHITE, 2)
    cv.rect(x + 104, y + 12, 54, 52, BROWN)
    cv.rect(x + 118, y + 16, 40, 48, PAPER_DK)
    cv.poly([(x + 118, y + 16), (x + 102, y + 22), (x + 102, y + 58),
             (x + 118, y + 64)], GOLD_DK)
    cv.rect(x + 120, y + 3, 38, 11, RED)
    draw_text(cv, x + 125, y + 5, "EXIT", 1, WHITE, 1, True)


def scene_iraq(cv, x, y):
    cv.rect(x, y, 180, 56, SAND)
    cv.circle(x + 90, y + 57, 21, ORANGE)
    cv.rect(x, y + 56, 180, 14, PAPER_DK)
    cv.rect(x + 8, y + 40, 24, 16, NAVY_DK)
    cv.rect(x + 38, y + 34, 20, 22, NAVY_DK)
    cv.circle(x + 48, y + 34, 10, NAVY_DK)
    cv.rect(x + 138, y + 15, 7, 41, NAVY_DK)
    cv.circle(x + 141, y + 13, 5, NAVY_DK)
    cv.rect(x + 152, y + 38, 22, 18, NAVY_DK)
    cv.rect(x + 76, y + 29, 28, 27, NAVY_DK)
    cv.circle(x + 90, y + 41, 8, SAND)
    cv.rect(x + 82, y + 41, 16, 15, SAND)
    cv.line(x + 90, y + 29, x + 90, y + 7, INK, 2)
    cv.rect(x + 90, y + 7, 21, 4, RED)
    cv.rect(x + 90, y + 11, 21, 4, WHITE)
    cv.rect(x + 90, y + 15, 21, 4, INK)


# ---------------------------------------------------------------- page
PANELS = [
    (scene_peace, ["RIVALS SIGN", "PEACE DEAL"]),
    (scene_court, ["COURT: MYANMAR", "GENOCIDE"]),
    (scene_markets, ["AI SELL-OFF", "ROUTS MARKETS"]),
    (scene_ipo, ["RECORD IPO", "STAR SLIDES"]),
    (scene_kerch, ["KERCH BRIDGE", "SPAN DOWN"]),
    (scene_microsoft, ["MICROSOFT OUTAGE", "WORLDWIDE"]),
    (scene_hormuz, ["US BLOCKADE", "CHOKES HORMUZ"]),
    (scene_cop31, ["COP31 STALLS", "ON FOSSILS"]),
    (scene_haiti, ["HAITI RAID", "KILLS 34"]),
    (scene_ukeu, ["UK-EU RESET DEAL"]),
    (scene_saudi, ["SAUDI SHIELD", "STOPS MISSILES"]),
    (scene_greenland, ["GREENLAND", "SECURITY DEAL"]),
    (scene_vietnam, ["VIETNAM CUTS", "DEATH PENALTY"]),
    (scene_cyber, ["TRUMP FIRES", "CYBER CHIEF"]),
    (scene_iraq, ["IRAQ ENTERS", "MILITIA TOWN"]),
]

REGIONS = [
    ("AMERICAS", RED_DK, [
        "BUKELE SEEKS THIRD TERM",
        "PERU HIT BY 6.7 QUAKE",
        "COLOMBIA PROTESTS TAXES",
        "LULA SHIELDS AMAZON",
        "SHEINBAUM FLIGHT VIRAL",
        "CANADA DEAL NEEDS WORK",
    ]),
    ("EUROPE", NAVY, [
        "GUARANTEES FOR UKRAINE",
        "NL EMBASSY HIT IN KYIV",
        "HUNGARY LIFTS EU VETO",
        "FRANKFURT PLOT ARRESTS",
        "META FINED EUR 805M",
        "DENMARK EXPELS ATTACHE",
    ]),
    ("MIDDLE EAST", GOLD_DK, [
        "QESHM BLAST: DISPOSAL",
        "QATAR MEDIATES HORMUZ",
        "TRUMP DEMANDS REAL DEAL",
        "SAUDI STRIKES HODEIDAH",
    ]),
    ("AFRICA", GREEN_DK, [
        "ANGOLA IN DE BEERS DEAL",
        "BOAT CAPSIZES SENEGAL",
        "LAST EBOLA CASE OUT",
    ]),
    ("ASIA-PACIFIC", TEAL_DK, [
        "CYCLONE AKVAN TO INDIA",
        "JAPAN QUAKE INJURES 22",
        "TSMC TIGHTENS CURBS",
        "KOREA CHOLERA AFTER 10Y",
        "NICHOLLS 113 LIFTS NZ",
        "JAPAN SUB STUDY FUNDED",
    ]),
]

CX = 40                 # content left edge
CW = 944                # content width
PANEL_W = 180
PANEL_GAP = 11
SCENE_H = 70
LABEL_H = 40


def draw_panel(cv, x, y, scene_fn, label_lines):
    cv.set_clip(x, y, PANEL_W, SCENE_H)
    scene_fn(cv, x, y)
    cv.reset_clip()
    ly = y + SCENE_H
    cv.rect(x, ly, PANEL_W, LABEL_H, NAVY)
    if len(label_lines) == 1:
        draw_text_centered(cv, x + PANEL_W // 2, ly + 13, label_lines[0],
                           2, WHITE, 0, True)
    else:
        draw_text_centered(cv, x + PANEL_W // 2, ly + 5, label_lines[0],
                           2, WHITE, 0, True)
        draw_text_centered(cv, x + PANEL_W // 2, ly + 22, label_lines[1],
                           2, WHITE, 0, True)
    cv.rect_outline(x, y, PANEL_W, SCENE_H + LABEL_H, INK, 2)


def draw_page(cv):
    cv.rect(0, 0, W, H, PAPER)
    cv.rect_outline(14, 14, 996, 996, INK, 3)
    cv.rect_outline(23, 23, 978, 978, INK, 1)

    # masthead
    draw_text_centered(cv, 512, 38, "THE WORLD IN ONE DAY", 3, INK, 2, True)
    cv.rect(CX, 70, CW, 2, INK)
    cv.rect(CX, 75, CW, 1, INK)
    draw_text_centered(cv, 512, 86, "FRIDAY 20 NOVEMBER 2026", 6, INK, 1, True)
    draw_text_centered(cv, 512, 140,
                       "EVERY CONTINENT \u00b7 EVERY BIG STORY \u00b7 ONE DAY",
                       2, RED, 1, True)
    cv.rect(CX, 164, CW, 2, INK)
    cv.rect(CX, 169, CW, 1, INK)

    # hero
    draw_hero(cv, CX, 178, CW, 250)
    cv.rect(CX, 428, CW, 62, RED)
    draw_text_centered(cv, 512, 437, "RUSSIA BOMBARDS UKRAINE", 4, WHITE, 1, True)
    draw_text_centered(cv, 512, 469,
                       "400+ DRONES \u00b7 110 MISSILES \u00b7 KYIV BRIDGES AND "
                       "POWER GRID HIT \u00b7 8 DEAD",
                       2, WHITE, 1, False)
    cv.rect_outline(CX, 178, CW, 312, INK, 3)

    # story grid
    gy = 504
    for row in range(3):
        for col in range(5):
            fn, lines = PANELS[row * 5 + col]
            draw_panel(cv, CX + col * (PANEL_W + PANEL_GAP),
                       gy + row * (SCENE_H + LABEL_H + 10), fn, lines)

    # headlines strip
    sy = 868
    cv.rect(CX, 858, CW, 2, INK)
    draw_text(cv, CX, sy, "MORE OF THE DAY", 2, INK, 1, True)
    rw = text_width("REGION BY REGION", 2, 1, True)
    draw_text(cv, CX + CW - rw, sy, "REGION BY REGION", 2, RED, 1, True)
    for col, (name, color, lines) in enumerate(REGIONS):
        rx = CX + col * (PANEL_W + PANEL_GAP)
        draw_text(cv, rx, 892, name, 1, color, 1, True)
        cv.rect(rx, 903, PANEL_W, 2, color)
        for i, line in enumerate(lines):
            draw_text(cv, rx, 911 + i * 11, line, 1, INK, 1, False)


def render_png_bytes():
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    return encode_png(cv)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    try:
        data = render_png_bytes()
    except Exception:
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "fallback.png")
        with open(src, "rb") as fh:
            data = fh.read()
    with open(target, "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
