"""frontpage.py — generator for the news-image-20261120 entry (v5).

Draws a classic illustrated newspaper front page for Friday
20 November 2026 with Pillow and the Liberation fonts: masthead,
giant serif date, red italic dek, a six-figure numbers strip, region
tabs computed from the story list, three hero panels with drawn
scenes, ten pictured story cards, a dot-matrix world map with the
pictured stories numbered on it, numbered one-line briefs, and a red
date-check box listing the neighbouring days' stories deliberately
left out.

Every figure on the page comes from the verified research dossier
(stories.md + supplement.md). The render is deterministic: the same
story data always produces the same PNG.

Run locally:  python3 frontpage.py   ->  writes entry.png (1024x1024)
"""

import os
from collections import Counter

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- fonts

FONT_DIR = "/usr/share/fonts/truetype/liberation"
SERIF = os.path.join(FONT_DIR, "LiberationSerif-Regular.ttf")
SERIF_B = os.path.join(FONT_DIR, "LiberationSerif-Bold.ttf")
SERIF_I = os.path.join(FONT_DIR, "LiberationSerif-Italic.ttf")
SANS = os.path.join(FONT_DIR, "LiberationSans-Regular.ttf")
SANS_B = os.path.join(FONT_DIR, "LiberationSans-Bold.ttf")


