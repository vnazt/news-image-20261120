#!/usr/bin/env python3
"""frontpage.py -- generator for the news-image-20261120 entry (V4).

Draws a complete illustrated newspaper front page for Friday 20 November 2026
with Pillow and the Liberation fonts, and writes entry.png (1024x1024) next
to this file. Deterministic: same data, same bytes, every run.

Layout: masthead + giant serif date, red italic dek, six-figure numbers
strip (six different stories), region tabs with counts computed from the
story list, three numbered hero panels, ten numbered mid cards, a dot-matrix
world map with numbered badges, numbered one-line briefs with real source
names, a red date-check box, and attribution footers.

Legibility floors: hero headlines 28px, hero summaries 13px, card headlines
15px, card text 12px, briefs 12px on a 15px pitch. If the briefs ever
overflow their band, briefs are cut from the bottom -- type never shrinks.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

FONT_DIR = "/usr/share/fonts/truetype/liberation"
SERIF = os.path.join(FONT_DIR, "LiberationSerif-Regular.ttf")
SERIF_B = os.path.join(FONT_DIR, "LiberationSerif-Bold.ttf")
SERIF_I = os.path.join(FONT_DIR, "LiberationSerif-Italic.ttf")
SANS = os.path.join(FONT_DIR, "LiberationSans-Regular.ttf")
SANS_B = os.path.join(FONT_DIR, "LiberationSans-Bold.ttf")

_cache = {}


def F(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

PAPER = (247, 243, 233)
INK = (26, 25, 28)
FAINT = (112, 106, 94)
RED = (176, 30, 30)
RED_SOFT = (250, 238, 235)
NAVY = (15, 23, 43)
NAVY2 = (24, 36, 62)
SKY = (31, 48, 84)
ORANGE = (243, 146, 44)
GOLD = (214, 168, 74)
TEAL = (28, 92, 102)
WHITE = (250, 249, 245)

REGION_COLORS = {
    "Europe": (38, 54, 96),
    "Asia": (176, 30, 30),
    "Americas": (28, 92, 102),
    "Middle East": (178, 108, 30),
    "Africa": (52, 110, 54),
    "Oceania": (104, 62, 140),
    "Global": (96, 92, 84),
}

# ---------------------------------------------------------------------------
# Story data -- every fact and figure comes from the verified dossier
# (~/workspace/makefun/newsimg20/research/stories.md). Nothing else.
# ---------------------------------------------------------------------------

HEROES = [
    {
        "n": 1,
        "tag": "SOUTH-EAST POLAND \u00b7 NATO TERRITORY",
        "headline": "Russian Missiles Fall Inside Poland",
        "summary": "Two missiles from the barrage fell in border "
                   "villages inside Poland, a NATO member. (Reuters)",
        "region": "Europe",
        "scene": "poland",
    },
    {
        "n": 2,
        "tag": "TOKYO \u00b7 SEOUL \u00b7 TAIPEI \u00b7 NEW YORK",
        "headline": "AI Sell-Off Turns Into a Worldwide Rout",
        "summary": "The Nikkei fell about 5% and Kospi and Taiwan "
                   "5\u20136% as Asian shares headed for their worst week "
                   "since 2020. (Reuters)",
        "region": "Global",
        "scene": "markets",
    },
    {
        "n": 3,
        "tag": "KYIV \u00b7 UKRAINE",
        "headline": "400 Drones and 110 Missiles Rain on Kyiv",
        "summary": "More than 400 drones and 110 missiles smashed the "
                   "Dnipro bridges and power grid, killing eight. "
                   "(Reuters)",
        "region": "Europe",
        "scene": "kyiv",
    },
]

CARDS = [
    {
        "n": 4,
        "tag": "SHENZHEN \u00b7 CHINA",
        "headline": "Three Rivals Sign Peace Declaration",
        "summary": "Trump, Xi and Putin sign a joint declaration after "
                   "their first-ever three-way summit. (Reuters)",
        "region": "Asia",
        "scene": "peace",
    },
    {
        "n": 5,
        "tag": "THE HAGUE \u00b7 MYANMAR",
        "headline": "Myanmar Rejects Genocide Ruling",
        "summary": "Myanmar dismisses the World Court's first-ever "
                   "genocide finding as \u201cunfair\u201d. (WSJ)",
        "region": "Asia",
        "scene": "court",
    },
    {
        "n": 6,
        "tag": "ODISHA \u00b7 INDIA",
        "headline": "Cyclone Akvan Nears Odisha Coast",
        "summary": "Indian Railways cancels trains as the cyclone "
                   "closes on the Odisha\u2013Andhra coast. "
                   "(Careerindia)",
        "region": "Asia",
        "scene": "cyclone",
    },
    {
        "n": 7,
        "tag": "ANTALYA \u00b7 T\u00dcRKIYE",
        "headline": "Climate Talks Stall Over Fossils",
        "summary": "Negotiators deadlock over fossil fuels in the "
                   "draft deal as the final day ends. "
                   "(Global Affairs News)",
        "region": "Europe",
        "scene": "cop",
    },
    {
        "n": 8,
        "tag": "BRUSSELS \u00b7 BELGIUM",
        "headline": "Britain and EU Agree Reset Deal",
        "summary": "A three-part reset \u2014 food trade, youth mobility "
                   "and carbon markets. (Reuters)",
        "region": "Europe",
        "scene": "ukeu",
    },
    {
        "n": 9,
        "tag": "STRAIT OF HORMUZ",
        "headline": "US Blockade Chokes Iran Strait",
        "summary": "Trump demands a \u201creal deal\u201d from Tehran "
                   "and rejects its terms; Qatar mediates. (Reuters)",
        "region": "Middle East",
        "scene": "hormuz",
    },
    {
        "n": 10,
        "tag": "PORT-AU-PRINCE \u00b7 HAITI",
        "headline": "Police Raid Kills 34 in Haiti",
        "summary": "National police kill 34 suspected gang members in "
                   "a major operation. (Open Chronicle)",
        "region": "Americas",
        "scene": "haiti",
    },
    {
        "n": 11,
        "tag": "RIYADH \u00b7 SAUDI ARABIA",
        "headline": "Saudi Shields Stop Houthi Missiles",
        "summary": "Air defences intercept Houthi missiles over Riyadh "
                   "in a day of emergency alerts; coalition jets strike "
                   "Hodeidah. (Reuters)",
        "region": "Middle East",
        "scene": "saudi",
    },
    {
        "n": 12,
        "tag": "WORLDWIDE \u00b7 TECH",
        "headline": "Microsoft Outage Darkens Offices",
        "summary": "A roughly 24-hour failure knocks out Outlook, "
                   "Teams and Copilot in dozens of countries. (Reuters)",
        "region": "Global",
        "scene": "microsoft",
    },
    {
        "n": 13,
        "tag": "WELLINGTON \u00b7 NEW ZEALAND",
        "headline": "Nicholls' 113 Lifts New Zealand",
        "summary": "Henry Nicholls scores an unbeaten 113 against "
                   "India in the first Test at Wellington. "
                   "(Careerindia)",
        "region": "Oceania",
        "scene": "cricket",
    },
]

# (place, fact, source, region) -- numbered 14..32 on the page. Facts are
# kept terse so nearly every brief fits on one line; the first nine run in
# the left brief column, the rest in the right one.
BRIEFS = [
    ("Kyiv", "Embassy hit by debris", "Informed Clearly", "Europe"),
    ("Kharkiv", "14 settlements retaken", "Meanwhile in Ukraine", "Europe"),
    ("Brussels", "Hungary lifts EU veto", "Meanwhile in Ukraine", "Europe"),
    ("Rome", "Italy fines Meta \u20ac805m", "Trending World", "Europe"),
    ("Nuuk", "Denmark seals Greenland deal", "AP", "Europe"),
    ("Taipei", "TSMC tightens chip curbs", "Reuters", "Asia"),
    ("Hanoi", "Death penalty cut for 6 crimes", "AFP", "Asia"),
    ("Tokyo", "Nuclear-sub study funded", "Kilambi News", "Asia"),
    ("Seoul", "First cholera case in decade", "Global Affairs News", "Asia"),
    ("New York", "Anthropic -8.5%, $81bn debut", "WSJ", "Americas"),
    ("Ottawa", "Canada deal \u201cneeds work\u201d", "Reuters", "Americas"),
    ("Lima", "6.7 quake hits central Peru", "USGS", "Americas"),
    ("Luanda", "$180m for 10% of De Beers", "Reuters", "Africa"),
    ("Dakar", "Migrant boat sinks", "Global Affairs News", "Africa"),
    ("Nairobi", "Last Ebola patient out", "Illustrated Global Briefing", "Africa"),
    ("Qeshm", "Blast was munitions disposal", "Reuters", "Middle East"),
    ("Jurf al-Sakhar", "Iraqi forces enter", "Global Affairs News", "Middle East"),
    ("Rarotonga", "Cyclone Xavier hits", "Trending World", "Oceania"),
    ("Canberra", "Xi hails ties turnaround", "Reuters", "Oceania"),
]

# Six figures, six different stories.
NUMBERS = [
    ("400+", "DRONES FIRED AT UKRAINE IN ONE NIGHT"),
    ("-5%", "NIKKEI FALL AS THE AI TRADE UNRAVELS"),
    ("34", "KILLED IN THE HAITI POLICE RAID"),
    ("113*", "NICHOLLS' UNBEATEN CENTURY VS INDIA"),
    ("$180M", "ANGOLA'S PRICE FOR 10% OF DE BEERS"),
    ("24H", "MICROSOFT 365 OUTAGE DARKENS OFFICES"),
]

DATE_CHECK = (
    "DATE CHECK \u2014 Deliberately left out as other days' news: the World "
    "Court's genocide ruling itself (Thursday) \u00b7 Anthropic's record "
    "market debut (Thursday) \u00b7 Bukele's third-term filing \u00b7 "
    "Ukraine's third hit on the Kerch bridge \u00b7 Mongolia's "
    "presidential-resignation vote (Thursday) \u00b7 the US\u2013Venezuela "
    "military deal (Wednesday)."
)

DEK = ("Kyiv's bridges burn as missiles fall in Poland \u00b7 the AI "
       "trade routs world markets \u00b7 three rivals sign a peace pledge")

# ---------------------------------------------------------------------------
# World map: land cells as (row, first_col, last_col) on a 20 x 80 grid.
# ---------------------------------------------------------------------------

LAND = [
    (0, 6, 13), (0, 26, 30), (0, 50, 70),
    (1, 1, 19), (1, 25, 29), (1, 34, 34), (1, 40, 43), (1, 45, 79),
    (2, 4, 20), (2, 35, 36), (2, 38, 79),
    (3, 5, 20), (3, 35, 35), (3, 37, 78),
    (4, 5, 19), (4, 38, 77),
    (5, 6, 18), (5, 38, 45), (5, 47, 72),
    (6, 7, 13), (6, 37, 61), (6, 62, 71),
    (7, 11, 14), (7, 36, 51), (7, 58, 62), (7, 64, 74),
    (8, 15, 20), (8, 37, 50), (8, 59, 61), (8, 64, 68), (8, 69, 75),
    (9, 16, 23), (9, 38, 49), (9, 50, 54), (9, 64, 64), (9, 66, 76),
    (10, 17, 24), (10, 39, 48), (10, 65, 75),
    (11, 18, 25), (11, 40, 47), (11, 63, 77),
    (12, 18, 25), (12, 41, 46), (12, 51, 51), (12, 66, 74),
    (13, 19, 24), (13, 42, 46), (13, 51, 51), (13, 65, 75),
    (14, 19, 23), (14, 42, 45), (14, 64, 76),
    (15, 20, 22), (15, 65, 75),
    (16, 20, 21), (16, 67, 73),
    (17, 78, 79),
    (18, 79, 79),
]

# Badge positions (col, row) for the 13 pictured stories.
BADGES = {
    1: (43, 3), 2: (76, 3), 3: (47, 3), 4: (68, 6), 5: (63, 7),
    6: (59, 8), 7: (51, 5), 8: (39, 3), 9: (56, 6), 10: (12, 8),
    11: (53, 8), 12: (9, 5), 13: (79, 17),
}

# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


def textw(d, s, font):
    return d.textlength(s, font=font)


def wrap(d, s, font, maxw):
    words = s.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if textw(d, trial, font) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def centered(d, cx, y, s, font, fill):
    d.text((cx - textw(d, s, font) / 2, y), s, font=font, fill=fill)


def badge(d, cx, cy, n, r=8):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
    f = F(SANS_B, 10 if n < 10 else 9)
    s = str(n)
    d.text((cx - textw(d, s, f) / 2, cy - (6 if n < 10 else 5)), s,
           font=f, fill=WHITE)


def starburst(d, cx, cy, r):
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rad = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    d.polygon(pts, fill=ORANGE)
    d.ellipse([cx - r * 0.28, cy - r * 0.28, cx + r * 0.28, cy + r * 0.28],
              fill=GOLD)


# ---------------------------------------------------------------------------
# Hero scenes (drawn in a 310 x 84 box)
# ---------------------------------------------------------------------------


def scene_poland(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    for sx, sy in [(30, 12), (90, 8), (160, 16), (230, 9), (285, 14),
                   (60, 22), (200, 24)]:
        d.ellipse([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=WHITE)
    # village silhouettes
    for hx, hw in [(18, 44), (78, 56), (150, 48), (216, 60)]:
        d.rectangle([x + hx, y + h - 26, x + hx + hw, y + h], fill=NAVY2)
        d.polygon([(x + hx - 4, y + h - 26), (x + hx + hw / 2, y + h - 40),
                   (x + hx + hw + 4, y + h - 26)], fill=NAVY2)
        d.rectangle([x + hx + hw / 2 - 4, y + h - 16, x + hx + hw / 2 + 4,
                     y + h - 6], fill=GOLD)
    # missile trails + bursts
    for tx, ty, bx, by in [(36, 4, 66, 40), (150, 2, 128, 34),
                           (268, 4, 238, 44)]:
        d.line([x + tx, y + ty, x + bx, y + by], fill=(200, 205, 215),
               width=2)
        starburst(d, x + bx, y + by, 13)
    # drone: small X with a red core
    dx, dy = 196, 20
    d.line([x + dx - 7, y + dy - 7, x + dx + 7, y + dy + 7], fill=WHITE,
           width=2)
    d.line([x + dx - 7, y + dy + 7, x + dx + 7, y + dy - 7], fill=WHITE,
           width=2)
    d.ellipse([x + dx - 3, y + dy - 3, x + dx + 3, y + dy + 3], fill=RED)


def scene_markets(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(10, 12, 18))
    for gx in range(0, w, 31):
        d.line([x + gx, y, x + gx, y + h], fill=(34, 38, 48), width=1)
    for gy in range(0, h, 21):
        d.line([x, y + gy, x + w, y + gy], fill=(34, 38, 48), width=1)
    pts = [(8, 14), (70, 22), (128, 34), (188, 50), (248, 64), (300, 76)]
    d.line([(x + px, y + py) for px, py in pts], fill=RED, width=3)
    for px, py in pts:
        d.ellipse([x + px - 3, y + py - 3, x + px + 3, y + py + 3],
                  fill=RED)
    f = F(SANS_B, 10)
    labels = [(10, 26, "NIKKEI -5%"), (118, 10, "KOSPI -5-6%"),
              (212, 28, "TAIPEI -5-6%")]
    for lx, ly, s in labels:
        d.text((x + lx + 1, y + ly + 1), s, font=f, fill=(0, 0, 0))
        d.text((x + lx, y + ly), s, font=f, fill=(255, 120, 110))


def scene_kyiv(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    for sx, sy in [(24, 10), (120, 7), (210, 13), (290, 8)]:
        d.ellipse([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=WHITE)
    # skyline blocks
    for bx, bw, bh in [(6, 26, 30), (40, 20, 22), (250, 24, 28),
                       (282, 22, 20)]:
        d.rectangle([x + bx, y + h - 22 - bh, x + bx + bw, y + h - 22],
                    fill=NAVY2)
    # river band
    d.rectangle([x, y + h - 22, x + w, y + h], fill=TEAL)
    # three distinct bridges across the river
    for cx0 in (52, 130, 208):
        deck_y = y + h - 22
        d.line([x + cx0, y + deck_y - 12, x + cx0 + 62, y + deck_y - 12],
               fill=(225, 230, 240), width=3)
        d.arc([x + cx0 + 4, y + deck_y - 26, x + cx0 + 58, y + deck_y + 2],
              start=180, end=360, fill=(225, 230, 240), width=2)
        d.line([x + cx0 + 8, y + deck_y - 12, x + cx0 + 8, y + deck_y],
               fill=(190, 195, 205), width=2)
        d.line([x + cx0 + 54, y + deck_y - 12, x + cx0 + 54, y + deck_y],
               fill=(190, 195, 205), width=2)
    # missile trails + bursts
    for tx, bx, by in [(30, 70, 30), (160, 140, 24), (286, 240, 34)]:
        d.line([x + tx, y + 2, x + bx, y + by], fill=(200, 205, 215),
               width=2)
        starburst(d, x + bx, y + by, 12)


HERO_SCENES = {"poland": scene_poland, "markets": scene_markets,
               "kyiv": scene_kyiv}

# ---------------------------------------------------------------------------
# Card banner scenes (drawn in a 184 x 36 box)
# ---------------------------------------------------------------------------


def _bg(d, x, y, w, h, color=SKY):
    d.rectangle([x, y, x + w, y + h], fill=color)


def card_peace(d, x, y, w, h):
    _bg(d, x, y, w, h)
    for fx, col in [(52, RED), (88, GOLD), (124, TEAL)]:
        d.rectangle([x + fx, y + 8, x + fx + 3, y + 28], fill=WHITE)
        d.rectangle([x + fx + 3, y + 8, x + fx + 15, y + 16], fill=col)
    d.ellipse([x + 78, y + 18, x + 106, y + 30], fill=WHITE)  # table
    d.polygon([(x + 88, y + 6), (x + 98, y + 2), (x + 96, y + 10),
               (x + 100, y + 12), (x + 92, y + 13)], fill=WHITE)  # dove


def card_court(d, x, y, w, h):
    _bg(d, x, y, w, h)
    cx = x + w / 2
    d.polygon([(cx - 30, y + 8), (cx + 30, y + 8), (cx, y + 1)], fill=WHITE)
    for i in range(-2, 3):
        d.rectangle([cx + i * 12 - 2, y + 11, cx + i * 12 + 2, y + 28],
                    fill=WHITE)
    d.rectangle([cx - 32, y + 29, cx + 32, y + 32], fill=WHITE)
    d.line([cx - 12, y + 12, cx + 12, y + 12], fill=GOLD, width=2)
    d.polygon([(cx - 12, y + 12), (cx - 17, y + 20), (cx - 7, y + 20)],
              fill=GOLD)
    d.polygon([(cx + 12, y + 12), (cx + 7, y + 20), (cx + 17, y + 20)],
              fill=GOLD)


def card_cyclone(d, x, y, w, h):
    _bg(d, x, y, w, h, TEAL)
    cx, cy = x + 60, y + h / 2
    for r in (5, 10, 15):
        d.arc([cx - r, cy - r, cx + r, cy + r], start=20, end=300,
              fill=WHITE, width=2)
    d.line([x + 110, y + h - 4, x + 122, y + 8], fill=GOLD, width=3)
    for i in range(5):
        d.arc([x + 118 + i * 3, y + 6 + i, x + 128 + i * 3, y + 12 + i],
              start=200, end=330, fill=GOLD, width=2)
    d.arc([x + 130, y + 20, x + 176, y + 36], start=180, end=360,
          fill=WHITE, width=2)


def card_cop(d, x, y, w, h):
    _bg(d, x, y, w, h)
    for cx0 in (48, 66):
        d.rectangle([x + cx0, y + 14, x + cx0 + 10, y + 32], fill=NAVY2)
        d.ellipse([x + cx0 - 3, y + 2, x + cx0 + 13, y + 12],
                  fill=(150, 150, 150))
    d.polygon([(x + 118, y + 6), (x + 136, y + 12), (x + 130, y + 28),
               (x + 112, y + 24), (x + 110, y + 12)], fill=(64, 140, 70))


def card_ukeu(d, x, y, w, h):
    _bg(d, x, y, w, h)
    cx1, cx2, cy = x + 76, x + 108, y + h / 2
    d.ellipse([cx1 - 15, cy - 15, cx1 + 15, cy + 15], fill=(30, 50, 140))
    for i in range(8):
        ang = 2 * math.pi * i / 8
        sx, sy = cx1 + 10 * math.cos(ang), cy + 10 * math.sin(ang)
        d.ellipse([sx - 1.6, sy - 1.6, sx + 1.6, sy + 1.6], fill=GOLD)
    d.ellipse([cx2 - 15, cy - 15, cx2 + 15, cy + 15], fill=(240, 240, 240))
    d.line([cx2 - 15, cy, cx2 + 15, cy], fill=RED, width=4)
    d.line([cx2, cy - 15, cx2, cy + 15], fill=RED, width=4)


def card_hormuz(d, x, y, w, h):
    _bg(d, x, y, w, h, TEAL)
    d.polygon([(x + 40, y + 22), (x + 96, y + 22), (x + 88, y + 30),
               (x + 48, y + 30)], fill=NAVY)
    d.rectangle([x + 56, y + 14, x + 78, y + 22], fill=NAVY2)
    d.polygon([(x + 116, y + 24), (x + 150, y + 24), (x + 144, y + 30),
               (x + 122, y + 30)], fill=(120, 60, 40))
    for i in range(6):
        d.arc([x + 14 + i * 28, y + 27, x + 28 + i * 28, y + 36],
              start=180, end=360, fill=WHITE, width=2)


def card_haiti(d, x, y, w, h):
    _bg(d, x, y, w, h)
    d.line([x + 62, y + 32, x + 62, y + 12], fill=(120, 84, 40), width=3)
    for dx, dy in [(-16, -8), (-8, -12), (0, -14), (9, -12), (17, -8)]:
        d.line([x + 62, y + 12, x + 62 + dx, y + 12 + dy],
               fill=(52, 130, 60), width=3)
    d.polygon([(x + 112, y + 6), (x + 128, y + 10), (x + 128, y + 22),
               (x + 120, y + 30), (x + 112, y + 22)], fill=GOLD)
    d.line([x + 116, y + 16, x + 124, y + 16], fill=NAVY, width=2)


def card_saudi(d, x, y, w, h):
    _bg(d, x, y, w, h)
    d.polygon([(x + 84, y + 4), (x + 100, y + 8), (x + 100, y + 22),
               (x + 92, y + 32), (x + 84, y + 22)], fill=GOLD)
    for r in (16, 24):
        d.arc([x + 72 - r, y + 18 - r, x + 72 + r, y + 18 + r],
              start=300, end=60, fill=ORANGE, width=2)
    d.line([x + 30, y + 30, x + 52, y + 12], fill=(200, 205, 215),
           width=2)
    starburst(d, x + 56, y + 10, 7)


def card_microsoft(d, x, y, w, h):
    _bg(d, x, y, w, h, (24, 26, 34))
    d.rectangle([x + 62, y + 5, x + 122, y + 29], outline=WHITE, width=2)
    d.line([x + 68, y + 11, x + 116, y + 23], fill=RED, width=3)
    d.line([x + 68, y + 23, x + 116, y + 11], fill=RED, width=3)
    d.rectangle([x + 40, y + 12, x + 54, y + 22], outline=GOLD, width=2)
    d.line([x + 40, y + 12, x + 47, y + 18], fill=GOLD, width=1)
    d.line([x + 54, y + 12, x + 47, y + 18], fill=GOLD, width=1)


def card_cricket(d, x, y, w, h):
    _bg(d, x, y, w, h, (44, 110, 54))
    d.line([x + 56, y + 6, x + 72, y + 28], fill=(216, 188, 130), width=5)
    d.ellipse([x + 84, y + 8, x + 94, y + 18], fill=(200, 40, 40))
    for i in range(3):
        d.line([x + 128 + i * 6, y + 12, x + 128 + i * 6, y + 28],
               fill=(230, 220, 180), width=2)
    d.arc([x + 20, y + 22, x + 170, y + 38], start=180, end=360,
          fill=WHITE, width=1)


CARD_SCENES = {
    "peace": card_peace, "court": card_court, "cyclone": card_cyclone,
    "cop": card_cop, "ukeu": card_ukeu, "hormuz": card_hormuz,
    "haiti": card_haiti, "saudi": card_saudi,
    "microsoft": card_microsoft, "cricket": card_cricket,
}

# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

X0, W = 36, 952
CX = X0 + W // 2


def build():
    img = Image.new("RGB", (1024, 1024), PAPER)
    d = ImageDraw.Draw(img)

    total = len(HEROES) + len(CARDS) + len(BRIEFS)
    counts = {}
    for s in HEROES + CARDS:
        counts[s["region"]] = counts.get(s["region"], 0) + 1
    for b in BRIEFS:
        counts[b[3]] = counts.get(b[3], 0) + 1

    # --- top bar ---------------------------------------------------------
    d.text((X0, 20), "THE WORLD IN ONE DAY", font=F(SANS_B, 16), fill=RED)
    right = ("%d STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED FRIDAY "
             "20 NOVEMBER 2026" % total)
    rf = F(SANS, 11)
    d.text((X0 + W - textw(d, right, rf), 24), right, font=rf, fill=INK)
    d.line([X0, 46, X0 + W, 46], fill=INK, width=2)
    d.line([X0, 50, X0 + W, 50], fill=INK, width=1)

    # --- date + dek --------------------------------------------------------
    centered(d, CX, 56, "Friday 20 November 2026", F(SERIF_B, 60), INK)
    centered(d, CX, 124, DEK, F(SERIF_I, 16), RED)
    d.line([X0, 148, X0 + W, 148], fill=INK, width=1)

    # --- numbers strip: six figures, six different stories ------------------
    colw = W / 6.0
    for i, (fig, cap) in enumerate(NUMBERS):
        cx = X0 + colw * i + colw / 2
        centered(d, cx, 156, fig, F(SANS_B, 30), INK)
        for j, ln in enumerate(wrap(d, cap, F(SANS, 10), colw - 14)):
            centered(d, cx, 192 + j * 12, ln, F(SANS, 10), FAINT)
        if i:
            d.line([X0 + colw * i, 158, X0 + colw * i, 212], fill=FAINT,
                   width=1)
    d.line([X0, 218, X0 + W, 218], fill=INK, width=1)

    # --- region tabs (counts computed from the final list) -------------------
    order = ["Europe", "Asia", "Americas", "Middle East", "Africa",
             "Oceania", "Global"]
    tx = X0
    tf = F(SANS_B, 11)
    for reg in order:
        label = "%s %d" % (reg.upper(), counts.get(reg, 0))
        tw = textw(d, label, tf) + 22
        d.rounded_rectangle([tx, 226, tx + tw, 248], radius=4,
                            fill=REGION_COLORS[reg])
        d.text((tx + 11, 231), label, font=tf, fill=WHITE)
        tx += tw + 7

    # --- heroes ----------------------------------------------------------------
    hw = (W - 20) // 3
    for i, hero in enumerate(HEROES):
        hx = X0 + i * (hw + 10)
        HERO_SCENES[hero["scene"]](d, hx, 258, hw, 76)
        badge(d, hx + 13, 271, hero["n"])
        d.text((hx, 340), hero["tag"], font=F(SANS_B, 11), fill=RED)
        lines = wrap(d, hero["headline"], F(SERIF_B, 28), hw)
        for j, ln in enumerate(lines[:3]):
            d.text((hx, 354 + j * 29), ln, font=F(SERIF_B, 28), fill=INK)
        slines = wrap(d, hero["summary"], F(SERIF, 13), hw)
        for j, ln in enumerate(slines[:3]):
            d.text((hx, 448 + j * 15), ln, font=F(SERIF, 13), fill=INK)

    # --- cards -------------------------------------------------------------------
    cw = (W - 32) // 5
    for idx, card in enumerate(CARDS):
        row, col = divmod(idx, 5)
        cx0 = X0 + col * (cw + 8)
        cy0 = 496 + row * 126
        CARD_SCENES[card["scene"]](d, cx0, cy0, cw, 36)
        badge(d, cx0 + 10, cy0 + 10, card["n"], r=7)
        d.text((cx0, cy0 + 40), card["tag"], font=F(SANS_B, 9), fill=RED)
        lines = wrap(d, card["headline"], F(SERIF_B, 15), cw)
        for j, ln in enumerate(lines[:2]):
            d.text((cx0, cy0 + 51 + j * 16), ln, font=F(SERIF_B, 15),
                   fill=INK)
        slines = wrap(d, card["summary"], F(SERIF, 12), cw)
        for j, ln in enumerate(slines[:3]):
            d.text((cx0, cy0 + 85 + j * 13), ln, font=F(SERIF, 12),
                   fill=INK)

    # --- bottom heading ------------------------------------------------------------
    d.line([X0, 752, X0 + W, 752], fill=INK, width=1)
    d.text((X0, 758), "ALSO ON FRIDAY \u2014 %d MORE STORIES" % len(BRIEFS),
           font=F(SANS_B, 13), fill=INK)

    # --- dot-matrix world map ---------------------------------------------------------
    mx, my = X0, 796
    cell, pitch = 4.0, 4.6
    d.text((mx, 780), "WHERE IT HAPPENED", font=F(SANS_B, 11), fill=INK)
    land = set()
    for r, c0, c1 in LAND:
        for c in range(c0, c1 + 1):
            land.add((c, r))
    for (c, r) in land:
        px, py = mx + c * cell + cell / 2, my + r * pitch
        d.ellipse([px - 1.4, py - 1.4, px + 1.4, py + 1.4],
                  fill=(90, 84, 70))
    for n, (c, r) in BADGES.items():
        badge(d, mx + c * cell + cell / 2, my + r * pitch, n, r=7)
    for j, ln in enumerate(wrap(d, "Red numbers match the pictured "
                                   "stories above; 1 to 3 are the "
                                   "front-page leads.", F(SANS, 10), 330)):
        d.text((mx, 896 + j * 12), ln, font=F(SANS, 10), fill=FAINT)

    # --- briefs: numbered, real source names only --------------------------------------
    bf = F(SANS, 12)
    bfb = F(SANS_B, 12)
    col_x = [X0 + 336, X0 + 656]
    col_w = [304, 296]
    chunks = [BRIEFS[:9], BRIEFS[9:]]
    band_bottom = 960
    for ci in range(2):
        y = 780
        for k, brief in enumerate(chunks[ci]):
            bi = k if ci == 0 else 9 + k
            place, fact, source, _reg = brief
            num = "%d " % (14 + bi)
            body = "%s \u2014 %s (%s)" % (place, fact, source)
            numw = textw(d, num, bfb)
            lines = wrap(d, body, bf, col_w[ci] - numw)
            if y + 15 * len(lines) > band_bottom:
                break  # cut from the bottom; never shrink type
            d.text((col_x[ci], y), num, font=bfb, fill=RED)
            for j, ln in enumerate(lines):
                d.text((col_x[ci] + numw, y + j * 15), ln, font=bf,
                       fill=INK)
            y += 15 * len(lines)

    # --- date-check box ------------------------------------------------------------------
    d.rectangle([X0, 964, X0 + W, 996], fill=RED_SOFT, outline=RED,
                width=1)
    dcf = F(SANS, 10)
    for j, ln in enumerate(wrap(d, DATE_CHECK, dcf, W - 20)[:2]):
        d.text((X0 + 10, 970 + j * 12), ln, font=dcf, fill=INK)

    # --- footer ------------------------------------------------------------------------------
    foot = ("Every story here happened, or was first reported, on Friday "
            "20 November 2026. Officials' counts are attributed.")
    d.text((X0, 1006), foot, font=F(SANS, 9), fill=FAINT)
    rfoot = "Sources named beside each story \u00b7 original drawings"
    d.text((X0 + W - textw(d, rfoot, F(SANS, 9)), 1006), rfoot,
           font=F(SANS, 9), fill=FAINT)

    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "entry.png")
    img = build()
    img.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    print("wrote %s: %d bytes, %dx%d" % (out, size, img.width, img.height))
    assert img.width == 1024 and img.height == 1024
    assert size <= 1048576, "entry.png too large: %d" % size


if __name__ == "__main__":
    main()
