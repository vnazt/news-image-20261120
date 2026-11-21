#!/usr/bin/env python3
"""The World in One Day - Friday 20 November 2026.

A single front-page image that sums up the world news of Friday
20 November 2026, drawn entirely by this program: its own PNG
encoder, its own raster canvas, its own bold bitmap typeface and
sixteen hand-built scenes (one per major story) plus a regional
headlines strip.  Pure Python 3.13 standard library, fully
deterministic: two runs produce byte-identical output.
"""

import os
import struct
import zlib
from math import isqrt, sqrt

W = 1024
H = 1024
SS = 2  # supersampling factor; the page is drawn at 2048 and boxed down

INK = (22, 28, 38)
PAPER = (247, 242, 231)
CREAM = (255, 246, 224)


def mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t + 0.5),
            int(c1[1] + (c2[1] - c1[1]) * t + 0.5),
            int(c1[2] + (c2[2] - c1[2]) * t + 0.5))


class Rng:
    """Tiny deterministic LCG so star fields and window lights are stable."""

    def __init__(self, seed):
        self.s = (seed & 0x7FFFFFFF) or 1

    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s

    def range(self, lo, hi):
        return lo + self.next() % max(1, hi - lo)

    def frac(self):
        return self.next() / 2147483648.0


# --------------------------------------------------------------------------
# Bold 7x9 bitmap typeface, drawn by hand for this page.
# --------------------------------------------------------------------------

_FONT_RAW = {
    'A': (".#####.", "##...##", "##...##", "##...##", "#######",
          "##...##", "##...##", "##...##", "##...##"),
    'B': ("######.", "##...##", "##...##", "##...##", "######.",
          "##...##", "##...##", "##...##", "######."),
    'C': (".#####.", "##...##", "##.....", "##.....", "##.....",
          "##.....", "##.....", "##...##", ".#####."),
    'D': ("######.", "##...##", "##...##", "##...##", "##...##",
          "##...##", "##...##", "##...##", "######."),
    'E': ("#######", "##.....", "##.....", "##.....", "######.",
          "##.....", "##.....", "##.....", "#######"),
    'F': ("#######", "##.....", "##.....", "##.....", "######.",
          "##.....", "##.....", "##.....", "##....."),
    'G': (".#####.", "##...##", "##.....", "##.....", "##..###",
          "##...##", "##...##", "##...##", ".#####."),
    'H': ("##...##", "##...##", "##...##", "##...##", "#######",
          "##...##", "##...##", "##...##", "##...##"),
    'I': ("#######", "...##..", "...##..", "...##..", "...##..",
          "...##..", "...##..", "...##..", "#######"),
    'J': ("#######", ".....##", ".....##", ".....##", ".....##",
          ".....##", ".....##", "##..##.", ".####.."),
    'K': ("##...##", "##..##.", "##.##..", "##.##..", "####...",
          "##.##..", "##..##.", "##..##.", "##...##"),
    'L': ("##.....", "##.....", "##.....", "##.....", "##.....",
          "##.....", "##.....", "##.....", "#######"),
    'M': ("##...##", "###.###", "##.#.##", "##.#.##", "##...##",
          "##...##", "##...##", "##...##", "##...##"),
    'N': ("##...##", "##...##", "###..##", "##.#.##", "##..###",
          "##...##", "##...##", "##...##", "##...##"),
    'O': (".#####.", "##...##", "##...##", "##...##", "##...##",
          "##...##", "##...##", "##...##", ".#####."),
    'P': ("######.", "##...##", "##...##", "##...##", "######.",
          "##.....", "##.....", "##.....", "##....."),
    'Q': (".#####.", "##...##", "##...##", "##...##", "##...##",
          "##.#.##", "##..##.", ".#####.", "....###"),
    'R': ("######.", "##...##", "##...##", "##...##", "######.",
          "##.##..", "##..##.", "##..##.", "##...##"),
    'S': (".######", "##.....", "##.....", "##.....", ".#####.",
          ".....##", ".....##", ".....##", "######."),
    'T': ("#######", "#######", "...##..", "...##..", "...##..",
          "...##..", "...##..", "...##..", "...##.."),
    'U': ("##...##", "##...##", "##...##", "##...##", "##...##",
          "##...##", "##...##", "##...##", ".#####."),
    'V': ("##...##", "##...##", "##...##", "##...##", "##...##",
          "##...##", ".##.##.", ".##.##.", "..###.."),
    'W': ("##...##", "##...##", "##...##", "##...##", "##...##",
          "##.#.##", "##.#.##", "###.###", "##...##"),
    'X': ("##...##", ".##.##.", ".##.##.", "..###..", "..###..",
          ".##.##.", ".##.##.", "##...##", "##...##"),
    'Y': ("##...##", "##...##", ".##.##.", ".##.##.", "..###..",
          "...##..", "...##..", "...##..", "...##.."),
    'Z': ("#######", "#######", ".....##", "....##.", "...##..",
          "..##...", ".##....", "##.....", "#######"),
    '0': (".#####.", "##...##", "##...##", "##..###", "##.#.##",
          "###..##", "##...##", "##...##", ".#####."),
    '1': ("..##...", ".###...", ".###...", "..##...", "..##...",
          "..##...", "..##...", "..##...", "#######"),
    '2': (".#####.", "##...##", "##...##", ".....##", "....##.",
          "...##..", "..##...", ".##....", "#######"),
    '3': (".#####.", "##...##", ".....##", "..####.", ".....##",
          ".....##", ".....##", "##...##", ".#####."),
    '4': ("....##.", "...###.", "...###.", "..##.##", "..##.##",
          "#######", ".....##", ".....##", ".....##"),
    '5': ("#######", "##.....", "##.....", "######.", ".....##",
          ".....##", ".....##", "##...##", ".#####."),
    '6': (".#####.", "##...##", "##.....", "######.", "##...##",
          "##...##", "##...##", "##...##", ".#####."),
    '7': ("#######", "#######", ".....##", "....##.", "....##.",
          "...##..", "...##..", "...##..", "...##.."),
    '8': (".#####.", "##...##", "##...##", ".#####.", "##...##",
          "##...##", "##...##", "##...##", ".#####."),
    '9': (".#####.", "##...##", "##...##", "##...##", ".######",
          ".....##", ".....##", "##...##", ".#####."),
    ' ': (".......",) * 9,
    '.': (".......", ".......", ".......", ".......", ".......",
          ".......", ".......", "..##...", "..##..."),
    ',': (".......", ".......", ".......", ".......", ".......",
          ".......", ".......", "..##...", ".##...."),
    ':': (".......", ".......", "..##...", "..##...", ".......",
          ".......", "..##...", "..##...", "......."),
    ';': (".......", ".......", "..##...", "..##...", ".......",
          ".......", "..##...", ".##....", "......."),
    '!': ("...##..", "...##..", "...##..", "...##..", "...##..",
          "...##..", ".......", "...##..", "...##.."),
    '?': (".#####.", "##...##", ".....##", "....##.", "...##..",
          "...##..", ".......", "...##..", "...##.."),
    "'": ("...##..", "...##..", ".......", ".......", ".......",
          ".......", ".......", ".......", "......."),
    '-': (".......", ".......", ".......", ".#####.", ".#####.",
          ".......", ".......", ".......", "......."),
    '+': (".......", ".......", "...##..", "...##..", ".#####.",
          "...##..", "...##..", ".......", "......."),
    '/': (".....##", ".....##", "....##.", "....##.", "...##..",
          "...##..", "..##...", "..##...", ".##...."),
    '&': (".#####.", "##...##", "##..##.", ".####..", "..##...",
          ".##.##.", "##..##.", "##...##", ".###.##"),
    '%': ("##...##", "##..##.", "....##.", "...##..", "..##...",
          "..##...", ".##....", "##..##.", "##...##"),
    '(': ("....##.", "...##..", "..##...", "..##...", "..##...",
          "..##...", "..##...", "...##..", "....##."),
    ')': (".##....", "..##...", "...##..", "...##..", "...##..",
          "...##..", "...##..", "..##...", ".##...."),
    '·': (".......", ".......", ".......", "..##...", "..##...",
          ".......", ".......", ".......", "......."),
    '"': (".##.##.", ".##.##.", ".......", ".......", ".......",
          ".......", ".......", ".......", "......."),
    '*': (".......", ".......", ".##.##.", "..###..", "#######",
          "..###..", ".##.##.", ".......", "......."),
    '=': (".......", ".......", ".#####.", ".#####.", ".......",
          ".#####.", ".#####.", ".......", "......."),
    '$': ("...##..", ".######", "##.##..", "##.##..", ".#####.",
          "..#.##.", "..#.##.", "######.", "...##.."),
    '#': (".......", ".##.##.", ".##.##.", "#######", ".##.##.",
          "#######", ".##.##.", ".##.##.", "......."),
}