def F(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- colours

PAPER = (246, 241, 226)
PAPER_DARK = (238, 231, 210)
INK = (24, 24, 22)
MUTED = (96, 92, 80)
RED = (176, 35, 24)
DARKRED = (146, 26, 18)
NAVY = (18, 34, 56)
NAVY2 = (26, 48, 76)
SKYLINE = (10, 20, 34)
GOLD = (232, 164, 32)
ORANGE = (244, 120, 32)
DOT = (122, 134, 158)
TAB_COLORS = {
    "Europe": (43, 90, 166),
    "Asia": (178, 62, 32),
    "Middle East": (125, 60, 152),
    "Africa": (30, 132, 73),
    "Americas": (183, 149, 11),
    "Oceania": (40, 116, 166),
    "Global": (93, 109, 126),
}
REGION_ORDER = ["Europe", "Asia", "Middle East", "Africa", "Americas",
                "Oceania", "Global"]

W = 1024
MARGIN = 28
CW = W - 2 * MARGIN  # 968 content width

# ---------------------------------------------------------------- story data
# Pictured stories: (number, place tag, headline, summary, region, scene key)
HEROES = [
    (1, "SOUTH-EAST POLAND · NATO TERRITORY",
     "Russian Missiles Fall Inside Poland",
     "Two missiles and a jet drone from the barrage on Ukraine fell in "
     "border villages; PM Tusk calls it a provocation. (Reuters)",
     "Europe", "poland"),
    (2, "NEW YORK · TOKYO · TAIPEI — MARKETS",
     "AI Sell-Off Turns Into a Worldwide Rout",
     "The S&P 500 fell 3.7% in a seventh straight loss; Nasdaq -5.3%, "
     "Nikkei -5.1%, Taiex -6.2% as the AI trade unravelled. (WSJ)",
     "Global", "markets"),
    (3, "KYIV · UKRAINE — WAR",
     "400 Drones and 110 Missiles Rain on Kyiv",
     "The overnight barrage smashed Dnipro bridges and the power grid, "
     "killed eight and forced nuclear plants to cut output. (Reuters)",
     "Europe", "kyiv"),
]

CARDS = [
    (4, "SHENZHEN · CHINA",
     "Three Rivals Sign Peace Declaration",
     "Trump, Xi and Putin sign a joint peace pledge. (Reuters)",
     "Asia", "peace"),
    (5, "THE HAGUE · MYANMAR",
     "Myanmar Rejects Genocide Ruling",
     "Naypyidaw calls the World Court's genocide finding 'unfair'. (WSJ)",
     "Asia", "court"),
    (6, "GOPALPUR · INDIA — CYCLONE",
     "Cyclone Akvan Comes Ashore",
     "372,000 evacuated to shelters as the storm hit Odisha. (PTI)",
     "Asia", "cyclone"),
    (7, "ANTALYA · TÜRKIYE — CLIMATE",
     "Climate Talks Stall Over Fossils",
     "Fossil-fuel deadlock as the final day ends with no deal. (Reuters)",
     "Asia", "cop"),
    (8, "BRUSSELS · BELGIUM",
     "Britain and EU Agree Reset Deal",
     "Food, carbon markets and 100,000 youth visas a year. (Reuters)",
     "Europe", "ukeu"),
    (9, "TALLINN · ESTONIA — SECURITY",
     "Estonia Shuts Russian Road Border",
     "All five road crossings close from 1 Dec for six months. (Reuters)",
     "Europe", "estonia"),
    (10, "STRAIT OF HORMUZ",
     "US Blockade Chokes Iran Strait",
     "Trump demands a 'real deal' from Tehran; Qatar mediates. (Reuters)",
     "Middle East", "hormuz"),
    (11, "PORT-AU-PRINCE · HAITI",
     "Police Raid Kills 34 in Haiti",
     "Police kill 34 gang suspects in a major raid. (Open Chronicle)",
     "Americas", "haiti"),
    (12, "WELLINGTON · NEW ZEALAND — CRICKET",
     "Phillips' 118 Lifts New Zealand",
     "Phillips hit 118; Nicholls made 175 not out vs India. (ESPNcricinfo)",
     "Oceania", "cricket"),
    (13, "TOKYO · JAPAN — ECONOMY",
     "Japan's Inflation Rises to 2.3%",
     "October prices rose 2.3%, fastest in a year. (Statistics Bureau)",
     "Asia", "japan"),
]

# Briefs: (number, text, region) — one line each, source named in the text.
BRIEFS = [
    (14, "Lviv — Station strike kills two (AFP)", "Europe"),
    (15, "New York — Bitcoin under $60,000 since July (Reuters)", "Americas"),
    (16, "New York — Nvidia plunges 14%, SEC probe (WSJ)", "Americas"),
    (17, "Tokyo — SoftBank closes 14.5% lower (CNBC)", "Asia"),
    (18, "New York — Anthropic -8.5% after $81bn debut (Reuters)", "Americas"),
    (19, "Berlin — Youth strike sweeps 25 countries (Reuters)", "Europe"),
    (20, "Rome — General strike hits 100+ cities (Reuters)", "Europe"),
    (21, "Turkana — Kenya drilling starts, oil due 1 Dec (QNC News)", "Africa"),
    (22, "Riyadh — Saudi shields stop Houthi missiles (Reuters)", "Middle East"),
    (23, "Hanoi — Death penalty cut for six crimes (AFP)", "Asia"),
    (24, "Washington — Trump fires cyber chief (Reuters)", "Americas"),
    (25, "Nuuk — Denmark seals Greenland security deal (AP)", "Europe"),
    (26, "Kyiv — Dutch embassy damaged by debris (Informed Clearly)", "Europe"),
    (27, "Kharkiv — 14 settlements retaken (Meanwhile in Ukraine)", "Europe"),
    (28, "Qeshm — Blast was munitions disposal, Iran says (Reuters)", "Middle East"),
    (29, "Taipei — TSMC tightens China chip curbs (Reuters)", "Asia"),
    (30, "Seoul — First cholera case in a decade (Global Affairs News)", "Asia"),
    (31, "Tokyo — Japan funds nuclear-sub study (Yonhap)", "Asia"),
    (32, "Luanda — Angola pays $180m for 10% of De Beers (Reuters)", "Africa"),
    (33, "Dakar — Migrant boat capsizes (Global Affairs News)", "Africa"),
    (34, "Canberra — Xi hails Australia ties turnaround (Reuters)", "Oceania"),
    (35, "Rarotonga — Cyclone Xavier hits Cooks (Trending World)", "Oceania"),
    (36, "Lima — 6.7 quake hits central Peru (USGS)", "Americas"),
]

NUMBERS = [
    ("400+", "DRONES FIRED AT UKRAINE IN A SINGLE NIGHT"),
    ("372,000", "PEOPLE SHELTERED FROM CYCLONE AKVAN"),
    ("-3.7%", "THE S&P 500 — A SEVENTH STRAIGHT LOSS"),
    ("100,000", "YOUTH VISAS A YEAR IN THE UK-EU DEAL"),
    ("+2.3%", "JAPAN'S OCTOBER INFLATION RATE"),
    ("118", "RUNS BY GLENN PHILLIPS AGAINST INDIA"),
]

DEK = ("Missiles fall inside Poland · the AI trade routs the world's "
       "markets · Kyiv's bridges burn on peace-pledge day")

DATE_CHECK = (
    "DATE CHECK — Deliberately left out as other days' news: the World "
    "Court's genocide ruling itself (Thursday) · Anthropic's record "
    "market debut (Thursday) · Bukele's third-term filing · Ukraine's "
    "third hit on the Kerch bridge · Mongolia's resignation vote "
    "(Thursday) · the US-Venezuela military deal (Wednesday)."
)

# Dot-matrix world map: one character per dot position, '#' = land.
MAP_ROWS = [
    "                                               ",
    "  #####         #######################        ",
    " #########     #########################       ",
    " ##########    ##########################      ",
    "  #########     ########################       ",
    "   ########      ######################        ",
    "    ######        ####################         ",
    "     ####          ##################           ",
    "     ####           ################            ",
    "      ###            ##############             ",
    "      ####            ############              ",
    "       #####           ##########               ",
    "       ######           ########        ##      ",
    "        ####             ######         ####    ",
    "        ###               ####           ##     ",
    "        ##                ##                     ",
    "         #                          #######     ",
    "                                   ########     ",
    "                                    #####       ",
    "                                               ",
]

# Badge positions for pictured stories 1-13, as fractions of the map box.
BADGES = {
    1: (0.478, 0.20),   # Poland
    2: (0.105, 0.28),   # Markets — New York
    3: (0.528, 0.25),   # Kyiv
    4: (0.790, 0.44),   # Shenzhen
    5: (0.730, 0.49),   # Myanmar
    6: (0.660, 0.53),   # Akvan — Odisha
    7: (0.548, 0.35),   # Antalya
    8: (0.448, 0.145),  # Brussels
    9: (0.508, 0.095),  # Estonia — Tallinn
    10: (0.600, 0.45),  # Hormuz
    11: (0.150, 0.47),  # Haiti
    12: (0.965, 0.90),  # Wellington
    13: (0.925, 0.26),  # Japan
}

ALL_STORIES = HEROES + CARDS + [(n, "", "", "", r, "") for n, _t, r in BRIEFS]
TOTAL = len(HEROES) + len(CARDS) + len(BRIEFS)
REGION_COUNTS = Counter(s[4] for s in ALL_STORIES)

# ---------------------------------------------------------------- helpers


def wrap(draw, text, font, width):
    """Greedy word-wrap to a pixel width; returns a list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if draw.textlength(trial, font=font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, text, font, fill, width, leading, max_lines=None):
    lines = wrap(draw, text, font, width)
    if max_lines:
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        draw.text((x, y + i * leading), ln, font=font, fill=fill)
    return y + len(lines) * leading


def centered(draw, cx, y, text, font, fill):
    w_ = draw.textlength(text, font=font)
    draw.text((cx - w_ / 2, y), text, font=font, fill=fill)
    return w_


def starburst(draw, cx, cy, r, fill=ORANGE, core=GOLD):
    import math
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)
    draw.ellipse([cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32],
                 fill=core)


def badge(draw, cx, cy, num, r=10):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED,
                 outline=(255, 255, 255), width=2)
    f = F(SANS_B, 11 if num < 10 else 10)
    t = str(num)
    w_ = draw.textlength(t, font=f)
    draw.text((cx - w_ / 2, cy - 6), t, font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------- scenes


def scene_poland(d, x, y, w, h):
    """Night village, missile trails and bursts, one drone."""
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    # village silhouette with lit windows
    base = y + h
    houses = [(0.04, 0.30), (0.16, 0.22), (0.30, 0.34), (0.62, 0.26),
              (0.76, 0.32), (0.88, 0.24)]
    for fx, fh in houses:
        hx, hw = x + fx * w, 0.10 * w
        top = base - fh * h
        d.rectangle([hx, top, hx + hw, base], fill=SKYLINE)
        d.polygon([(hx - 3, top), (hx + hw / 2, top - 0.16 * h),
                   (hx + hw + 3, top)], fill=SKYLINE)
        for wy in (0.35, 0.6):
            for wx in (0.25, 0.6):
                d.rectangle([hx + wx * hw, top + wy * fh * h,
                             hx + wx * hw + 3, top + wy * fh * h + 4],
                            fill=GOLD)
    # missile trails with bursts
    for fx, fy, tx, ty in [(0.10, 0.06, 0.30, 0.52), (0.48, 0.02, 0.60, 0.44),
                           (0.86, 0.05, 0.74, 0.50)]:
        d.line([x + fx * w, y + fy * h, x + tx * w, y + ty * h],
               fill=(220, 226, 235), width=2)
        starburst(d, x + tx * w, y + ty * h, 11)
    # drone (X shape) top right
    dx, dy = x + 0.93 * w, y + 0.30 * h
    d.line([dx - 6, dy - 5, dx + 6, dy + 5], fill=(200, 60, 50), width=2)
    d.line([dx - 6, dy + 5, dx + 6, dy - 5], fill=(200, 60, 50), width=2)
    d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(235, 235, 235))


def scene_markets(d, x, y, w, h):
    """Dark chart panel, red plunge line, labelled closes."""
    d.rectangle([x, y, x + w, y + h], fill=(8, 12, 20))
    for i in range(1, 5):
        gy = y + h * i / 5
        d.line([x, gy, x + w, gy], fill=(38, 48, 66), width=1)
    for i in range(1, 6):
        gx = x + w * i / 6
        d.line([gx, y, gx, y + h], fill=(30, 40, 58), width=1)
    pts = [(x + 0.03 * w, y + 0.22 * h), (x + 0.22 * w, y + 0.30 * h),
           (x + 0.42 * w, y + 0.46 * h), (x + 0.62 * w, y + 0.60 * h),
           (x + 0.82 * w, y + 0.74 * h), (x + 0.97 * w, y + 0.86 * h)]
    d.line(pts, fill=(232, 48, 40), width=3)
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 120, 100))
    f = F(SANS_B, 12)
    d.text((x + 0.16 * w, y + 0.10 * h), "S&P -3.7%", font=f,
           fill=(255, 150, 130))
    d.text((x + 0.40 * w, y + 0.24 * h), "NASDAQ -5.3%", font=f,
           fill=(255, 150, 130))
    d.text((x + 0.66 * w, y + 0.44 * h), "NIKKEI -5.1%", font=f,
           fill=(255, 150, 130))
    d.text((x + 0.74 * w, y + 0.06 * h), "TAIEX -6.2%", font=f,
           fill=(255, 150, 130))


def scene_kyiv(d, x, y, w, h):
    """Skyline, river with three bridges, trails and bursts."""
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    base = y + h * 0.78
    # skyline
    for fx, fw, fh in [(0.02, 0.10, 0.42), (0.14, 0.08, 0.55),
                       (0.24, 0.11, 0.36), (0.68, 0.09, 0.50),
                       (0.79, 0.10, 0.40), (0.90, 0.08, 0.55)]:
        bx, bw = x + fx * w, fw * w
        top = base - fh * h
        d.rectangle([bx, top, bx + bw, base], fill=SKYLINE)
        for wy in (0.3, 0.55, 0.78):
            d.rectangle([bx + 0.3 * bw, top + wy * fh * h,
                         bx + 0.3 * bw + 3, top + wy * fh * h + 4], fill=GOLD)
    # river
    d.rectangle([x, base, x + w, y + h], fill=(24, 84, 110))
    for i in range(7):
        rx = x + (0.06 + 0.13 * i) * w
        d.line([rx, y + h * 0.90, rx + 0.05 * w, y + h * 0.90],
               fill=(90, 170, 195), width=2)
    # three bridges
    for fx in (0.16, 0.47, 0.78):
        bx = x + fx * w
        d.line([bx - 0.11 * w, base, bx + 0.11 * w, base],
               fill=(200, 205, 215), width=3)
        d.line([bx, base - 0.16 * h, bx, base], fill=(200, 205, 215), width=2)
        d.line([bx - 0.11 * w, base, bx, base - 0.16 * h], fill=(160, 168, 180),
               width=1)
        d.line([bx + 0.11 * w, base, bx, base - 0.16 * h], fill=(160, 168, 180),
               width=1)
    # trails + bursts
    for fx, fy, tx, ty in [(0.08, 0.04, 0.24, 0.40), (0.55, 0.02, 0.50, 0.36),
                           (0.92, 0.05, 0.80, 0.42)]:
        d.line([x + fx * w, y + fy * h, x + tx * w, y + ty * h],
               fill=(220, 226, 235), width=2)
        starburst(d, x + tx * w, y + ty * h, 11)


def _banner(d, x, y, w, h, fill=NAVY2):
    d.rectangle([x, y, x + w, y + h], fill=fill)


def scene_peace(d, x, y, w, h):
    _banner(d, x, y, w, h)
    cy = y + h / 2
    # dove: body ellipse + wing triangle + head
    d.ellipse([x + 0.36 * w, cy - 7, x + 0.60 * w, cy + 6], fill=(240, 240, 240))
    d.polygon([(x + 0.42 * w, cy - 4), (x + 0.52 * w, cy - 15),
               (x + 0.58 * w, cy - 3)], fill=(225, 228, 232))
    d.ellipse([x + 0.58 * w, cy - 10, x + 0.65 * w, cy - 3], fill=(240, 240, 240))
    d.polygon([(x + 0.65 * w, cy - 7), (x + 0.70 * w, cy - 5),
               (x + 0.65 * w, cy - 3)], fill=GOLD)
    # three flag blocks
    for i, c in enumerate([(200, 60, 50), (240, 240, 240), (60, 110, 200)]):
        fx = x + (0.06 + 0.13 * i) * w
        d.rectangle([fx, cy - 10, fx + 0.09 * w, cy + 4], fill=c)
        d.line([fx, cy - 12, fx, cy + 12], fill=(200, 200, 200), width=1)
    fx = x + 0.80 * w
    d.rectangle([fx, cy - 10, fx + 0.09 * w, cy + 4], fill=(220, 180, 40))
    d.line([fx, cy - 12, fx, cy + 12], fill=(200, 200, 200), width=1)


def scene_court(d, x, y, w, h):
    _banner(d, x, y, w, h)
    cx, cy = x + w / 2, y + h / 2
    # pillars
    for dx in (-26, -9, 9, 26):
        d.rectangle([cx + dx - 3, cy - 8, cx + dx + 3, cy + 10], fill=(225, 222, 210))
    d.polygon([(cx - 36, cy - 8), (cx, cy - 18), (cx + 36, cy - 8)],
              fill=(225, 222, 210))
    d.rectangle([cx - 38, cy + 10, cx + 38, cy + 13], fill=(225, 222, 210))
    # red X over the right side
    d.line([cx + 14, cy - 14, cx + 34, cy + 12], fill=(232, 60, 45), width=4)
    d.line([cx + 34, cy - 14, cx + 14, cy + 12], fill=(232, 60, 45), width=4)


def scene_cyclone(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(16, 60, 84))
    import math
    cx, cy = x + 0.30 * w, y + h / 2
    for k in range(3):
        pts = []
        for t in range(0, 26):
            ang = 0.55 * t + k * 2.1
            rad = 2.2 * t / 3.2
            if rad > 15:
                break
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang) * 0.8))
        if len(pts) > 1:
            d.line(pts, fill=(235, 240, 245), width=2)
    # coastline + houses on the right
    d.polygon([(x + 0.55 * w, y + h), (x + 0.72 * w, y + 0.45 * h),
               (x + w, y + 0.45 * h), (x + w, y + h)], fill=(30, 90, 60))
    for fx in (0.78, 0.88):
        hx = x + fx * w
        d.rectangle([hx, y + h - 12, hx + 10, y + h - 4], fill=(240, 235, 220))
        d.polygon([(hx - 2, y + h - 12), (hx + 5, y + h - 17), (hx + 12, y + h - 12)],
                  fill=(150, 60, 40))


def scene_cop(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(40, 44, 40))
    cy = y + h / 2
    # chimneys with smoke
    for fx in (0.10, 0.22):
        cx0 = x + fx * w
        d.rectangle([cx0, cy - 2, cx0 + 10, cy + 14], fill=(120, 120, 118))
        d.ellipse([cx0 - 2, cy - 14, cx0 + 8, cy - 5], fill=(170, 170, 168))
        d.ellipse([cx0 + 4, cy - 19, cx0 + 15, cy - 10], fill=(150, 150, 148))
    # big leaf
    d.polygon([(x + 0.55 * w, cy + 12), (x + 0.68 * w, cy - 12),
               (x + 0.86 * w, cy - 10), (x + 0.72 * w, cy + 12)],
              fill=(52, 168, 84))
    d.line([x + 0.57 * w, cy + 11, x + 0.84 * w, cy - 9], fill=(30, 110, 55),
           width=2)
    # knot between
    d.ellipse([x + 0.40 * w, cy - 6, x + 0.50 * w, cy + 6], outline=(220, 200, 150),
              width=3)


def scene_ukeu(d, x, y, w, h):
    _banner(d, x, y, w, h)
    cy = y + h / 2
    # EU flag block
    fx = x + 0.14 * w
    d.rectangle([fx, cy - 12, fx + 0.26 * w, cy + 12], fill=(30, 60, 160))
    import math
    for i in range(8):
        ang = 2 * math.pi * i / 8
        sx, sy = fx + 0.13 * w + 8 * math.cos(ang), cy + 8 * math.sin(ang)
        d.ellipse([sx - 1.6, sy - 1.6, sx + 1.6, sy + 1.6], fill=GOLD)
    # UK flag block (simplified cross)
    fx2 = x + 0.58 * w
    d.rectangle([fx2, cy - 12, fx2 + 0.26 * w, cy + 12], fill=(35, 45, 120))
    d.rectangle([fx2 + 0.10 * w, cy - 12, fx2 + 0.16 * w, cy + 12], fill=(240, 240, 240))
    d.rectangle([fx2, cy - 3, fx2 + 0.26 * w, cy + 3], fill=(240, 240, 240))
    d.rectangle([fx2 + 0.115 * w, cy - 12, fx2 + 0.145 * w, cy + 12], fill=(200, 40, 40))
    d.rectangle([fx2, cy - 1.5, fx2 + 0.26 * w, cy + 1.5], fill=(200, 40, 40))


def scene_estonia(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(30, 40, 52))
    cy = y + h / 2
    # road with barrier
    d.polygon([(x + 0.08 * w, y + h), (x + 0.42 * w, cy + 2),
               (x + 0.58 * w, cy + 2), (x + 0.92 * w, y + h)], fill=(70, 74, 80))
    d.line([x + 0.485 * w, y + h, x + 0.5 * w, cy + 3], fill=(230, 230, 230), width=2)
    # barrier arm across
    bx = x + 0.30 * w
    d.rectangle([bx, cy - 14, bx + 4, cy + 12], fill=(200, 200, 200))
    for i in range(5):
        c = (220, 50, 40) if i % 2 == 0 else (240, 240, 240)
        d.rectangle([bx + 4 + i * 0.075 * w, cy - 13 + i * 1.6,
                     bx + 4 + (i + 1) * 0.075 * w, cy - 8 + i * 1.6], fill=c)


def scene_hormuz(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(14, 52, 74))
    cy = y + h / 2
    # waves
    for r_ in range(2):
        for i in range(6):
            wx = x + (0.05 + 0.15 * i) * w
            wy = y + h - 8 - r_ * 7
            d.arc([wx, wy - 4, wx + 14, wy + 4], 0, 180, fill=(110, 190, 215), width=2)
    # warship left
    d.polygon([(x + 0.06 * w, cy + 4), (x + 0.34 * w, cy + 4),
               (x + 0.29 * w, cy + 10), (x + 0.10 * w, cy + 10)], fill=(90, 100, 112))
    d.rectangle([x + 0.14 * w, cy - 4, x + 0.24 * w, cy + 4], fill=(90, 100, 112))
    d.rectangle([x + 0.17 * w, cy - 10, x + 0.20 * w, cy - 4], fill=(90, 100, 112))
    # tanker right
    d.polygon([(x + 0.60 * w, cy + 4), (x + 0.94 * w, cy + 4),
               (x + 0.89 * w, cy + 10), (x + 0.64 * w, cy + 10)], fill=(150, 70, 50))
    d.rectangle([x + 0.66 * w, cy - 3, x + 0.86 * w, cy + 4], fill=(170, 84, 60))


def scene_haiti(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(18, 66, 60))
    cy = y + h / 2
    # island + palm
    d.ellipse([x + 0.08 * w, cy + 4, x + 0.52 * w, cy + 16], fill=(214, 186, 120))
    px = x + 0.28 * w
    d.line([px, cy + 6, px + 3, cy - 10], fill=(120, 84, 40), width=3)
    import math
    for a in (200, 250, 300, 340):
        ex = px + 3 + 13 * math.cos(math.radians(a))
        ey = cy - 10 + 8 * math.sin(math.radians(a))
        d.line([px + 3, cy - 10, ex, ey], fill=(52, 168, 84), width=2)
    # shield
    sx = x + 0.68 * w
    d.polygon([(sx, cy - 13), (sx + 16, cy - 9), (sx + 16, cy + 2),
               (sx + 8, cy + 14), (sx, cy + 2)], fill=(43, 90, 166))
    d.polygon([(sx, cy - 13), (sx - 0, cy + 2), (sx + 8, cy + 14),
               (sx + 8, cy - 11)], fill=(58, 110, 190))
    d.text((sx + 3, cy - 6), "34", font=F(SANS_B, 10), fill=(255, 255, 255))


def scene_cricket(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(24, 84, 40))
    cy = y + h / 2
    # pitch strip
    d.rectangle([x + 0.30 * w, cy - 3, x + 0.78 * w, cy + 5], fill=(216, 192, 130))
    # stumps
    for fx in (0.33, 0.72):
        for s in range(3):
            sx = x + fx * w + s * 4
            d.line([sx, cy - 8, sx, cy + 3], fill=(240, 230, 200), width=2)
    # bat + ball
    d.line([x + 0.52 * w, cy + 8, x + 0.58 * w, cy - 8], fill=(226, 200, 150), width=4)
    d.ellipse([x + 0.63 * w, cy - 12, x + 0.63 * w + 7, cy - 5], fill=(200, 40, 40))
    d.arc([x + 0.60 * w, cy - 16, x + 0.80 * w, cy + 2], 200, 330,
          fill=(255, 255, 255), width=1)


def scene_japan(d, x, y, w, h):
    _banner(d, x, y, w, h, fill=(52, 30, 34))
    cy = y + h / 2
    # rising price steps + yen coin
    pts = [(x + 0.08 * w, cy + 10), (x + 0.24 * w, cy + 10), (x + 0.24 * w, cy + 2),
           (x + 0.40 * w, cy + 2), (x + 0.40 * w, cy - 6), (x + 0.56 * w, cy - 6)]
    d.line(pts, fill=(255, 170, 60), width=3)
    d.polygon([(x + 0.56 * w, cy - 11), (x + 0.56 * w, cy - 1),
               (x + 0.65 * w, cy - 6)], fill=(255, 170, 60))
    cx = x + 0.82 * w
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=GOLD)
    d.text((cx - 5, cy - 7), "¥", font=F(SANS_B, 13), fill=(120, 80, 10))


SCENES = {
    "poland": scene_poland, "markets": scene_markets, "kyiv": scene_kyiv,
    "peace": scene_peace, "court": scene_court, "cyclone": scene_cyclone,
    "cop": scene_cop, "ukeu": scene_ukeu, "estonia": scene_estonia,
    "hormuz": scene_hormuz, "haiti": scene_haiti, "cricket": scene_cricket,
    "japan": scene_japan,
}


# ---------------------------------------------------------------- page


def draw_fit(d, x, y, text, path, size, max_width, fill, min_size=8):
    """Draw text, shrinking the font until it fits max_width."""
    s = size
    while s > min_size and d.textlength(text, font=F(path, s)) > max_width:
        s -= 1
    d.text((x, y), text, font=F(path, s), fill=fill)
    return s


def build():
    img = Image.new("RGB", (W, W), PAPER)
    d = ImageDraw.Draw(img)

    # ---- top bar
    d.text((MARGIN, 13), "THE WORLD IN ONE DAY", font=F(SANS_B, 17), fill=RED)
    right = f"{TOTAL} STORIES · 7 REGIONS · EVERY ONE DATED FRIDAY 20 NOVEMBER 2026"
    rf = F(SANS, 11)
    d.text((W - MARGIN - d.textlength(right, font=rf), 17), right, font=rf,
           fill=INK)
    d.line([MARGIN, 40, W - MARGIN, 40], fill=INK, width=3)
    d.line([MARGIN, 45, W - MARGIN, 45], fill=INK, width=1)

    # ---- giant date + dek
    centered(d, W / 2, 52, "Friday 20 November 2026", F(SERIF_B, 66), INK)
    centered(d, W / 2, 128, DEK, F(SERIF_I, 17), RED)
    d.line([MARGIN, 156, W - MARGIN, 156], fill=INK, width=1)

    # ---- numbers strip
    cell = CW / 6
    for i, (fig, cap) in enumerate(NUMBERS):
        cx = MARGIN + cell * i + cell / 2
        centered(d, cx, 164, fig, F(SERIF_B, 33), INK)
        for j, ln in enumerate(wrap(d, cap, F(SANS, 10), cell - 14)):
            centered(d, cx, 204 + j * 12, ln, F(SANS, 10), MUTED)
        if i:
            d.line([MARGIN + cell * i, 166, MARGIN + cell * i, 224],
                   fill=(190, 182, 160), width=1)
    d.line([MARGIN, 230, W - MARGIN, 230], fill=INK, width=1)

    # ---- region tabs (counts computed from the story list)
    labels = [(r, f"{r.upper()} {REGION_COUNTS[r]}") for r in REGION_ORDER]
    tf = F(SANS_B, 12)
    widths = [d.textlength(t, font=tf) + 20 for _r, t in labels]
    gap = (CW - sum(widths)) / (len(labels) - 1)
    tx = float(MARGIN)
    for (r, t), tw in zip(labels, widths):
        d.rectangle([tx, 238, tx + tw, 262], fill=TAB_COLORS[r])
        centered(d, tx + tw / 2, 244, t, tf, (255, 255, 255))
        tx += tw + gap

    # ---- heroes
    hy = 274
    hero_w = 316
    for i, (num, tag, head, summ, _reg, scene) in enumerate(HEROES):
        hx = MARGIN + i * (hero_w + 10)
        SCENES[scene](d, hx, hy, hero_w, 96)
        badge(d, hx + 15, hy + 15, num, r=11)
        d.text((hx, hy + 102), tag, font=F(SANS_B, 11), fill=RED)
        text_block(d, hx, hy + 120, head, F(SERIF_B, 28), INK, hero_w, 30,
                   max_lines=2)
        text_block(d, hx, hy + 184, summ, F(SERIF, 13), INK, hero_w, 16,
                   max_lines=3)
    d.line([MARGIN, 512, W - MARGIN, 512], fill=INK, width=1)

    # ---- cards, two rows of five
    card_w, card_h = 187, 118
    for i, (num, tag, head, summ, _reg, scene) in enumerate(CARDS):
        cx0 = MARGIN + (i % 5) * (card_w + 8)
        cy0 = 522 + (i // 5) * 124
        SCENES[scene](d, cx0, cy0, card_w, 36)
        badge(d, cx0 + 10, cy0 + 10, num, r=8)
        draw_fit(d, cx0, cy0 + 41, tag, SANS_B, 10, card_w, RED)
        text_block(d, cx0, cy0 + 55, head, F(SERIF_B, 15), INK, card_w, 17,
                   max_lines=2)
        text_block(d, cx0, cy0 + 91, summ, F(SERIF, 12), INK, card_w, 14,
                   max_lines=2)

    # ---- bottom band: map (left) + briefs (right)
    by = 774
    d.text((MARGIN, by), "WHERE IT HAPPENED", font=F(SANS_B, 12), fill=INK)
    map_x, map_y, map_w = MARGIN, by + 24, 328
    rows, cols = len(MAP_ROWS), len(MAP_ROWS[0])
    pitch = 7.0
    for ri, row in enumerate(MAP_ROWS):
        for ci, ch in enumerate(row):
            if ch == "#":
                cxp = map_x + ci * pitch + pitch / 2
                cyp = map_y + ri * pitch + pitch / 2
                d.ellipse([cxp - 2.6, cyp - 2.6, cxp + 2.6, cyp + 2.6],
                          fill=DOT)
    for num, (fx, fy) in BADGES.items():
        badge(d, map_x + fx * map_w, map_y + fy * rows * pitch, num, r=9)
    text_block(d, MARGIN, map_y + rows * pitch + 8,
               "Each number is the pictured story of that number on this page.",
               F(SERIF_I, 10), MUTED, map_w, 12)

    bx = 372
    d.text((bx, by), f"ALSO ON FRIDAY — {len(BRIEFS)} MORE STORIES",
           font=F(SANS_B, 13), fill=INK)
    bf = F(SANS, 12)
    col_w, pitch_b = 300, 15
    for i, (num, text, _reg) in enumerate(BRIEFS):
        col = 0 if i < 12 else 1
        row_i = i if i < 12 else i - 12
        x0 = bx + col * (col_w + 12)
        y0 = by + 16 + row_i * pitch_b
        label = f"{num} "
        d.text((x0, y0), label, font=F(SANS_B, 12), fill=RED)
        off = d.textlength(label, font=F(SANS_B, 12))
        draw_fit(d, x0 + off, y0, text, SANS, 12, col_w - off, INK,
                 min_size=10)

    # ---- date-check box
    box_y = 970
    d.rectangle([MARGIN, box_y, W - MARGIN, box_y + 31], fill=(250, 238, 231),
                outline=RED, width=2)
    text_block(d, MARGIN + 8, box_y + 5, DATE_CHECK, F(SERIF, 11), DARKRED,
               CW - 16, 12, max_lines=2)

    # ---- footer
    foot = ("Every story here happened, or was first reported, on Friday "
            "20 November 2026. Officials' counts are attributed.")
    d.text((MARGIN, 1005), foot, font=F(SANS, 9), fill=MUTED)
    tail = "Sources named beside each story · original drawings"
    tf2 = F(SANS, 9)
    d.text((W - MARGIN - d.textlength(tail, font=tf2), 1005), tail, font=tf2,
           fill=MUTED)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    img.save(out, format="PNG", optimize=True)
    return out


if __name__ == "__main__":
    print(build())
