#!/usr/bin/env python3
"""Sum up 20 November 2026's world news in one image.

A pure-standard-library drawing program: it rasterises a broadsheet
front page (masthead, one hero panel, fifteen drawn story panels and a
regional headlines strip) and writes it as entry.png.

Run:  python3 main.py          (writes to $MAKEFUN_OUTPUT_DIR or /output)
"""

import os
import shutil
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- PNG -----


def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def encode_png(w, h, buf):
    """Encode an RGB bytearray (w*h*3) as PNG bytes, deterministically."""
    stride = w * 3
    raw = bytearray()
    prev = bytearray(stride)
    for y in range(h):
        row = bytes(buf[y * stride:(y + 1) * stride])
        best = None
        for f in (0, 1, 2):
            if f == 0:
                filt = row
            elif f == 1:
                filt = bytes((row[i] - (row[i - 3] if i >= 3 else 0)) & 0xFF
                             for i in range(stride))
            else:
                filt = bytes((row[i] - prev[i]) & 0xFF for i in range(stride))
            score = 0
            for b in filt:
                score += b if b < 128 else 256 - b
            if best is None or score < best[0]:
                best = (score, f, filt)
        raw.append(best[1])
        raw += best[2]
        prev = bytearray(row)
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            _chunk(b"IEND", b""))


# ------------------------------------------------------------- colours -----

PAPER = (247, 242, 231)
INK = (26, 26, 40)
RED = (178, 34, 44)
DARKRED = (120, 22, 30)
NAVY = (16, 24, 48)
SKYBLUE = (120, 178, 224)
SEA = (38, 96, 140)
SAND = (216, 188, 138)
GREEN = (52, 140, 74)
LEAF = (74, 178, 92)
GOLD = (232, 176, 44)
ORANGE = (240, 120, 40)
SMOKE = (120, 124, 134)
GREY = (96, 100, 110)
LIGHT = (238, 240, 244)
WHITE = (255, 255, 255)
BLACK = (8, 8, 12)
TAN = (198, 164, 110)