def _norm_font(raw):
    out = {}
    for ch, rows in raw.items():
        fixed = []
        for r in list(rows)[:9]:
            fixed.append((r + ".......")[:7])
        while len(fixed) < 9:
            fixed.append(".......")
        out[ch] = tuple(fixed)
    return out


FONT = _norm_font(_FONT_RAW)


# --------------------------------------------------------------------------
# Raster canvas (supersampled) and PNG encoder.
# --------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, ss):
        self.ss = ss
        self.w = w * ss
        self.h = h * ss
        self.px = bytearray(self.w * self.h * 3)

    # -- low level ------------------------------------------------------
    def _span(self, y, x0, x1, c):
        if y < 0 or y >= self.h or x1 <= x0:
            return
        if x0 < 0:
            x0 = 0
        if x1 > self.w:
            x1 = self.w
        if x1 <= x0:
            return
        off = (y * self.w + x0) * 3
        self.px[off:off + (x1 - x0) * 3] = bytes(c) * (x1 - x0)

    def _ss(self, v):
        return int(round(v * self.ss))

    # -- shapes (final-page coordinates) --------------------------------
    def fill_rect(self, x, y, w, h, c):
        x0, x1 = self._ss(x), self._ss(x + w)
        y0, y1 = self._ss(y), self._ss(y + h)
        for yy in range(y0, y1):
            self._span(yy, x0, x1, c)

    def rect_outline(self, x, y, w, h, c, t=2.0):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def vgrad(self, x, y, w, h, c1, c2):
        x0, x1 = self._ss(x), self._ss(x + w)
        y0, y1 = self._ss(y), self._ss(y + h)
        span = max(1, y1 - y0 - 1)
        for yy in range(y0, y1):
            self._span(yy, x0, x1, mix(c1, c2, (yy - y0) / span))

    def circle(self, cx, cy, r, c):
        cx, cy, r = self._ss(cx), self._ss(cy), max(1, self._ss(r))
        for dy in range(-r, r + 1):
            hw = isqrt(r * r - dy * dy)
            self._span(cy + dy, cx - hw, cx + hw + 1, c)

    def ellipse(self, cx, cy, rx, ry, c):
        cx, cy = self._ss(cx), self._ss(cy)
        rx, ry = max(1, self._ss(rx)), max(1, self._ss(ry))
        for dy in range(-ry, ry + 1):
            hw = int(rx * sqrt(max(0.0, 1.0 - (dy / ry) ** 2)))
            self._span(cy + dy, cx - hw, cx + hw + 1, c)

    def ring(self, cx, cy, r, t, c):
        cx, cy = self._ss(cx), self._ss(cy)
        ro = max(1, self._ss(r))
        ri = max(0, self._ss(r - t))
        for dy in range(-ro, ro + 1):
            hwo = isqrt(ro * ro - dy * dy)
            if abs(dy) < ri:
                hwi = isqrt(ri * ri - dy * dy)
                self._span(cy + dy, cx - hwo, cx - hwi, c)
                self._span(cy + dy, cx + hwi, cx + hwo + 1, c)
            else:
                self._span(cy + dy, cx - hwo, cx + hwo + 1, c)

    def ellipse_ring(self, cx, cy, rx, ry, t, c):
        cx, cy = self._ss(cx), self._ss(cy)
        rxo, ryo = max(1, self._ss(rx)), max(1, self._ss(ry))
        rxi, ryi = max(0, self._ss(rx - t)), max(0, self._ss(ry - t))
        for dy in range(-ryo, ryo + 1):
            hwo = int(rxo * sqrt(max(0.0, 1.0 - (dy / ryo) ** 2)))
            if ryi > 0 and abs(dy) < ryi:
                hwi = int(rxi * sqrt(max(0.0, 1.0 - (dy / ryi) ** 2)))
                self._span(cy + dy, cx - hwo, cx - hwi, c)
                self._span(cy + dy, cx + hwi, cx + hwo + 1, c)
            else:
                self._span(cy + dy, cx - hwo, cx + hwo + 1, c)

    def line(self, x0, y0, x1, y1, c, wdt=2.0, dash=None):
        dx, dy = x1 - x0, y1 - y0
        dist = sqrt(dx * dx + dy * dy)
        step = max(0.7, wdt * 0.38)
        n = int(dist / step) + 1
        for i in range(n + 1):
            if dash is not None:
                on, off = dash
                if (i % (on + off)) >= on:
                    continue
            t = i / n if n else 0.0
            self.circle(x0 + dx * t, y0 + dy * t, wdt / 2.0, c)

    def poly(self, pts, c):
        sp = [(self._ss(px), self._ss(py)) for px, py in pts]
        ys = [p[1] for p in sp]
        y0, y1 = max(0, min(ys)), min(self.h - 1, max(ys))
        n = len(sp)
        for yy in range(y0, y1 + 1):
            yc = yy + 0.5
            xs = []
            for i in range(n):
                xa, ya = sp[i]
                xb, yb = sp[(i + 1) % n]
                if (ya <= yc < yb) or (yb <= yc < ya):
                    xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self._span(yy, int(xs[i]), int(xs[i + 1]) + 1, c)

    # -- text -------------------------------------------------------------
    def text_w(self, s, size, condense=0.92, tracking=1.0):
        if not s:
            return 0.0
        ux = size / 9.0 * condense
        adv = 8.3 * ux * tracking
        return adv * len(s) - (adv - 7 * ux)

    def text(self, x, y, s, size, color, align='l', condense=0.92,
             tracking=1.0):
        s = s.upper()
        uy = size / 9.0
        ux = uy * condense
        adv = 8.3 * ux * tracking
        wtot = self.text_w(s, size, condense, tracking)
        if align == 'c':
            x -= wtot / 2.0
        elif align == 'r':
            x -= wtot
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[' '])
            for r in range(9):
                row = g[r]
                for ci in range(7):
                    if row[ci] == '#':
                        self.fill_rect(cx + ci * ux, y + r * uy,
                                       ux * 1.09, uy * 1.09, color)
            cx += adv
        return wtot

    def fit_size(self, s, maxw, maxsize, condense=0.92, tracking=1.0):
        w1 = self.text_w(s, 1.0, condense, tracking)
        if w1 <= 0:
            return maxsize
        return min(maxsize, maxw / w1)

    # -- output -----------------------------------------------------------
    def downscale(self):
        """Box-average the supersampled buffer down to final size."""
        ss = self.ss
        w = self.w // ss
        h = self.h // ss
        src = self.px
        sw3 = self.w * 3
        out = bytearray(w * h * 3)

        def avg2(b):
            return bytes([(a + b) >> 1
                          for a, b in zip(b[0::2], b[1::2])])

        for oy in range(h):
            rows = []
            for k in range(ss):
                base = (oy * ss + k) * sw3
                chans = []
                for c in range(3):
                    chans.append(avg2(bytes(src[base + c:base + sw3:3])))
                rows.append(chans)
            orow = oy * w * 3
            for c in range(3):
                if ss == 2:
                    merged = bytes([(a + b) >> 1 for a, b in
                                    zip(rows[0][c], rows[1][c])])
                else:
                    merged = rows[0][c]
                out[orow + c:orow + w * 3:3] = merged
        return bytes(out), w, h


def _png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def _filter_rows(raw, w, h, bpp):
    stride = w * bpp
    out = bytearray()
    prev = bytes(stride)
    for yy in range(h):
        row = raw[yy * stride:(yy + 1) * stride]
        cands = [b"\x00" + row]
        sub = bytearray(stride)
        for i in range(stride):
            left = row[i - bpp] if i >= bpp else 0
            sub[i] = (row[i] - left) & 0xFF
        cands.append(b"\x01" + bytes(sub))
        up = bytearray(stride)
        for i in range(stride):
            up[i] = (row[i] - prev[i]) & 0xFF
        cands.append(b"\x02" + bytes(up))

        def sad(cand):
            return sum(b if b < 128 else 256 - b for b in cand[1:])

        out += min(cands, key=sad)
        prev = row
    return bytes(out)


def encode_png(rgb, w, h):
    """RGB PNG; falls back to a fixed 256-colour palette if oversized."""
    data = _filter_rows(rgb, w, h, 3)
    png = (b"\x89PNG\r\n\x1a\n" +
           _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
           _png_chunk(b"IDAT", zlib.compress(data, 9)) +
           _png_chunk(b"IEND", b""))
    if len(png) <= 1048576:
        return png
    # Deterministic uniform 3-3-2 palette quantisation.
    idx = bytearray(w * h)
    for i in range(w * h):
        r, g, b = rgb[3 * i], rgb[3 * i + 1], rgb[3 * i + 2]
        idx[i] = ((r >> 5) << 5) | ((g >> 5) << 2) | (b >> 6)
    pal = bytearray()
    for i in range(256):
        pal += bytes((((i >> 5) & 7) * 255 // 7,
                      ((i >> 2) & 7) * 255 // 7,
                      (i & 3) * 255 // 3))
    data = _filter_rows(bytes(idx), w, h, 1)
    return (b"\x89PNG\r\n\x1a\n" +
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0)) +
            _png_chunk(b"PLTE", bytes(pal)) +
            _png_chunk(b"IDAT", zlib.compress(data, 9)) +
            _png_chunk(b"IEND", b""))


# --------------------------------------------------------------------------
# Scene building blocks.
# --------------------------------------------------------------------------

from math import cos, sin, pi


def cloud(cv, cx, cy, s, c):
    cv.circle(cx, cy, s, c)
    cv.circle(cx - s * 0.95, cy + s * 0.18, s * 0.68, c)
    cv.circle(cx + s * 0.95, cy + s * 0.18, s * 0.74, c)
    cv.circle(cx + s * 0.25, cy - s * 0.38, s * 0.62, c)


def sparkle(cv, cx, cy, s, c):
    cv.line(cx - s, cy, cx + s, cy, c, 1.8)
    cv.line(cx, cy - s, cx, cy + s, c, 1.8)
    cv.circle(cx, cy, s * 0.22, c)


def star5(cv, cx, cy, r, c):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        a = -pi / 2 + i * pi / 5
        pts.append((cx + cos(a) * rr, cy + sin(a) * rr))
    cv.poly(pts, c)


def burst(cv, cx, cy, r):
    for k in range(8):
        a = k * pi / 4 + 0.39
        cv.line(cx, cy, cx + cos(a) * r * 1.3, cy + sin(a) * r * 1.3,
                (250, 170, 70), max(1.4, r * 0.14))
    cv.circle(cx, cy, r, (216, 64, 32))
    cv.circle(cx, cy, r * 0.76, (242, 122, 38))
    cv.circle(cx, cy, r * 0.54, (252, 182, 62))
    cv.circle(cx, cy, r * 0.33, (255, 232, 166))
    cv.circle(cx, cy, r * 0.17, (255, 252, 240))


def drone(cv, cx, cy, s, c):
    cv.line(cx - 7 * s, cy - 5 * s, cx + 7 * s, cy + 5 * s, c, 2.2 * s)
    cv.line(cx + 7 * s, cy - 5 * s, cx - 7 * s, cy + 5 * s, c, 2.2 * s)
    for dx, dy in ((-7, -5), (7, -5), (-7, 5), (7, 5)):
        cv.circle(cx + dx * s, cy + dy * s, 2.6 * s, c)
    cv.circle(cx, cy, 3 * s, c)
    cv.circle(cx, cy, 1.2 * s, (255, 70, 60))


def shield(cv, cx, top, w, h, c):
    hw = w / 2.0
    cv.poly([(cx - hw, top), (cx + hw, top), (cx + hw, top + h * 0.42),
             (cx + hw * 0.62, top + h * 0.78), (cx, top + h),
             (cx - hw * 0.62, top + h * 0.78), (cx - hw, top + h * 0.42)], c)


def plume(cv, cx, cy):
    blobs = ((0, 0, 15, (96, 104, 120)), (-13, 13, 12, (78, 86, 102)),
             (-27, 24, 10, (112, 120, 136)), (5, 19, 11, (86, 94, 110)),
             (-8, 33, 9, (104, 112, 128)), (-20, 40, 8, (70, 78, 94)))
    for dx, dy, r, c in blobs:
        cv.circle(cx + dx, cy - dy, r, c)


# --------------------------------------------------------------------------
# HERO scene - the barrage over Kyiv (box given by caller).
# --------------------------------------------------------------------------

def sc_hero(cv, x, y, w, h):
    cv.vgrad(x, y, w, h, (7, 11, 36), (30, 56, 92))
    rng = Rng(7)
    for _ in range(110):
        sx = x + rng.frac() * w
        sy = y + rng.frac() * h * 0.5
        col = (214, 224, 250) if rng.frac() < 0.7 else (255, 240, 200)
        cv.circle(sx, sy, 0.8 + rng.frac() * 0.9, col)
    # moon crescent
    cv.circle(x + w - 70, y + 34, 15, (233, 237, 245))
    cv.circle(x + w - 78, y + 29, 13, (11, 19, 45))
    # faint night clouds drifting over the city
    cloud(cv, x + 180, y + 26, 16, (16, 24, 46))
    cloud(cv, x + 620, y + 18, 13, (14, 22, 42))
    cloud(cv, x + 880, y + 52, 12, (16, 24, 46))
    cloud(cv, x + 420, y + 40, 11, (15, 23, 44))
    # searchlight beams
    river_top = y + h - 58
    cv.poly([(x + 120, river_top), (x + 330, y + 6), (x + 386, y + 6),
             (x + 210, river_top)], (58, 78, 112))
    cv.poly([(x + w - 140, river_top), (x + w - 330, y + 4),
             (x + w - 282, y + 4), (x + w - 60, river_top)], (52, 70, 104))
    # fire-glow on the horizon behind the skyline
    cv.ellipse(x + 205, river_top - 4, 95, 15, (96, 44, 26))
    cv.ellipse(x + 550, river_top - 3, 80, 13, (88, 40, 24))
    cv.ellipse(x + 840, river_top - 5, 90, 14, (96, 44, 26))
    # two skyline layers with lit windows
    for seed, col, dark, lit_p in ((11, (15, 23, 43), (26, 38, 62), 0.42),
                                   (29, (9, 14, 27), (16, 24, 40), 0.16)):
        rng = Rng(seed)
        bx = x + 4
        while bx < x + w - 12:
            bw = rng.range(34, 88)
            bh = rng.range(28, 92)
            cv.fill_rect(bx, river_top - bh, bw, bh, col)
            wy = river_top - bh + 5
            while wy < river_top - 5:
                wx = bx + 4
                while wx < bx + bw - 5:
                    if rng.frac() < lit_p:
                        cv.fill_rect(wx, wy, 3.4, 4.4, (255, 196, 92))
                    else:
                        cv.fill_rect(wx, wy, 3.4, 4.4, dark)
                    wx += 9
                wy += 8
            bx += bw + rng.range(2, 10)
    # the Dnipro
    cv.vgrad(x, river_top, w, 58, (9, 28, 54), (19, 56, 94))
    rng = Rng(31)
    for _ in range(46):
        rx = x + rng.frac() * w
        ry = river_top + 6 + rng.frac() * 44
        ln = 8 + rng.frac() * 22
        col = (255, 178, 96) if rng.frac() < 0.3 else (96, 138, 178)
        cv.fill_rect(rx, ry, ln, 1.6, col)
    # bridge: pylons, deck, cables, lights
    deck_y = river_top - 8
    pylons = (x + w * 0.31, x + w * 0.66)
    for px in pylons:
        cv.fill_rect(px - 5, deck_y - 58, 10, 66, (22, 32, 52))
        cv.circle(px, deck_y - 60, 2.4, (255, 214, 130))
    cv.fill_rect(x + 34, deck_y, w - 68, 5.5, (34, 46, 68))
    cv.fill_rect(x + 34, deck_y, w - 68, 1.8, (96, 118, 148))
    for px in pylons:
        for dx in (-150, -100, -55, -20, 20, 55, 100, 150):
            cv.line(px, deck_y - 56, px + dx, deck_y, (104, 126, 158), 1.3)
    lx = x + 52
    while lx < x + w - 40:
        cv.circle(lx, deck_y - 3, 1.7, (255, 210, 120))
        lx += 46
    # smoke, trails, bursts, drones
    plume(cv, x + 205, deck_y - 6)
    plume(cv, x + 548, deck_y - 2)
    plume(cv, x + 838, deck_y - 8)
    trails = ((90, -4, 208, deck_y - 10), (330, -4, 452, 64),
              (520, -4, 550, deck_y - 4), (690, -4, 756, 52),
              (930, -4, 840, deck_y - 12), (40, 44, 150, 120),
              (880, 30, 800, 96), (240, -4, 300, 88))
    for sx, sy, tx, ty in trails:
        cv.line(x + sx, y + sy, x + tx, y + ty, (110, 128, 158), 6.5)
        cv.line(x + sx, y + sy, x + tx, y + ty, (168, 184, 208), 3.4)
        cv.line(x + sx, y + sy, x + tx, y + ty, (232, 238, 250), 1.5)
    burst(cv, x + 208, deck_y - 12, 17)
    burst(cv, x + 452, y + 64, 13)
    burst(cv, x + 550, deck_y - 6, 15)
    burst(cv, x + 756, y + 52, 12)
    burst(cv, x + 840, deck_y - 14, 16)
    burst(cv, x + 300, y + 88, 10)
    drone(cv, x + 250, y + 52, 1.6, (10, 14, 24))
    drone(cv, x + 700, y + 30, 1.4, (10, 14, 24))
    drone(cv, x + 120, y + 96, 1.2, (10, 14, 24))