# -------------------------------------------------------------- canvas -----


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.clip = (0, 0, w, h)
        self.rect(0, 0, w, h, bg)

    def set_clip(self, x0, y0, x1, y1):
        self.clip = (max(0, x0), max(0, y0), min(self.w, x1), min(self.h, y1))

    def full_clip(self):
        self.clip = (0, 0, self.w, self.h)

    def px(self, x, y, c):
        cx0, cy0, cx1, cy1 = self.clip
        if cx0 <= x < cx1 and cy0 <= y < cy1:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x0, y0, x1, y1, c):
        cx0, cy0, cx1, cy1 = self.clip
        x0 = max(x0, cx0)
        y0 = max(y0, cy0)
        x1 = min(x1, cx1)
        y1 = min(y1, cy1)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(c) * (x1 - x0)
        n = (x1 - x0) * 3
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.buf[i:i + n] = row

    def frame(self, x0, y0, x1, y1, c, th=2):
        self.rect(x0, y0, x1, y0 + th, c)
        self.rect(x0, y1 - th, x1, y1, c)
        self.rect(x0, y0, x0 + th, y1, c)
        self.rect(x1 - th, y0, x1, y1, c)

    def line(self, x0, y0, x1, y1, c, th=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = th // 2
        while True:
            self.circle(x0, y0, r, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        if r <= 0:
            self.px(cx, cy, c)
            return
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def ring(self, cx, cy, r, c, th=2):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d2 = dx * dx + dy * dy
                if (r - th) * (r - th) <= d2 <= r * r:
                    self.px(cx + dx, cy + dy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        if rx <= 0 or ry <= 0:
            return
        for dy in range(-ry, ry + 1):
            dx = int(rx * (1.0 - (dy * dy) / float(ry * ry)) ** 0.5)
            self.rect(cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        y0, y1 = min(ys), max(ys)
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                if ya == yb:
                    continue
                if (ya <= y < yb) or (yb <= y < ya):
                    xs.append(xa + (y - ya) * (xb - xa) // (yb - ya))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(xs[i], y, xs[i + 1] + 1, y + 1, c)

    def star(self, cx, cy, r_out, r_in, c, n=8, rot=0.0):
        import math
        pts = []
        for i in range(2 * n):
            r = r_out if i % 2 == 0 else r_in
            a = rot + i * math.pi / n
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.poly(pts, c)

    def bezier(self, p0, p1, p2, c, th=2):
        steps = 40
        last = None
        for i in range(steps + 1):
            t = i / steps
            x = int((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0])
            y = int((1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1])
            if last is not None:
                self.line(last[0], last[1], x, y, c, th)
            last = (x, y)

    def gradient(self, x0, y0, x1, y1, top, bot):
        for y in range(y0, y1):
            t = (y - y0) / max(1, (y1 - y0 - 1))
            c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
            self.rect(x0, y, x1, y + 1, c)


def lcg(seed):
    """Deterministic pseudo-random stream (fixed seed -> fixed art)."""
    state = [seed & 0x7FFFFFFF]

    def nxt(mod):
        state[0] = (state[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return state[0] % mod

    return nxt


# ---------------------------------------------------------------- font -----

FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    '2': (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ';': (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '%': ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.##."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '=': (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '_': (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale if s else 0


def draw_text(c, x, y, s, scale, color, bold=False):
    """Draw text with top-left at (x, y). Returns the x just past the text."""
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        for gy, row in enumerate(glyph):
            for gx, cell in enumerate(row):
                if cell == '#':
                    bx = x + gx * scale
                    by = y + gy * scale
                    c.rect(bx, by, bx + scale, by + scale, color)
                    if bold:
                        off = max(1, scale // 2)
                        c.rect(bx + off, by, bx + off + scale, by + scale, color)
        x += 6 * scale
    return x


def draw_text_centered(c, cx, y, s, scale, color, bold=False):
    w = text_width(s, scale)
    if bold:
        w += max(1, scale // 2)
    return draw_text(c, cx - w // 2, y, s, scale, color, bold)


def wrap_text(s, max_chars):
    words = s.split()
    lines = []
    cur = ""
    for wd in words:
        if not cur:
            cur = wd
        elif len(cur) + 1 + len(wd) <= max_chars:
            cur += " " + wd
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- scenes -----


def burst(c, cx, cy, r, col_core=GOLD, col_ray=ORANGE):
    c.star(cx, cy, r, max(2, r * 2 // 5), col_ray, n=8)
    c.circle(cx, cy, max(2, r // 3), col_core)


def smoke(c, cx, cy, r, col=SMOKE):
    for dx, dy, rr in ((-r // 2, 0, r * 3 // 5), (r // 3, -r // 4, r * 7 // 10),
                       (0, r // 5, r // 2), (r // 2, r // 4, r * 2 // 5)):
        c.circle(cx + dx, cy + dy, rr, col)


def scene_hero(c, x, y, w, h):
    """Story 1: Russia's giant missile-and-drone barrage on Ukraine."""
    c.gradient(x, y, x + w, y + h, (10, 14, 34), (34, 44, 74))
    rnd = lcg(20261120)
    for _ in range(70):  # stars
        c.px(x + rnd(w), y + rnd(h // 2), (200, 205, 220))
    # missile trails + bodies arcing in
    trails = [((x + w - 60, y + 6), (x + w - 300, y + 30), (x + 560, y + 96)),
              ((x + w - 200, y + 2), (x + w - 420, y + 26), (x + 430, y + 110)),
              ((x + 80, y + 4), (x + 260, y + 30), (x + 350, y + 92)),
              ((x + 300, y + 2), (x + 430, y + 22), (x + 640, y + 104))]
    for p0, p1, p2 in trails:
        c.bezier(p0, p1, p2, (240, 190, 120), 3)
        c.bezier(p0, p1, p2, (255, 240, 210), 1)
        c.circle(p2[0], p2[1], 4, (220, 224, 230))
        burst(c, p2[0] + 6, p2[1] + 8, 12)
    # drones (small X shapes with a red eye)
    for dx, dy in ((180, 34), (700, 26), (520, 48), (90, 60), (830, 44)):
        cx, cy = x + dx, y + dy
        c.line(cx - 9, cy - 6, cx + 9, cy + 6, (30, 34, 44), 3)
        c.line(cx - 9, cy + 6, cx + 9, cy - 6, (30, 34, 44), 3)
        c.circle(cx, cy, 3, RED)
    base = y + h - 44
    # far skyline with lit windows
    rnd2 = lcg(777)
    bx = x + 6
    while bx < x + w - 30:
        bw = 26 + rnd2(38)
        bh = 40 + rnd2(56)
        c.rect(bx, base - bh, bx + bw, base, (16, 22, 40))
        for _ in range(bw // 6):
            wx = bx + 3 + rnd2(max(4, bw - 8))
            wy = base - bh + 4 + rnd2(max(4, bh - 10))
            c.rect(wx, wy, wx + 3, wy + 4, (250, 205, 90))
        bx += bw + 4 + rnd2(10)
    # river band
    c.rect(x, base, x + w, y + h, (18, 44, 66))
    for i in range(26):
        sx = x + rnd2(w - 30)
        c.line(sx, base + 6 + rnd2(h - 50), sx + 16, base + 6 + rnd2(h - 50),
               (70, 120, 160), 2)
    # bridge: two towers, deck, cables; middle hit
    deck_y = base - 6
    c.rect(x + 40, deck_y, x + w - 40, deck_y + 8, (128, 138, 152))
    for tx in (x + 240, x + w - 240):
        c.rect(tx, deck_y - 56, tx + 12, deck_y, (128, 138, 152))
        c.line(tx + 6, deck_y - 56, x + 60, deck_y, (168, 176, 188), 2)
        c.line(tx + 6, deck_y - 56, x + w - 60, deck_y, (168, 176, 188), 2)
    burst(c, x + w // 2, deck_y - 2, 30)
    burst(c, x + w // 2 - 90, deck_y - 6, 18)
    smoke(c, x + w // 2 + 10, deck_y - 46, 30)
    smoke(c, x + 210, base - 66, 20, (96, 100, 110))
    burst(c, x + 190, base - 40, 15)
    # near silhouettes
    c.rect(x, base - 26, x + 90, base + 2, (8, 10, 18))
    c.rect(x + w - 110, base - 34, x + w, base + 2, (8, 10, 18))


def scene_peace(c, x, y, w, h):
    """Story 2: three rivals sign a peace declaration in Shenzhen."""
    c.gradient(x, y, x + w, y + h, (168, 205, 232), (226, 238, 246))
    # three banners behind
    for i, col in enumerate((RED, (44, 84, 160), GOLD)):
        bx = x + 22 + i * (w // 3)
        c.rect(bx, y + 4, bx + 3, y + h - 26, (90, 80, 60))
        c.poly([(bx + 3, y + 6), (bx + 34, y + 10), (bx + 3, y + 26)], col)
    # dove above (soft sky patch behind it so the white bird reads)
    cx, cy = x + w // 2, y + 16
    c.ellipse(cx, cy, 34, 13, (140, 178, 204))
    c.ellipse(cx, cy, 13, 6, WHITE)
    c.poly([(cx - 12, cy), (cx - 26, cy - 10), (cx - 8, cy + 3)], WHITE)
    c.poly([(cx + 2, cy - 2), (cx + 16, cy - 12), (cx + 14, cy + 2)], WHITE)
    c.circle(cx + 12, cy - 3, 3, WHITE)
    c.px(cx + 13, cy - 3, ORANGE)
    # round table + three chairs
    ty = y + h - 30
    c.ellipse(x + w // 2, ty, w // 3, 12, (120, 84, 50))
    c.ellipse(x + w // 2, ty - 3, w // 3, 12, (160, 116, 72))
    for i, dx in enumerate((w // 6, w // 2, 5 * w // 6)):
        c.rect(x + dx - 10, ty + 6, x + dx + 10, ty + 18, (70, 60, 50))
    # paper on the table
    c.rect(x + w // 2 - 14, ty - 8, x + w // 2 + 14, ty - 1, WHITE)


def scene_icj(c, x, y, w, h):
    """Story 3: World Court condemns Myanmar genocide."""
    c.gradient(x, y, x + w, y + h, (196, 205, 214), (232, 234, 236))
    cx = x + w // 2
    # scales of justice on the roof
    top = y + 4
    c.line(cx, top, cx, top + 14, INK, 2)
    c.line(cx - 16, top + 3, cx + 16, top + 3, INK, 2)
    for sx in (cx - 16, cx + 16):
        c.line(sx, top + 3, sx - 5, top + 12, INK, 1)
        c.line(sx, top + 3, sx + 5, top + 12, INK, 1)
        c.poly([(sx - 6, top + 12), (sx + 6, top + 12), (sx, top + 17)], GOLD)
    # pediment + columns
    c.poly([(x + 12, top + 24), (x + w - 12, top + 24), (cx, top + 15)], (240, 240, 242))
    c.rect(x + 12, top + 24, x + w - 12, top + 28, (240, 240, 242))
    for i in range(4):
        colx = x + 22 + i * ((w - 44) // 3)
        c.rect(colx, top + 28, colx + 8, y + h - 12, WHITE)
    c.rect(x + 10, y + h - 12, x + w - 10, y + h - 7, (200, 203, 208))
    c.rect(x + 6, y + h - 7, x + w - 6, y + h - 2, (188, 191, 196))


def scene_markets(c, x, y, w, h):
    """Story 4: AI sell-off routs global markets."""
    c.gradient(x, y, x + w, y + h, (14, 18, 34), (30, 38, 62))
    cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 6
    c.circle(cx, cy, r, (38, 84, 140))
    c.ellipse(cx, cy, r // 3, r, (46, 104, 158))
    c.ellipse(cx, cy, r, r // 4, (46, 104, 158))
    c.line(cx - r, cy, cx + r, cy, (46, 104, 158), 1)
    # plunging red zigzag across the globe
    pts = [(x + 8, y + 10), (x + w // 4, y + h // 3), (x + w // 3, y + h // 4),
           (x + w // 2, y + h // 2), (x + 3 * w // 5, y + 2 * h // 5),
           (x + w - 26, y + h - 14)]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], RED, 4)
    ex, ey = pts[-1]
    c.poly([(ex, ey), (ex - 14, ey - 2), (ex - 4, ey - 12)], RED)


def scene_anthropic(c, x, y, w, h):
    """Story 5: record IPO star Anthropic slides."""
    c.gradient(x, y, x + w, y + h, (240, 234, 214), (250, 246, 232))
    cx = x + w // 2
    # opening bell
    c.circle(cx, y + 16, 10, GOLD)
    c.rect(cx - 3, y + 2, cx + 3, y + 8, (120, 90, 30))
    c.circle(cx, y + 16, 5, (250, 205, 90))
    # chart: rockets up, then bends down
    base = y + h - 8
    c.line(x + 8, base, x + w - 8, base, GREY, 2)
    pts = [(x + 10, base - 4), (x + w // 3, base - 10), (x + w // 2, y + 34),
           (x + 2 * w // 3, y + 40), (x + w - 14, base - 16)]
    cols = [GREEN, GREEN, RED, RED]
    for i in range(len(pts) - 1):
        c.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], cols[i], 4)
    ex, ey = pts[-1]
    c.poly([(ex, ey), (ex - 13, ey - 4), (ex - 3, ey - 13)], RED)


def scene_kerch(c, x, y, w, h):
    """Story 6: Ukraine collapses Kerch Bridge roadway."""
    c.gradient(x, y, x + w, y + h * 3 // 5, (150, 196, 228), (196, 224, 240))
    c.rect(x, y + h * 3 // 5, x + w, y + h, SEA)
    deck = y + h * 3 // 5 - 4
    # intact spans left and right, middle tilted into the sea
    c.rect(x + 4, deck, x + w // 3, deck + 6, (110, 116, 124))
    c.rect(x + 2 * w // 3, deck, x + w - 4, deck + 6, (110, 116, 124))
    c.poly([(x + w // 3, deck), (x + 2 * w // 3, deck + 2),
            (x + 2 * w // 3 - 6, deck + 26), (x + w // 3 + 8, deck + 20)],
           (90, 96, 104))
    for px_ in (x + w // 4, x + 3 * w // 4):
        c.rect(px_, deck + 6, px_ + 6, y + h - 4, (90, 96, 104))
    # splash where the span went down
    for dx in (-8, 0, 9):
        c.line(x + w // 2 + dx, deck + 22, x + w // 2 + dx * 2, deck + 8, WHITE, 2)


def scene_microsoft(c, x, y, w, h):
    """Story 7: Microsoft outage darkens offices worldwide."""
    c.gradient(x, y, x + w, y + h, (24, 28, 40), (40, 46, 60))
    # dark monitor
    mx0, my0, mx1, my1 = x + 16, y + 6, x + w - 16, y + h - 12
    c.rect(mx0, my0, mx1, my1, (10, 12, 18))
    c.frame(mx0, my0, mx1, my1, (90, 96, 108), 3)
    c.rect(x + w // 2 - 4, my1, x + w // 2 + 4, y + h - 4, (90, 96, 108))
    # envelope icon
    ex0, ey0 = mx0 + 14, my0 + 12
    c.rect(ex0, ey0, ex0 + 34, ey0 + 24, (70, 120, 180))
    c.poly([(ex0, ey0), (ex0 + 34, ey0), (ex0 + 17, ey0 + 13)], (120, 170, 220))
    # chat bubble icon
    bx0, by0 = mx1 - 48, my0 + 12
    c.rect(bx0, by0, bx0 + 34, by0 + 22, (70, 150, 110))
    c.poly([(bx0 + 6, by0 + 22), (bx0 + 16, by0 + 22), (bx0 + 8, by0 + 30)],
           (70, 150, 110))
    # big red X over the screen
    c.line(mx0 + 10, my0 + 8, mx1 - 10, my1 - 8, RED, 6)
    c.line(mx1 - 10, my0 + 8, mx0 + 10, my1 - 8, RED, 6)


def scene_hormuz(c, x, y, w, h):
    """Story 8: US blockade chokes the Strait of Hormuz."""
    c.rect(x, y, x + w, y + h, SEA)
    # land masses squeezing the strait
    c.poly([(x, y), (x + w // 3, y), (x + w // 5, y + h), (x, y + h)], SAND)
    c.poly([(x + w, y), (x + w, y + h), (x + 4 * w // 5, y + h),
            (x + 2 * w // 3, y)], SAND)
    mid = y + h // 2
    # warship in the narrows
    wx = x + w // 2
    c.poly([(wx - 36, mid + 6), (wx + 36, mid + 6), (wx + 26, mid + 20),
            (wx - 26, mid + 20)], (112, 120, 130))
    c.rect(wx - 14, mid - 6, wx + 16, mid + 6, (140, 148, 158))
    c.rect(wx + 2, mid - 18, wx + 7, mid - 6, (140, 148, 158))
    c.line(wx - 20, mid - 6, wx - 28, mid - 14, (140, 148, 158), 3)
    # tankers queueing behind
    for i, tx in enumerate((x + w - 44, x + w - 78)):
        ty = y + 10 + i * 28
        c.poly([(tx - 19, ty + 7), (tx + 19, ty + 7), (tx + 13, ty + 14),
                (tx - 13, ty + 14)], (30, 32, 38))
        c.rect(tx - 10, ty, tx + 10, ty + 7, (58, 62, 70))


def scene_cop(c, x, y, w, h):
    """Story 9: climate talks stall over fossil fuels."""
    c.gradient(x, y, x + w, y + h, (206, 214, 200), (232, 236, 220))
    # factory chimneys left
    for i, chx in enumerate((x + 12, x + 32)):
        c.rect(chx, y + h // 3, chx + 12, y + h - 8, (120, 110, 100))
        c.rect(chx - 2, y + h // 3 - 4, chx + 14, y + h // 3, (100, 92, 84))
        smoke(c, chx + 6, y + h // 3 - 14, 10, (150, 148, 140))
    # green leaf right
    lx, ly = x + w - 44, y + h // 2
    c.ellipse(lx, ly, 24, 13, LEAF)
    c.line(lx - 22, ly + 10, lx + 22, ly - 10, (40, 110, 56), 2)
    c.line(lx + 20, ly + 8, lx + 30, ly + 16, (110, 84, 50), 3)
    # knotted rope between them
    ry = y + h - 18
    c.line(x + 8, ry, x + w - 8, ry, (150, 120, 70), 3)
    c.ring(x + w // 2, ry, 8, (150, 120, 70), 3)
    c.ring(x + w // 2 - 10, ry, 6, (150, 120, 70), 3)


def scene_haiti(c, x, y, w, h):
    """Story 10: Haiti police kill 34 suspects in a big operation."""
    c.rect(x, y, x + w, y + h, SEA)
    # island
    c.ellipse(x + w // 2, y + h - 16, w // 2 - 8, 16, (86, 160, 92))
    # palm tree
    px_, py = x + w // 3, y + h - 22
    c.bezier((px_, py), (px_ + 4, py - 18), (px_ + 10, py - 30), (110, 84, 50), 4)
    for a in range(5):
        import math
        ang = math.pi * (0.08 + 0.21 * a)
        ex = int(px_ + 10 + 20 * math.cos(ang))
        ey = int(py - 30 - 12 * math.sin(ang))
        c.bezier((px_ + 10, py - 30), (px_ + 10 + 10, py - 40), (ex, ey), GREEN, 3)
    # police shield badge
    sx, sy = x + 2 * w // 3, y + h // 2 - 6
    c.poly([(sx - 15, sy - 14), (sx + 15, sy - 14), (sx + 15, sy + 4),
            (sx, sy + 20), (sx - 15, sy + 4)], (36, 72, 150))
    c.star(sx, sy - 2, 8, 3, GOLD, n=5)


def scene_ukeu(c, x, y, w, h):
    """Story 11: Britain and the EU agree a reset deal."""
    c.gradient(x, y, x + w, y + h, (214, 224, 238), (236, 240, 246))
    cy = y + h // 2
    # left piece with circle of stars (EU)
    lx = x + w // 2 - 34
    c.rect(lx - 30, cy - 24, lx + 8, cy + 24, (44, 84, 160))
    c.circle(lx + 8, cy - 6, 7, (44, 84, 160))
    import math
    for i in range(8):
        a = i * math.pi / 4
        c.circle(int(lx - 11 + 13 * math.cos(a)), int(cy + 13 * math.sin(a)), 2, GOLD)
    # right piece with a red cross (UK-ish)
    rx = x + w // 2 + 30
    c.rect(rx - 8, cy - 24, rx + 30, cy + 24, WHITE)
    c.circle(rx - 8, cy + 8, 7, WHITE)
    c.rect(rx + 6, cy - 24, rx + 16, cy + 24, RED)
    c.rect(rx - 8, cy - 5, rx + 30, cy + 5, RED)


def scene_saudi(c, x, y, w, h):
    """Story 12: Saudi shields stop Houthi missiles."""
    c.gradient(x, y, x + w, y + h, (240, 214, 160), (246, 230, 190))
    base = y + h - 8
    # skyline towers
    for tx, th_ in ((10, 34), (36, 48), (70, 28), (w - 60, 42), (w - 34, 30)):
        c.rect(x + tx, base - th_, x + tx + 20, base, (150, 138, 120))
    # missile arcs bouncing off a shield
    sx, sy = x + w // 2, y + h // 3
    for p0, p1, p2 in (((x + 8, y + 4), (x + 50, y + 6), (sx - 16, sy - 4)),
                       ((x + w - 8, y + 2), (x + w - 52, y + 8), (sx + 16, sy - 6))):
        c.bezier(p0, p1, p2, (120, 110, 100), 3)
    burst(c, sx - 18, sy - 6, 9)
    burst(c, sx + 18, sy - 8, 9)
    # the shield
    c.poly([(sx - 14, sy - 10), (sx + 14, sy - 10), (sx + 14, sy + 8),
            (sx, sy + 24), (sx - 14, sy + 8)], (52, 140, 74))
    c.poly([(sx - 9, sy - 6), (sx + 9, sy - 6), (sx + 9, sy + 6),
            (sx, sy + 17), (sx - 9, sy + 6)], LEAF)


def scene_greenland(c, x, y, w, h):
    """Story 13: Denmark seals Greenland security deal."""
    c.rect(x, y, x + w, y + h, (52, 110, 156))
    # ice island
    c.poly([(x + 18, y + h - 14), (x + 44, y + h // 2 + 8), (x + w // 2, y + h // 3),
            (x + w - 40, y + h // 2), (x + w - 16, y + h - 14)], (238, 244, 248))
    c.poly([(x + w // 2, y + h // 3), (x + w - 40, y + h // 2),
            (x + w // 2 + 12, y + h // 2 + 4)], (210, 226, 236))
    # flag on the summit (Greenland: white/red with disc)
    fx, fy = x + w // 2, y + h // 3
    c.line(fx, fy, fx, fy - 22, (60, 60, 66), 3)
    c.rect(fx, fy - 22, fx + 26, fy - 16, WHITE)
    c.rect(fx, fy - 16, fx + 26, fy - 10, RED)
    c.circle(fx + 8, fy - 16, 4, RED)
    # small shield beside the island
    sx, sy = x + w - 34, y + h - 30
    c.poly([(sx - 10, sy - 10), (sx + 10, sy - 10), (sx + 10, sy + 2),
            (sx, sy + 14), (sx - 10, sy + 2)], GOLD)


def scene_vietnam(c, x, y, w, h):
    """Story 14: Vietnam scraps death penalty offences."""
    c.gradient(x, y, x + w, y + h, (226, 220, 204), (240, 236, 220))
    cx = x + w // 2
    # gallows beam + rope + noose
    c.rect(x + 16, y + 8, x + w - 16, y + 14, (110, 88, 60))
    c.rect(x + 20, y + 8, x + 26, y + h - 8, (110, 88, 60))
    c.line(cx + 18, y + 14, cx + 18, y + 30, (90, 74, 48), 3)
    c.ring(cx + 18, y + 42, 11, (90, 74, 48), 3)
    # big red cross struck through it
    c.line(cx - 2, y + 16, cx + 40, y + h - 14, RED, 7)
    c.line(cx + 40, y + 16, cx - 2, y + h - 14, RED, 7)


def scene_cairncross(c, x, y, w, h):
    """Story 15: Trump fires cyber chief Cairncross."""
    c.gradient(x, y, x + w, y + h, (206, 212, 220), (230, 233, 238))
    sx, sy = x + w // 3, y + h // 2
    # cracked shield with keyhole
    c.poly([(sx - 20, sy - 22), (sx + 20, sy - 22), (sx + 20, sy + 2),
            (sx, sy + 28), (sx - 20, sy + 2)], (70, 92, 120))
    c.circle(sx, sy - 6, 5, (20, 24, 32))
    c.poly([(sx - 3, sy - 3), (sx + 3, sy - 3), (sx + 5, sy + 8),
            (sx - 5, sy + 8)], (20, 24, 32))
    crack = [(sx - 14, sy - 20), (sx - 4, sy - 8), (sx - 10, sy + 2),
             (sx, sy + 12), (sx - 4, sy + 24)]
    for i in range(len(crack) - 1):
        c.line(crack[i][0], crack[i][1], crack[i + 1][0], crack[i + 1][1],
               (16, 18, 24), 2)
    # open exit door with light behind
    dx = x + 2 * w // 3
    c.rect(dx - 14, y + 12, dx + 18, y + h - 10, (250, 226, 150))
    c.poly([(dx - 14, y + 12), (dx + 2, y + 20), (dx + 2, y + h - 18),
            (dx - 14, y + h - 10)], (120, 96, 70))
    c.circle(dx - 2, y + h // 2, 2, GOLD)


def scene_iraq(c, x, y, w, h):
    """Story 16: Iraqi forces enter militia town Jurf al-Sakhar."""
    c.gradient(x, y, x + w, y + h, (250, 196, 120), (250, 226, 170))
    base = y + h - 8
    # sunrise
    c.circle(x + w // 2, base - 6, 22, (250, 170, 60))
    # town gate + houses
    c.rect(x + 12, base - 20, x + 44, base, (170, 140, 104))
    c.rect(x + w - 44, base - 16, x + w - 12, base, (170, 140, 104))
    gx = x + w // 2
    c.rect(gx - 22, base - 30, gx - 14, base, (150, 122, 90))
    c.rect(gx + 14, base - 30, gx + 22, base, (150, 122, 90))
    c.poly([(gx - 24, base - 30), (gx + 24, base - 30), (gx, base - 44)],
           (150, 122, 90))
    # flag raised over the gate
    c.line(gx, base - 44, gx, base - 62, (70, 62, 52), 3)
    c.poly([(gx, base - 62), (gx + 22, base - 57), (gx, base - 51)], RED)
    c.rect(gx, base - 62, gx + 22, base - 59, WHITE)
    c.rect(gx, base - 54, gx + 22, base - 51, (30, 30, 34))


# -------------------------------------------------------------- layout -----

M = 24
CW = W - 2 * M

GRID = [
    (scene_peace, "RIVALS SIGN PEACE DEAL"),
    (scene_icj, "COURT: MYANMAR GENOCIDE"),
    (scene_markets, "AI SELL-OFF ROUTS MARKETS"),
    (scene_anthropic, "RECORD IPO STAR SLIDES"),
    (scene_kerch, "KERCH BRIDGE SPAN DOWN"),
    (scene_microsoft, "GLOBAL MICROSOFT OUTAGE"),
    (scene_hormuz, "US BLOCKADE CHOKES HORMUZ"),
    (scene_cop, "COP31 STALLS ON FOSSILS"),
    (scene_haiti, "HAITI RAID KILLS 34"),
    (scene_ukeu, "UK-EU RESET DEAL"),
    (scene_saudi, "SAUDI SHIELD STOPS MISSILES"),
    (scene_greenland, "GREENLAND SECURITY DEAL"),
    (scene_vietnam, "VIETNAM CUTS DEATH PENALTY"),
    (scene_cairncross, "TRUMP FIRES CYBER CHIEF"),
    (scene_iraq, "IRAQ ENTERS MILITIA TOWN"),
]

STRIP = [
    ("AMERICAS", [
        "BUKELE SEEKS THIRD TERM",
        "PERU HIT BY 6.7 QUAKE",
        "COLOMBIA PROTESTS TAXES",
        "LULA SHIELDS AMAZON LAND",
        "SHEINBAUM FLIGHT VIRAL",
    ]),
    ("EUROPE", [
        "EUROPE OFFERS GUARANTEES",
        "DUTCH EMBASSY HIT IN KYIV",
        "HUNGARY LIFTS EU VETO",
        "FRANKFURT BOMB PLOT ARRESTS",
        "ITALY FINES META 805M",
    ]),
    ("MIDDLE EAST", [
        "IRAN: QESHM BLAST DISPOSAL",
        "QATAR MEDIATES HORMUZ TALKS",
    ]),
    ("AFRICA", [
        "ANGOLA BUYS DE BEERS STAKE",
        "BOAT CAPSIZES OFF SENEGAL",
        "KENYA LAST EBOLA CASE OUT",
    ]),
    ("ASIA-PACIFIC", [
        "CYCLONE AKVAN NEARS INDIA",
        "JAPAN QUAKE INJURES 22",
        "TSMC TIGHTENS CHIP CURBS",
        "KOREA CHOLERA AFTER 10 YRS",
        "NICHOLLS 113 LIFTS NZ",
    ]),
]


def masthead(c):
    c.rect(M, 14, W - M, 17, INK)
    c.rect(M, 20, W - M, 21, INK)
    draw_text_centered(c, W // 2, 27, "THE WORLD IN ONE DAY", 3, INK, bold=True)
    draw_text_centered(c, W // 2, 56, "FRIDAY 20 NOVEMBER 2026", 6, INK, bold=True)
    draw_text_centered(c, W // 2, 104, "53 STORIES - EVERY CONTINENT - ONE DAY",
                       2, RED, bold=True)
    c.rect(M, 124, W - M, 125, INK)
    c.rect(M, 127, W - M, 130, INK)


def hero_panel(c):
    x, y, w, h = M, 138, CW, 258
    scene_h = 186
    c.set_clip(x + 2, y + 2, x + w - 2, y + scene_h)
    scene_hero(c, x + 2, y + 2, w - 4, scene_h - 2)
    c.full_clip()
    c.rect(x, y + scene_h, x + w, y + h, DARKRED)
    c.frame(x, y, x + w, y + h, INK, 3)
    draw_text_centered(c, W // 2, y + scene_h + 9, "RUSSIA BOMBARDS UKRAINE",
                       5, WHITE, bold=True)
    draw_text_centered(c, W // 2, y + scene_h + 51,
                       "400+ DRONES - 110 MISSILES - KYIV BRIDGES AND "
                       "POWER GRID HIT - 8 DEAD", 2, (250, 220, 200))


def grid_panel(c, x, y, w, h, scene_fn, label):
    label_h = 40
    c.set_clip(x + 2, y + 2, x + w - 2, y + h - label_h)
    scene_fn(c, x + 2, y + 2, w - 4, h - label_h - 2)
    c.full_clip()
    c.rect(x, y + h - label_h, x + w, y + h, INK)
    lines = wrap_text(label, 15)[:2]
    ly = y + h - label_h + (label_h - len(lines) * 17 + 7) // 2
    for ln in lines:
        draw_text_centered(c, x + w // 2, ly, ln, 2, WHITE, bold=True)
        ly += 17
    c.frame(x, y, x + w, y + h, INK, 2)


def headlines_strip(c):
    y = 790
    draw_text(c, M, y, "MORE OF THE DAY - REGION BY REGION", 2, INK, bold=True)
    tail = "53 STORIES IN ALL"
    draw_text(c, W - M - text_width(tail, 2), y, tail, 2, RED, bold=True)
    c.rect(M, y + 20, W - M, y + 22, INK)
    col_w, gap = 187, 10
    top = y + 30
    for i, (region, items) in enumerate(STRIP):
        cx = M + i * (col_w + gap)
        draw_text(c, cx, top, region, 2, RED, bold=True)
        c.rect(cx, top + 17, cx + col_w, top + 19, RED)
        ly = top + 26
        for item in items:
            for ln in wrap_text(item, col_w // 12):
                if ly + 14 > H - 10:
                    break
                draw_text(c, cx, ly, ln, 2, (44, 44, 54))
                ly += 15
            ly += 3


def draw():
    c = Canvas(W, H, PAPER)
    masthead(c)
    hero_panel(c)
    gx, gy, gw, gh, hgap, vgap = M, 406, 188, 118, 9, 8
    for idx, (scene_fn, label) in enumerate(GRID):
        row, col = divmod(idx, 5)
        grid_panel(c, gx + col * (gw + hgap), gy + row * (gh + vgap),
                   gw, gh, scene_fn, label)
    headlines_strip(c)
    return encode_png(W, H, c.buf)


def render_png_bytes():
    return draw()


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, "entry.png")
    try:
        data = render_png_bytes()
        with open(dest, "wb") as f:
            f.write(data)
    except Exception:
        here = os.path.dirname(os.path.abspath(__file__))
        for cand in (os.path.join(here, "fallback.png"),
                     os.path.join(os.getcwd(), "fallback.png"),
                     "fallback.png"):
            if os.path.exists(cand):
                shutil.copyfile(cand, dest)
                return
        raise


if __name__ == "__main__":
    main()