# --------------------------------------------------------------------------
# Panel scenes.  Each fills the box (x, y, 182, 79).
# --------------------------------------------------------------------------

def sc_peace(cv, x, y):
    cv.vgrad(x, y, 182, 79, (172, 216, 224), (240, 246, 236))
    for fx, fc in ((28, (198, 40, 44)), (80, (34, 82, 158)),
                   (132, (198, 40, 44))):
        cv.fill_rect(x + fx + 14, y + 4, 2.4, 40, (90, 74, 60))
        cv.fill_rect(x + fx + 16, y + 5, 30, 14, fc)
        cv.fill_rect(x + fx + 16, y + 5, 30, 3, mix(fc, (255, 255, 255), 0.25))
    star5(cv, x + 59, y + 12, 5, (250, 200, 70))
    for dx in (-6, 0, 6):
        cv.circle(x + 111 + dx, y + 9, 1.8, (240, 244, 250))
        cv.circle(x + 111 + dx, y + 15, 1.8, (240, 244, 250))
    cv.ring(x + 163, y + 12, 4.6, 1.8, (250, 200, 70))
    # chairs
    for cxh, cc in ((44, (176, 32, 40)), (78, (30, 70, 150)),
                    (112, (206, 158, 44))):
        cv.fill_rect(x + cxh, y + 33, 26, 19, cc)
        cv.ellipse(x + cxh + 13, y + 33, 13, 5, cc)
    # table
    cv.poly([(x + 82, y + 60), (x + 100, y + 60), (x + 105, y + 76),
             (x + 77, y + 76)], (96, 66, 40))
    cv.ellipse(x + 91, y + 60, 53, 13, (110, 76, 46))
    cv.ellipse(x + 91, y + 57, 53, 13, (150, 108, 70))
    cv.ellipse(x + 91, y + 56, 46, 10, (164, 122, 80))
    # document and cups on the table
    cv.fill_rect(x + 80, y + 50, 22, 9, (250, 250, 246))
    cv.line(x + 83, y + 53, x + 99, y + 53, (150, 150, 150), 1.2)
    cv.line(x + 83, y + 56, x + 97, y + 56, (150, 150, 150), 1.2)
    cv.fill_rect(x + 58, y + 52, 5, 4, (240, 240, 240))
    cv.fill_rect(x + 118, y + 52, 5, 4, (240, 240, 240))
    # dove above
    cv.poly([(x + 102, y + 24), (x + 116, y + 19), (x + 113, y + 28)],
            (236, 236, 232))
    cv.poly([(x + 84, y + 21), (x + 70, y + 10), (x + 76, y + 24)],
            (250, 250, 248))
    cv.ellipse(x + 91, y + 23, 13, 7, (250, 250, 248))
    cv.circle(x + 79, y + 19, 4.2, (250, 250, 248))
    cv.poly([(x + 75, y + 18), (x + 69, y + 20), (x + 75, y + 22)],
            (255, 160, 60))
    cv.line(x + 70, y + 21, x + 62, y + 27, (70, 150, 80), 1.8)
    cv.ellipse(x + 64, y + 25, 3.4, 1.8, (70, 160, 84))
    cv.ellipse(x + 68, y + 28, 3.0, 1.6, (70, 160, 84))


def sc_court(cv, x, y):
    cv.vgrad(x, y, 182, 79, (158, 196, 228), (233, 241, 247))
    cv.circle(x + 162, y + 10, 15, (250, 226, 150))
    cv.circle(x + 162, y + 10, 10, (252, 238, 186))
    cv.fill_rect(x, y + 66, 182, 13, (198, 188, 164))
    for i, sw_ in enumerate((118, 132, 146)):
        cv.fill_rect(x + 91 - sw_ / 2, y + 60 + i * 3.2, sw_, 3.2,
                     (172 - i * 9, 172 - i * 9, 180 - i * 9))
    cv.fill_rect(x + 37, y + 26, 108, 34, (204, 206, 214))
    for i in range(5):
        cx_ = x + 45 + i * 23
        cv.fill_rect(cx_, y + 27, 10, 32, (241, 242, 246))
        cv.fill_rect(cx_ + 7, y + 27, 3, 32, (196, 198, 208))
        cv.fill_rect(cx_ - 1, y + 25, 12, 3, (228, 229, 235))
        cv.fill_rect(cx_ - 1, y + 57, 12, 3, (228, 229, 235))
    cv.fill_rect(x + 33, y + 20, 116, 6, (233, 234, 239))
    cv.poly([(x + 37, y + 20), (x + 145, y + 20), (x + 91, y + 7)],
            (221, 222, 229))
    cv.circle(x + 91, y + 16, 3.2, (206, 164, 52))
    # scales of justice standing on the steps
    gold, gold_d = (216, 174, 64), (172, 134, 42)
    cv.line(x + 84, y + 59, x + 98, y + 59, gold_d, 3)
    cv.line(x + 91, y + 59, x + 91, y + 33, gold_d, 2.6)
    cv.line(x + 68, y + 33, x + 114, y + 33, gold_d, 2.6)
    cv.circle(x + 91, y + 33, 2.4, gold)
    for px in (68, 114):
        cv.line(x + px, y + 33, x + px - 6, y + 43, gold_d, 1.2)
        cv.line(x + px, y + 33, x + px + 6, y + 43, gold_d, 1.2)
        cv.ellipse(x + px, y + 44, 8.5, 2.8, gold)
        cv.ellipse(x + px, y + 43, 8.5, 2.2, (238, 204, 110))
    for bx in (16, 166):
        cv.circle(x + bx, y + 62, 6.5, (110, 164, 88))
        cv.circle(x + bx - 5, y + 65, 4.5, (94, 148, 78))
        cv.circle(x + bx + 5, y + 65, 4.5, (94, 148, 78))


def sc_markets(cv, x, y):
    cv.vgrad(x, y, 182, 79, (10, 16, 34), (22, 34, 58))
    for gx in range(0, 183, 18):
        cv.line(x + gx, y, x + gx, y + 79, (34, 50, 82), 1)
    for gy in range(0, 80, 16):
        cv.line(x, y + gy, x + 182, y + gy, (34, 50, 82), 1)
    cx_, cy_, r = x + 52, y + 40, 27
    cv.circle(cx_, cy_, r + 2.5, (18, 44, 78))
    cv.circle(cx_, cy_, r, (26, 78, 132))
    for bx, by, br in ((44, 28, 7), (52, 24, 5), (38, 36, 5), (58, 40, 8),
                       (50, 50, 6), (63, 30, 4), (42, 56, 4), (66, 50, 5)):
        cv.circle(x + bx, y + by, br, (44, 148, 88))
    cv.ellipse_ring(cx_, cy_, 12, 27, 1.2, (70, 130, 185))
    cv.ellipse_ring(cx_, cy_, 22, 27, 1.2, (70, 130, 185))
    cv.ring(cx_, cy_, r, 1.6, (86, 148, 205))
    pts = [(84, 14), (102, 22), (114, 17), (128, 30), (140, 26),
           (156, 44), (172, 58)]
    for wd, col in ((9, (110, 26, 34)), (5, (232, 48, 52))):
        for a, b in zip(pts, pts[1:]):
            cv.line(x + a[0], y + a[1], x + b[0], y + b[1], col, wd)
    cv.poly([(x + 172, y + 58), (x + 160, y + 56), (x + 168, y + 46)],
            (240, 70, 70))
    for i, (chh, cg) in enumerate(((10, (232, 48, 52)), (7, (64, 200, 110)),
                                   (12, (232, 48, 52)), (8, (232, 48, 52)))):
        cx2 = x + 118 + i * 15
        cv.fill_rect(cx2, y + 74 - chh, 8, chh, cg)
        cv.line(cx2 + 4, y + 71 - chh, cx2 + 4, y + 76, cg, 1.4)


def sc_ipo(cv, x, y):
    cv.vgrad(x, y, 182, 79, (40, 34, 88), (96, 66, 148))
    rng = Rng(5)
    for _ in range(14):
        cv.circle(x + rng.range(4, 178), y + rng.range(3, 40), 1.1,
                  (200, 190, 240))
    cv.fill_rect(x + 14, y + 12, 56, 5, (122, 84, 50))
    cv.fill_rect(x + 17, y + 17, 5, 30, (106, 72, 44))
    cv.fill_rect(x + 62, y + 17, 5, 30, (106, 72, 44))
    cv.fill_rect(x + 12, y + 47, 60, 4, (106, 72, 44))
    cv.circle(x + 42, y + 26, 13, (238, 186, 74))
    cv.poly([(x + 29, y + 26), (x + 55, y + 26), (x + 60, y + 40),
             (x + 24, y + 40)], (238, 186, 74))
    cv.poly([(x + 29, y + 26), (x + 38, y + 26), (x + 34, y + 40),
             (x + 24, y + 40)], (250, 208, 116))
    cv.fill_rect(x + 23, y + 40, 38, 3.4, (206, 152, 52))
    cv.circle(x + 42, y + 46, 3.4, (150, 108, 40))
    cv.line(x + 86, y + 68, x + 176, y + 68, (205, 205, 225), 1.6)
    cv.line(x + 86, y + 68, x + 86, y + 10, (205, 205, 225), 1.6)
    up = [(88, 64), (102, 56), (116, 38), (128, 20)]
    for a, b in zip(up, up[1:]):
        cv.line(x + a[0], y + a[1], x + b[0], y + b[1], (70, 216, 124), 4.6)
    sparkle(cv, x + 130, y + 16, 6, (255, 240, 170))
    sparkle(cv, x + 118, y + 10, 4, (255, 255, 255))
    sparkle(cv, x + 142, y + 24, 4, (255, 240, 170))
    dn = [(128, 20), (142, 32), (156, 48), (172, 62)]
    for a, b in zip(dn, dn[1:]):
        cv.line(x + a[0], y + a[1], x + b[0], y + b[1], (240, 74, 70), 4.6)
    cv.poly([(x + 172, y + 62), (x + 161, y + 60), (x + 169, y + 50)],
            (244, 96, 92))
    for i in range(9):
        cv.fill_rect(x + 88 + i * 10, y + 72, 6, 3,
                     (240, 200, 90) if i % 2 else (120, 200, 150))


def sc_kerch(cv, x, y):
    cv.vgrad(x, y, 182, 44, (168, 204, 226), (236, 243, 245))
    cv.vgrad(x, y + 44, 182, 35, (34, 112, 142), (58, 152, 178))
    cv.circle(x + 16, y + 12, 7, (252, 226, 140))
    cloud(cv, x + 34, y + 10, 6, (250, 252, 253))
    cloud(cv, x + 148, y + 8, 5, (244, 248, 250))
    cv.fill_rect(x, y + 40, 182, 3, (140, 160, 165))
    cv.fill_rect(x + 2, y + 38, 100, 4.4, (92, 100, 112))
    cv.fill_rect(x + 2, y + 36.6, 100, 1.6, (170, 180, 190))
    for px in (26, 66):
        cv.fill_rect(x + px, y + 40, 5, 16, (80, 88, 100))
    cv.line(x + 102, y + 40, x + 140, y + 56, (84, 92, 104), 6.5)
    cv.line(x + 102, y + 38.6, x + 140, y + 54.6, (150, 160, 172), 1.8)
    cv.fill_rect(x + 152, y + 40, 28, 4.4, (92, 100, 112))
    cv.fill_rect(x + 166, y + 42, 5, 13, (80, 88, 100))
    cv.line(x + 146, y + 58, x + 160, y + 50, (84, 92, 104), 5)
    cv.line(x + 148, y + 60, x + 158, y + 67, (84, 92, 104), 3.6)
    for sx_, sr in ((126, 5.5), (140, 4.4), (114, 3.8), (152, 3.2)):
        cv.circle(x + sx_, y + 63, sr, (240, 248, 250))
        cv.circle(x + sx_ - sr * 0.7, y + 65, sr * 0.62, (226, 242, 248))
        cv.circle(x + sx_ + sr * 0.7, y + 65, sr * 0.62, (226, 242, 248))
    cv.ellipse(x + 133, y + 66, 26, 3.4, (214, 238, 246))
    for wx, wy in ((20, 66), (52, 70), (160, 70), (88, 72), (30, 74)):
        cv.line(x + wx, y + wy, x + wx + 12, y + wy, (200, 230, 240), 1.6)
    cv.line(x + 108, y + 10, x + 138, y + 16, (90, 100, 110), 1.4, dash=(3, 3))
    drone(cv, x + 146, y + 18, 1.0, (30, 38, 50))


def sc_microsoft(cv, x, y):
    cv.vgrad(x, y, 182, 79, (26, 33, 48), (44, 56, 76))
    cv.fill_rect(x + 8, y + 8, 10, 10, (250, 214, 96))
    cv.fill_rect(x + 164, y + 6, 10, 10, (244, 156, 168))
    cv.fill_rect(x + 150, y + 20, 8, 8, (150, 220, 170))
    cv.fill_rect(x, y + 64, 182, 15, (16, 21, 31))
    cv.fill_rect(x + 36, y + 8, 110, 52, (12, 17, 25))
    cv.fill_rect(x + 40, y + 12, 102, 44, (32, 48, 72))
    cv.fill_rect(x + 50, y + 22, 34, 23, (214, 224, 238))
    cv.line(x + 50, y + 22, x + 67, y + 35, (90, 110, 140), 2)
    cv.line(x + 84, y + 22, x + 67, y + 35, (90, 110, 140), 2)
    cv.fill_rect(x + 96, y + 22, 30, 19, (96, 168, 226))
    cv.poly([(x + 102, y + 41), (x + 112, y + 41), (x + 103, y + 49)],
            (96, 168, 226))
    for dx in (104, 111, 118):
        cv.circle(x + dx, y + 31, 2, (230, 244, 252))
    cv.line(x + 44, y + 14, x + 138, y + 54, (148, 22, 30), 8.5)
    cv.line(x + 138, y + 14, x + 44, y + 54, (148, 22, 30), 8.5)
    cv.line(x + 44, y + 14, x + 138, y + 54, (228, 46, 50), 5.5)
    cv.line(x + 138, y + 14, x + 44, y + 54, (228, 46, 50), 5.5)
    cv.fill_rect(x + 86, y + 60, 10, 6, (10, 14, 20))
    cv.fill_rect(x + 72, y + 66, 38, 4, (10, 14, 20))
    cv.fill_rect(x + 156, y + 56, 9, 9, (226, 90, 80))
    cv.ring(x + 168, y + 60, 3.4, 1.6, (226, 90, 80))


def tanker(cv, cx, cy, s):
    cv.poly([(cx - 26 * s, cy - 4 * s), (cx + 26 * s, cy - 4 * s),
             (cx + 20 * s, cy + 4 * s), (cx - 20 * s, cy + 4 * s)],
            (38, 46, 58))
    cv.fill_rect(cx - 16 * s, cy - 9 * s, 30 * s, 5 * s, (52, 62, 74))
    cv.fill_rect(cx + 12 * s, cy - 13 * s, 6 * s, 9 * s, (66, 76, 90))
    cv.fill_rect(cx - 20 * s, cy - 12 * s, 8 * s, 3 * s, (150, 70, 58))


def warship(cv, cx, cy, s):
    cv.poly([(cx - 34 * s, cy), (cx + 34 * s, cy), (cx + 26 * s, cy + 9 * s),
             (cx - 27 * s, cy + 9 * s)], (98, 108, 122))
    cv.fill_rect(cx - 24 * s, cy - 6 * s, 46 * s, 6 * s, (122, 133, 148))
    cv.fill_rect(cx - 8 * s, cy - 14 * s, 18 * s, 8 * s, (134, 145, 160))
    cv.fill_rect(cx - 4 * s, cy - 19 * s, 10 * s, 5 * s, (146, 157, 172))
    cv.line(cx + 16 * s, cy - 6 * s, cx + 30 * s, cy - 12 * s,
            (70, 78, 90), 2.4 * s)
    cv.line(cx - 18 * s, cy - 6 * s, cx - 18 * s, cy - 20 * s,
            (70, 78, 90), 1.8 * s)
    cv.fill_rect(cx - 18 * s, cy - 20 * s, 9 * s, 3.4 * s, (226, 60, 54))
    cv.line(cx - 34 * s, cy + 8 * s, cx - 48 * s, cy + 12 * s,
            (200, 228, 240), 1.6 * s)
    cv.line(cx + 34 * s, cy + 8 * s, cx + 46 * s, cy + 12 * s,
            (200, 228, 240), 1.6 * s)


def sc_hormuz(cv, x, y):
    cv.vgrad(x, y, 182, 40, (238, 158, 84), (250, 216, 156))
    cv.vgrad(x, y + 40, 182, 39, (30, 86, 122), (44, 124, 164))
    cv.circle(x + 148, y + 30, 13, (255, 232, 170))
    cv.circle(x + 148, y + 30, 9, (255, 242, 200))
    cv.poly([(x, y + 30), (x + 54, y + 32), (x + 34, y + 50), (x, y + 54)],
            (156, 120, 80))
    cv.poly([(x, y + 30), (x + 54, y + 32), (x + 44, y + 40), (x, y + 40)],
            (178, 142, 96))
    cv.poly([(x + 182, y + 32), (x + 128, y + 34), (x + 150, y + 52),
             (x + 182, y + 56)], (156, 120, 80))
    cv.poly([(x + 182, y + 32), (x + 128, y + 34), (x + 140, y + 42),
             (x + 182, y + 42)], (178, 142, 96))
    tanker(cv, x + 138, y + 57, 0.62)
    tanker(cv, x + 158, y + 66, 0.5)
    warship(cv, x + 84, y + 52, 1.0)
    for wx, wy in ((14, 66), (44, 72), (120, 72), (66, 70)):
        cv.line(x + wx, y + wy, x + wx + 13, y + wy, (190, 224, 240), 1.6)


def sc_cop(cv, x, y):
    cv.vgrad(x, y, 182, 79, (172, 212, 226), (240, 245, 236))
    cv.circle(x + 166, y + 11, 8, (252, 216, 96))
    cv.fill_rect(x, y + 62, 182, 17, (168, 148, 116))
    cv.ellipse(x + 140, y + 71, 54, 12, (96, 168, 98))
    cv.fill_rect(x + 6, y + 42, 62, 22, (130, 122, 116))
    cv.fill_rect(x + 6, y + 42, 62, 4, (108, 100, 96))
    for cxh, cht in ((16, 30), (32, 38), (48, 26)):
        cv.fill_rect(x + cxh, y + 42 - cht, 10, cht, (152, 142, 136))
        cv.fill_rect(x + cxh, y + 42 - cht, 10, 4, (198, 62, 56))
    for sx_, sy_, sr, sc in ((22, 8, 5.6, (128, 128, 132)),
                             (34, 4, 7.6, (150, 150, 154)),
                             (47, 7, 6.2, (140, 140, 144)),
                             (56, 2, 5.2, (160, 160, 164))):
        cv.circle(x + sx_, y + sy_, sr, sc)
    # the leaf
    cv.poly([(x + 112, y + 54), (x + 124, y + 26), (x + 148, y + 12),
             (x + 168, y + 16), (x + 170, y + 34), (x + 152, y + 54),
             (x + 128, y + 60)], (54, 166, 82))
    cv.poly([(x + 124, y + 26), (x + 148, y + 12), (x + 150, y + 34),
             (x + 132, y + 52)], (80, 188, 104))
    cv.line(x + 118, y + 56, x + 164, y + 18, (38, 118, 60), 2)
    cv.line(x + 118, y + 56, x + 110, y + 64, (38, 118, 60), 2.4)
    # knotted rope between factory and leaf
    cv.line(x + 66, y + 54, x + 88, y + 56, (198, 166, 112), 4)
    cv.line(x + 100, y + 55, x + 114, y + 55, (198, 166, 112), 4)
    cv.circle(x + 92, y + 56, 5.5, (186, 154, 100))
    cv.circle(x + 97, y + 53, 4.6, (208, 178, 124))
    cv.circle(x + 90, y + 51, 3.6, (176, 144, 92))
    for fx, fy, fc in ((128, 66, (250, 240, 160)), (150, 70, (250, 250, 250)),
                       (164, 64, (250, 200, 200))):
        cv.circle(x + fx, y + fy, 1.8, fc)


def sc_haiti(cv, x, y):
    cv.vgrad(x, y, 182, 79, (110, 186, 224), (222, 240, 248))
    cv.circle(x + 20, y + 11, 8, (252, 228, 140))
    cloud(cv, x + 142, y + 10, 6, (250, 252, 253))
    cv.vgrad(x, y + 54, 182, 25, (36, 130, 170), (64, 164, 198))
    cv.ellipse(x + 70, y + 60, 66, 11, (240, 216, 152))
    cv.ellipse(x + 70, y + 57, 66, 11, (246, 226, 168))
    cv.line(x + 52, y + 58, x + 58, y + 44, (140, 102, 64), 5)
    cv.line(x + 58, y + 44, x + 66, y + 28, (140, 102, 64), 3.6)
    for ex, ey, mx, my in ((44, 16, 54, 20), (58, 10, 62, 18),
                           (76, 10, 70, 18), (88, 18, 76, 22),
                           (46, 26, 56, 24)):
        cv.line(x + 66, y + 27, x + mx, y + my, (70, 160, 84), 3)
        cv.line(x + mx, y + my, x + ex, y + ey, (70, 160, 84), 2.4)
    cv.circle(x + 63, y + 30, 2.6, (110, 78, 44))
    cv.circle(x + 69, y + 31, 2.6, (110, 78, 44))
    shield(cv, x + 136, y + 14, 52, 52, (24, 62, 128))
    shield(cv, x + 136, y + 17.5, 45, 46, (34, 92, 178))
    star5(cv, x + 136, y + 36, 10, (248, 198, 66))
    for wx, wy in ((118, 68), (150, 72), (14, 70)):
        cv.line(x + wx, y + wy, x + wx + 12, y + wy, (210, 238, 248), 1.6)


def sc_ukeu(cv, x, y):
    cv.vgrad(x, y, 182, 79, (204, 224, 240), (240, 245, 248))
    cv.ellipse(x + 91, y + 72, 80, 5, (190, 205, 220))
    bx, by, bw, bh = x + 94, y + 14, 76, 52
    cv.fill_rect(bx + 3, by + 3, bw, bh, (176, 192, 208))
    cv.fill_rect(bx, by, bw, bh, (240, 240, 244))
    cv.fill_rect(bx + 31, by, 13, bh, (206, 32, 44))
    cv.fill_rect(bx, by + 20, bw, 13, (206, 32, 44))
    cv.rect_outline(bx, by, bw, bh, (120, 130, 145), 2)
    ax, ay, aw, ah = x + 12, y + 14, 76, 52
    cv.fill_rect(ax + 3, ay + 3, aw, ah, (150, 170, 195))
    cv.fill_rect(ax, ay, aw, ah, (34, 82, 166))
    cv.circle(ax + aw, ay + 26, 11, (34, 82, 166))
    cv.circle(ax + aw, ay + 26, 11, (34, 82, 166))
    for i in range(8):
        a = i * pi / 4
        star5(cv, ax + 36 + cos(a) * 17, ay + 26 + sin(a) * 17, 3.4,
              (250, 200, 70))
    sparkle(cv, x + 92, y + 10, 6, (250, 190, 60))
    sparkle(cv, x + 100, y + 66, 4.6, (250, 190, 60))


def sc_saudi(cv, x, y):
    cv.vgrad(x, y, 182, 79, (66, 42, 94), (216, 122, 82))
    base = y + 64
    col = (28, 22, 38)
    cv.fill_rect(x + 4, base - 26, 20, 26, col)
    cv.fill_rect(x + 28, base - 36, 16, 36, col)
    cv.fill_rect(x + 50, base - 30, 6, 30, col)
    cv.fill_rect(x + 66, base - 30, 6, 30, col)
    cv.fill_rect(x + 48, base - 44, 26, 15, col)
    cv.fill_rect(x + 82, base - 22, 18, 22, col)
    cv.fill_rect(x + 140, base - 18, 26, 18, col)
    cv.circle(x + 153, base - 18, 10, col)
    cv.fill_rect(x + 168, base - 30, 12, 30, col)
    rng = Rng(12)
    for _ in range(16):
        cv.fill_rect(x + rng.range(6, 174), base - rng.range(4, 40),
                     2.2, 3, (255, 200, 110))
    cv.fill_rect(x, base, 182, 15, (198, 152, 98))
    cv.ellipse(x + 46, base + 2, 36, 7, (210, 166, 108))
    cv.ellipse(x + 138, base + 3, 34, 6, (188, 142, 90))
    shield(cv, x + 112, y + 8, 46, 48, (198, 156, 52))
    shield(cv, x + 112, y + 11, 39, 42, (32, 58, 118))
    star5(cv, x + 112, y + 28, 8, (250, 226, 150))
    for sx_, sy_, ex, ey in ((176, 2, 132, 16), (168, 12, 134, 26),
                             (182, 20, 136, 34)):
        mx_, my_ = (sx_ + ex) / 2, min(sy_, ey) - 10
        cv.line(x + sx_, y + sy_, x + mx_, y + my_, (250, 206, 130), 2.6,
                dash=(4, 3))
        cv.line(x + mx_, y + my_, x + ex, y + ey, (250, 206, 130), 2.6,
                dash=(4, 3))
        burst(cv, x + ex, y + ey, 5.5)


def sc_greenland(cv, x, y):
    cv.vgrad(x, y, 182, 79, (168, 218, 234), (238, 248, 250))
    cv.circle(x + 18, y + 11, 7.5, (250, 240, 198))
    cv.vgrad(x, y + 56, 182, 23, (70, 150, 185), (112, 182, 206))
    cv.poly([(x + 8, y + 58), (x + 24, y + 48), (x + 40, y + 58)],
            (226, 240, 246))
    cv.poly([(x + 146, y + 59), (x + 160, y + 50), (x + 176, y + 59)],
            (226, 240, 246))
    cv.poly([(x + 28, y + 58), (x + 62, y + 34), (x + 104, y + 28),
             (x + 140, y + 38), (x + 158, y + 58)], (246, 250, 252))
    cv.poly([(x + 104, y + 28), (x + 140, y + 38), (x + 158, y + 58),
             (x + 120, y + 58)], (196, 224, 238))
    cv.poly([(x + 62, y + 34), (x + 84, y + 44), (x + 70, y + 58),
             (x + 44, y + 58)], (214, 234, 244))
    cv.line(x + 96, y + 30, x + 96, y + 6, (70, 74, 82), 2.2)
    cv.fill_rect(x + 96, y + 6, 24, 7, (248, 248, 248))
    cv.fill_rect(x + 96, y + 13, 24, 7, (214, 42, 46))
    cv.circle(x + 103, y + 13, 4.6, (248, 248, 248))
    arc = []
    for i in range(7):
        a = pi + i * pi / 6
        arc.append((x + 103 + 4.6 * cos(a), y + 13 + 4.6 * sin(a)))
    cv.poly(arc, (214, 42, 46))
    shield(cv, x + 136, y + 38, 24, 26, (198, 156, 52))
    shield(cv, x + 136, y + 40.5, 19, 21, (34, 92, 178))
    star5(cv, x + 136, y + 49, 4.6, (250, 226, 150))
    rng = Rng(13)
    for _ in range(22):
        cv.circle(x + rng.range(2, 180), y + rng.range(2, 52), 1.1,
                  (255, 255, 255))
    for wx in (20, 60, 130, 160):
        cv.line(x + wx, y + 68, x + wx + 10, y + 68, (220, 242, 250), 1.5)


def sc_vietnam(cv, x, y):
    cv.vgrad(x, y, 182, 79, (198, 190, 178), (230, 224, 210))
    cv.poly([(x + 52, y + 22), (x + 130, y + 22), (x + 91, y + 10)],
            (128, 122, 116))
    cv.fill_rect(x + 56, y + 22, 78, 4, (120, 114, 108))
    for i in range(4):
        cv.fill_rect(x + 62 + i * 18, y + 26, 7, 26, (134, 128, 120))
    cv.fill_rect(x + 52, y + 52, 86, 4, (120, 114, 108))
    cv.fill_rect(x + 46, y + 56, 98, 4, (110, 104, 98))
    cv.fill_rect(x, y + 62, 182, 17, (164, 152, 134))
    cv.fill_rect(x + 40, y + 60, 110, 3, (140, 130, 114))
    cv.line(x + 91, y + 16, x + 91, y + 27, (120, 92, 58), 3)
    cv.ellipse_ring(x + 91, y + 38, 8.5, 11, 3, (120, 92, 58))
    cv.ring(x + 91, y + 38, 21, 5.5, (206, 34, 40))
    cv.line(x + 76, y + 23, x + 106, y + 53, (206, 34, 40), 5.5)
    cv.line(x + 58, y + 66, x + 70, y + 63, (120, 92, 58), 2.4)
    cv.line(x + 112, y + 65, x + 124, y + 68, (120, 92, 58), 2.4)


def sc_cyber(cv, x, y):
    cv.vgrad(x, y, 182, 79, (52, 62, 84), (88, 100, 124))
    cv.fill_rect(x, y + 62, 182, 17, (36, 42, 56))
    cv.line(x, y + 62, x + 182, y + 62, (120, 132, 152), 1.6)
    shield(cv, x + 52, y + 10, 58, 56, (16, 24, 38))
    shield(cv, x + 52, y + 12, 52, 51, (58, 110, 168))
    shield(cv, x + 52, y + 16, 42, 42, (84, 140, 200))
    cv.circle(x + 52, y + 34, 5, (14, 22, 34))
    cv.poly([(x + 48.5, y + 36), (x + 55.5, y + 36), (x + 57, y + 46),
             (x + 47, y + 46)], (14, 22, 34))
    crack = [(40, 14), (48, 24), (43, 32), (52, 42), (47, 52), (54, 60)]
    for a, b in zip(crack, crack[1:]):
        cv.line(x + a[0], y + a[1], x + b[0], y + b[1], (16, 24, 36), 2.6)
    # open exit door with light spilling out
    cv.fill_rect(x + 118, y + 8, 52, 56, (20, 26, 38))
    cv.vgrad(x + 122, y + 12, 44, 52, (252, 224, 148), (246, 196, 104))
    cv.poly([(x + 122, y + 12), (x + 104, y + 18), (x + 104, y + 58),
             (x + 122, y + 64)], (150, 96, 54))
    cv.poly([(x + 122, y + 12), (x + 104, y + 18), (x + 104, y + 58),
             (x + 122, y + 64)], (160, 104, 60))
    cv.circle(x + 108, y + 38, 2.2, (250, 220, 150))
    cv.poly([(x + 122, y + 64), (x + 166, y + 64), (x + 178, y + 76),
             (x + 110, y + 76)], (240, 200, 116))
    cv.fill_rect(x + 124, y + 0.5, 40, 10, (206, 40, 44))
    cv.text(x + 144, y + 2.2, "EXIT", 7, (255, 244, 230), align='c',
            condense=1.0)


def sc_iraq(cv, x, y):
    cv.vgrad(x, y, 182, 79, (246, 166, 84), (252, 226, 172))
    for a in (0.35, 0.8, 1.25, 1.7, 2.2, 2.65):
        cv.line(x + 58 + cos(a) * 20, y + 52 - sin(a) * 20,
                x + 58 + cos(a) * 27, y + 52 - sin(a) * 27,
                (255, 200, 110), 2)
    cv.circle(x + 58, y + 52, 17, (255, 214, 130))
    cv.circle(x + 58, y + 52, 12.5, (255, 232, 168))
    col, col_d = (146, 104, 66), (128, 90, 56)
    cv.fill_rect(x + 6, y + 44, 30, 22, col)
    cv.fill_rect(x + 40, y + 38, 26, 28, col_d)
    cv.circle(x + 53, y + 38, 9, col_d)
    cv.fill_rect(x + 118, y + 40, 30, 26, col)
    cv.circle(x + 133, y + 40, 8, col)
    cv.fill_rect(x + 152, y + 34, 10, 32, col_d)
    cv.poly([(x + 150, y + 34), (x + 164, y + 34), (x + 157, y + 26)], col_d)
    cv.fill_rect(x + 154.5, y + 40, 5, 6, (250, 220, 160))
    cv.fill_rect(x + 76, y + 36, 34, 30, col)
    cv.circle(x + 93, y + 36, 17, col)
    cv.poly([(x + 82, y + 66), (x + 82, y + 48), (x + 93, y + 40),
             (x + 104, y + 48), (x + 104, y + 66)], (70, 48, 30))
    for wx, wy in ((14, 50), (26, 54), (46, 46), (124, 48), (138, 54),
                   (84, 44)):
        cv.fill_rect(x + wx, y + wy, 3.4, 4.6, (255, 224, 150))
    cv.line(x + 93, y + 20, x + 93, y + 8, (60, 44, 30), 2.2)
    cv.fill_rect(x + 93, y + 8, 26, 5.2, (206, 40, 44))
    cv.fill_rect(x + 93, y + 13.2, 26, 5.2, (246, 246, 246))
    cv.fill_rect(x + 93, y + 18.4, 26, 5.2, (28, 28, 32))
    for dx in (7, 12, 17):
        cv.circle(x + 93 + dx, y + 15.8, 1.3, (40, 150, 80))
    cv.fill_rect(x, y + 66, 182, 13, (176, 134, 84))
    cv.ellipse(x + 40, y + 70, 50, 6, (190, 148, 96))
    cv.ellipse(x + 150, y + 72, 46, 5, (166, 126, 78))
    for bx, by in ((140, 14), (156, 9), (126, 7)):
        cv.line(x + bx - 4, y + by, x + bx, y + by - 2.6, (90, 64, 44), 1.5)
        cv.line(x + bx, y + by - 2.6, x + bx + 4, y + by, (90, 64, 44), 1.5)


# --------------------------------------------------------------------------
# Page composition.
# --------------------------------------------------------------------------

PANELS = [
    (sc_peace, "RIVALS SIGN PEACE DEAL"),
    (sc_court, "COURT: MYANMAR GENOCIDE"),
    (sc_markets, "AI SELL-OFF ROUTS MARKETS"),
    (sc_ipo, "RECORD IPO STAR SLIDES"),
    (sc_kerch, "KERCH BRIDGE SPAN DOWN"),
    (sc_microsoft, "MICROSOFT OUTAGE WORLDWIDE"),
    (sc_hormuz, "US BLOCKADE CHOKES HORMUZ"),
    (sc_cop, "COP31 STALLS ON FOSSILS"),
    (sc_haiti, "HAITI RAID KILLS 34"),
    (sc_ukeu, "UK-EU RESET DEAL"),
    (sc_saudi, "SAUDI SHIELD STOPS MISSILES"),
    (sc_greenland, "GREENLAND SECURITY DEAL"),
    (sc_vietnam, "VIETNAM CUTS DEATH PENALTY"),
    (sc_cyber, "TRUMP FIRES CYBER CHIEF"),
    (sc_iraq, "IRAQ ENTERS MILITIA TOWN"),
]

STRIP = [
    ("AMERICAS", (196, 56, 44),
     ["BUKELE SEEKS THIRD TERM", "PERU HIT BY 6.7 QUAKE",
      "COLOMBIA PROTESTS TAXES", "LULA SHIELDS AMAZON",
      "SHEINBAUM FLIGHT VIRAL", "CANADA DEAL NEEDS WORK",
      "DATA-CENTRE TAX VOW"]),
    ("EUROPE", (36, 84, 168),
     ["GUARANTEES FOR UKRAINE", "NL EMBASSY HIT IN KYIV",
      "HUNGARY LIFTS EU VETO", "FRANKFURT PLOT ARRESTS",
      "META FINED EUR 805M", "KHARKIV TOWNS RETAKEN",
      "DENMARK EXPELS ATTACHE", "CEASEFIRE DRILLS POLAND"]),
    ("MIDDLE EAST", (196, 138, 30),
     ["QESHM BLAST: DISPOSAL", "QATAR MEDIATES HORMUZ",
      "SAUDI STRIKES HODEIDAH", "TEHRAN REJECTS US TERMS"]),
    ("AFRICA", (36, 140, 80),
     ["ANGOLA IN DE BEERS DEAL", "BOAT CAPSIZES SENEGAL",
      "LAST EBOLA CASE OUT"]),
    ("ASIA-PACIFIC", (128, 62, 168),
     ["CYCLONE AKVAN TO INDIA", "JAPAN QUAKE INJURES 22",
      "TSMC TIGHTENS CURBS", "KOREA CHOLERA AFTER 10Y",
      "NICHOLLS 113 LIFTS NZ", "XAVIER HITS COOK IS.",
      "JAPAN SUB STUDY FUNDED", "BOMBERS ENTER TW ZONE"]),
]


def panel_label(cv, x, y, w, label):
    by = y + 85
    cv.fill_rect(x + 3, by, w - 6, 32, (17, 23, 32))
    size1 = cv.fit_size(label, w - 16, 15.5)
    if size1 >= 11.8:
        cv.text(x + w / 2, by + (32 - size1) / 2, label, size1,
                (250, 244, 230), align='c')
        return
    words = label.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        score = max(cv.text_w(a, 13.0), cv.text_w(b, 13.0))
        if best is None or score < best[0]:
            best = (score, a, b)
    _, la, lb = best
    size = min(13.5, (w - 16) / max(cv.text_w(la, 1.0),
                                    cv.text_w(lb, 1.0)))
    cv.text(x + w / 2, by + 3.2, la, size, (250, 244, 230), align='c')
    cv.text(x + w / 2, by + 3.2 + size + 2.8, lb, size, (250, 244, 230),
            align='c')


def panel(cv, x, y, w, scene_fn, label):
    cv.fill_rect(x, y, w, 120, INK)
    scene_fn(cv, x + 3, y + 3)
    panel_label(cv, x, y, w, label)


def compose():
    cv = Canvas(W, H, SS)
    cv.fill_rect(0, 0, W, H, PAPER)
    cv.rect_outline(8, 8, W - 16, H - 16, INK, 3)
    cv.rect_outline(14, 14, W - 28, H - 28, INK, 1.2)
    # masthead
    cv.fill_rect(26, 24, 972, 3, INK)
    cv.fill_rect(26, 30, 972, 1.2, INK)
    cv.text(512, 38, "THE WORLD IN ONE DAY", 22, INK, align='c',
            tracking=1.25)
    dsize = cv.fit_size("FRIDAY 20 NOVEMBER 2026", 950, 56)
    cv.text(512, 66, "FRIDAY 20 NOVEMBER 2026", dsize, INK, align='c')
    cv.text(512, 66 + dsize + 8, "EVERY CONTINENT · EVERY BIG STORY · ONE DAY",
            14.5, (150, 32, 38), align='c', tracking=1.1)
    rule_y = 66 + dsize + 8 + 22
    cv.fill_rect(26, rule_y, 972, 1.2, INK)
    cv.fill_rect(26, rule_y + 4, 972, 3, INK)
    # hero
    hx, hy, hw, hh = 26, 164, 972, 296
    cv.fill_rect(hx, hy, hw, hh, INK)
    sc_hero(cv, hx + 3, hy + 3, hw - 6, hh - 70)
    by = hy + hh - 64
    cv.vgrad(hx + 3, by, hw - 6, 61, (146, 18, 28), (198, 42, 46))
    tsize = cv.fit_size("RUSSIA BOMBARDS UKRAINE", 930, 30)
    cv.text(512, by + 7, "RUSSIA BOMBARDS UKRAINE", tsize, (255, 246, 230),
            align='c')
    fact = "400+ DRONES · 110 MISSILES · KYIV BRIDGES AND POWER GRID HIT · 8 DEAD"
    fsize = cv.fit_size(fact, 930, 14.5)
    cv.text(512, by + 7 + tsize + 5, fact, fsize, (255, 214, 170), align='c')
    # panel grid: 5 columns x 3 rows
    for idx, (fn, label) in enumerate(PANELS):
        px = 26 + (idx % 5) * 196
        py = 468 + (idx // 5) * 128
        panel(cv, px, py, 188, fn, label)
    # headlines strip
    sy = 852
    cv.text(26, sy, "MORE OF THE DAY", 15, INK)
    cv.text(998, sy, "REGION BY REGION", 15, (176, 28, 36), align='r')
    cv.fill_rect(26, sy + 22, 972, 2.4, INK)
    for i, (name, colr, lines) in enumerate(STRIP):
        cx = 26 + i * 196
        cv.fill_rect(cx, sy + 32, 26, 3.4, colr)
        cv.text(cx, sy + 40, name, 12.5, colr)
        ly = sy + 60
        for ln in lines:
            sz = cv.fit_size(ln, 182, 9.8, condense=0.88)
            cv.text(cx, ly, ln, sz, (40, 44, 52), condense=0.88)
            ly += 11.6
    return cv


def render_png_bytes():
    cv = compose()
    rgb, w, h = cv.downscale()
    return encode_png(rgb, w, h)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    try:
        data = render_png_bytes()
    except Exception:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "fallback.png"), "rb") as fh:
            data = fh.read()
    with open(os.path.join(outdir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
