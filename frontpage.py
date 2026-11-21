#!/usr/bin/env python3
"""frontpage.py -- generator for the news-image-20261120 entry.

Draws a classic illustrated newspaper front page for Friday 20 November
2026 with Pillow and the Liberation fonts: masthead, giant serif date,
numbers strip, region tabs, three hero panels, ten mid cards, a
dot-matrix world map, one-line briefs, a date-check box and a footer.

Deterministic: the same code always produces the same entry.png.
Run locally:  python3 frontpage.py   (writes entry.png beside this file)
"""

import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/liberation"

W, H = 1024, 1024
MX = 28                      # side margin
CW = W - 2 * MX              # content width = 968

PAPER = (246, 242, 231)
INK = (24, 22, 18)
FAINT = (108, 100, 88)
RULE = (168, 158, 138)
RED = (176, 32, 28)
GOLD = (198, 156, 62)


def serif(style, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "LiberationSerif-%s.ttf" % style), size)


def sans(style, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, "LiberationSans-%s.ttf" % style), size)


# ---------------------------------------------------------------- stories

HEROES = [
    {
        "n": 1, "region": "Europe", "scene": "poland",
        "tag": "SOUTH-EAST POLAND - NATO TERRITORY",
        "headline": "Russian Missiles Fall Inside Poland",
        "summary": "Two missiles and a jet drone fell in border villages. "
                   "PM Tusk called it a provocation. (Reuters)",
    },
    {
        "n": 2, "region": "Global", "scene": "markets",
        "tag": "TOKYO - SEOUL - TAIPEI - NEW YORK",
        "headline": "AI Sell-Off Turns Into a Worldwide Rout",
        "summary": "The AI trade unravels: Nikkei -5%, Kospi -5-6%, stocks' "
                   "longest losing run since 2023. (Reuters)",
    },
    {
        "n": 3, "region": "Europe", "scene": "kyiv",
        "tag": "KYIV - UKRAINE",
        "headline": "400 Drones and 110 Missiles Rain on Kyiv",
        "summary": "Bridges and power grid smashed, eight killed; nuclear "
                   "plants cut output. (Reuters)",
    },
]

CARDS = [
    {
        "n": 4, "region": "Asia", "scene": "peace",
        "tag": "SHENZHEN - CHINA",
        "headline": "Three Rivals Sign Peace Declaration",
        "summary": "Trump, Xi and Putin issue a joint peace pledge. (Reuters)",
    },
    {
        "n": 5, "region": "Asia", "scene": "myanmar",
        "tag": "THE HAGUE - MYANMAR",
        "headline": "Myanmar Rejects Genocide Ruling",
        "summary": "Rulers call the World Court's finding 'unfair'. (WSJ)",
    },
    {
        "n": 6, "region": "Asia", "scene": "akvan",
        "tag": "ODISHA - INDIA",
        "headline": "Cyclone Akvan Nears Odisha Coast",
        "summary": "Trains cancelled as the storm nears land. (Careerindia)",
    },
    {
        "n": 7, "region": "Asia", "scene": "cop31",
        "tag": "ANTALYA - TURKIYE",
        "headline": "Climate Talks Stall Over Fossils",
        "summary": "Deadlock on fossil fuels as final day ends. (Reuters/AP)",
    },
    {
        "n": 8, "region": "Europe", "scene": "ukeu",
        "tag": "BRUSSELS - BELGIUM",
        "headline": "Britain and EU Agree Reset Deal",
        "summary": "Food, youth mobility and carbon markets included. (Reuters)",
    },
    {
        "n": 9, "region": "Middle East", "scene": "hormuz",
        "tag": "STRAIT OF HORMUZ",
        "headline": "US Blockade Chokes Iran Strait",
        "summary": "Trump demands a 'real deal'; Qatar mediates. (Reuters)",
    },
    {
        "n": 10, "region": "Americas", "scene": "haiti",
        "tag": "PORT-AU-PRINCE - HAITI",
        "headline": "Police Raid Kills 34 in Haiti",
        "summary": "Police kill 34 suspected gang members. (Open Chronicle)",
    },
    {
        "n": 11, "region": "Middle East", "scene": "saudi",
        "tag": "RIYADH - SAUDI ARABIA",
        "headline": "Saudi Shields Stop Houthi Missiles",
        "summary": "Air defences intercept the missiles over Riyadh. (Reuters)",
    },
    {
        "n": 12, "region": "Global", "scene": "microsoft",
        "tag": "WORLDWIDE - TECH",
        "headline": "Microsoft Outage Darkens Offices",
        "summary": "Outlook and Teams down for a day; servers blamed. (Reuters)",
    },
    {
        "n": 13, "region": "Asia", "scene": "vietnam",
        "tag": "HANOI - VIETNAM",
        "headline": "Vietnam Cuts the Death Penalty",
        "summary": "Assembly ends it for drugs and five other crimes. (AFP)",
    },
]

# place, fact, source tag, region -- terse one-liners, most expendable last
BRIEFS = [
    ("KYIV", "Dutch embassy damaged by debris", "Informed", "Europe"),
    ("KHARKIV", "Ukraine retakes 14 settlements", "Digest", "Europe"),
    ("BRUSSELS", "Hungary lifts Ukraine EU veto", "Digest", "Europe"),
    ("FRANKFURT", "Two held over bar bomb plot", "Informed", "Europe"),
    ("COPENHAGEN", "Denmark expels Russian attache", "Kilambi", "Europe"),
    ("ROME", "Italy fines Meta \u20ac805 million", "Roundup", "Europe"),
    ("EUROPE", "Four capitals propose Ukraine guarantees", "CNN", "Europe"),
    ("TAIPEI", "TSMC tightens China chip curbs", "Reuters", "Asia"),
    ("PHNOM PENH", "US sanctions scam enablers", "IANS", "Asia"),
    ("TOKYO", "Japan funds nuclear-sub study", "Yonhap", "Asia"),
    ("JAPAN", "5.7 quake injures 22 people", "Roundup", "Asia"),
    ("SEOUL", "First cholera case in a decade", "Roundup", "Asia"),
    ("TAIWAN", "Russian bombers enter air zone", "Informed", "Asia"),
    ("QESHM", "Iran: blast was munitions disposal", "Reuters", "Middle East"),
    ("LUANDA", "Angola buys 10% of De Beers, $180m", "Reuters", "Africa"),
    ("SENEGAL", "Migrant boat capsizes off coast", "Roundup", "Africa"),
    ("NAIROBI", "Last Ebola patient discharged", "Briefing", "Africa"),
    ("OTTAWA", "Trump: Canada deal needs work", "Reuters", "Americas"),
    ("PERU", "6.7 quake shakes central region", "USGS", "Americas"),
    ("BRASILIA", "Lula shields Raoni's Amazon land", "Roundup", "Americas"),
    ("BOGOTA", "Protests over taxes, US ties", "Roundup", "Americas"),
    ("RAROTONGA", "Cyclone Xavier hits Cook Islands", "Roundup", "Oceania"),
    ("WELLINGTON", "Nicholls hits unbeaten 113", "Careerindia", "Oceania"),
    ("SHENZHEN", "Humans must oversee military AI", "Std Topic", "Global"),
    ("ORBIT", "Space data-centre arms-race warning", "Informed", "Global"),
]

REGIONS = ["Europe", "Asia", "Middle East", "Africa", "Americas", "Oceania", "Global"]
TAB_COLORS = {
    "Europe": (36, 78, 140), "Asia": (176, 32, 28), "Middle East": (188, 108, 16),
    "Africa": (30, 116, 58), "Americas": (104, 58, 148), "Oceania": (14, 124, 134),
    "Global": (84, 84, 84),
}

NUMBERS = [
    ("400+", "DRONES FIRED AT UKRAINE"),
    ("110", "MISSILES IN THE BARRAGE"),
    ("8", "KILLED IN KYIV"),
    ("-5%", "WORST WEEK SINCE 2020"),
    ("34", "KILLED IN HAITI RAID"),
    ("-8.5%", "ANTHROPIC'S SLIDE"),
]

DATE_CHECK = (
    "DATE CHECK - Deliberately left out as other days' news: the World Court's "
    "genocide ruling itself (Thursday) - Anthropic's record market debut "
    "(Thursday) - Bukele's third-term filing - Ukraine's third hit on the Kerch "
    "bridge - Mongolia's presidential-resignation vote (Thursday) - the "
    "US-Venezuela military deal (Wednesday)."
)

# ------------------------------------------------------------- text utils

def wrap_lines(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if not cur or d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(d, x, y, text, font, fill, maxw, lh, max_lines=None):
    lines = wrap_lines(d, text, font, maxw)
    if max_lines:
        lines = lines[:max_lines]
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


BF_B = None  # brief fonts, set in build()
BF_R = None


def brief_tokens(brief):
    place, fact, source, _region = brief
    toks = [(w, BF_B, INK) for w in place.split()]
    toks.append(("\u2014", BF_R, INK))
    toks += [(w, BF_R, INK) for w in fact.split()]
    toks += [(w, BF_R, FAINT) for w in ("(" + source + ")").split()]
    return toks


def wrap_rich(d, toks, maxw):
    space = d.textlength(" ", font=BF_R)
    lines, cur, curw = [], [], 0.0
    for tok in toks:
        wlen = d.textlength(tok[0], font=tok[1])
        add = wlen if not cur else space + wlen
        if cur and curw + add > maxw:
            lines.append(cur)
            cur, curw = [tok], wlen
        else:
            cur.append(tok)
            curw += add
    if cur:
        lines.append(cur)
    return lines


def select_briefs(d, colw, col_lines):
    """Greedy column fill; returns the briefs that fit (rest are cut)."""
    kept, col, used = [], 0, 0
    for b in BRIEFS:
        n = len(wrap_rich(d, brief_tokens(b), colw))
        if n > col_lines:
            continue
        if used + n > col_lines:
            col += 1
            used = 0
            if col > 2:
                break
        kept.append(b)
        used += n
    return kept


# ----------------------------------------------------------------- scenes

def _stars(d, w, h, seed, count=26):
    rng = random.Random(seed)
    for _ in range(count):
        x, y = rng.randrange(2, w - 2), rng.randrange(2, max(4, h - 18))
        d.point((x, y), fill=(210, 215, 230))


def _burst(d, x, y, r=8):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 148, 44))
    d.ellipse([x - r // 2, y - r // 2, x + r // 2, y + r // 2], fill=(255, 214, 120))
    for dx, dy in ((-r - 4, 0), (r + 4, 0), (0, -r - 4), (0, r + 3), (-r - 2, -r - 2), (r + 2, -r - 2)):
        d.line([x, y, x + dx, y + dy], fill=(255, 170, 70), width=2)


def _trail(d, x0, y0, x1, y1):
    d.line([x0, y0, x1, y1], fill=(232, 128, 48), width=5)
    d.line([x0, y0, x1, y1], fill=(245, 245, 245), width=2)


def scene_poland(w, h):
    img = Image.new("RGB", (w, h), (15, 21, 38))
    d = ImageDraw.Draw(img)
    _stars(d, w, h, 11)
    # village silhouette
    d.rectangle([0, h - 16, w, h], fill=(5, 7, 12))
    for x, hw, hh in ((18, 34, 14), (66, 26, 10), (150, 30, 12), (236, 36, 15), (282, 24, 10)):
        d.rectangle([x, h - 16 - hh, x + hw, h - 16], fill=(5, 7, 12))
        d.polygon([(x - 2, h - 16 - hh), (x + hw + 2, h - 16 - hh), (x + hw // 2, h - 22 - hh)], fill=(5, 7, 12))
        d.rectangle([x + hw // 2 - 2, h - 12 - hh, x + hw // 2 + 1, h - 9 - hh], fill=(255, 190, 90))
        d.rectangle([x + 5, h - 11 - hh, x + 8, h - 8 - hh], fill=(255, 190, 90))
        d.rectangle([x + hw - 9, h - 10 - hh, x + hw - 6, h - 7 - hh], fill=(255, 214, 130))
    _trail(d, 52, -2, 104, 32)
    _trail(d, 176, -2, 208, 26)
    _trail(d, 268, -2, 244, 34)
    _burst(d, 104, 32, 8)
    _burst(d, 208, 26, 7)
    _burst(d, 244, 34, 8)
    # jet drone: small X with red core
    d.line([88, 12, 100, 22], fill=(170, 178, 195), width=2)
    d.line([100, 12, 88, 22], fill=(170, 178, 195), width=2)
    d.ellipse([92, 15, 96, 19], fill=(230, 60, 50))
    return img


def scene_markets(w, h):
    img = Image.new("RGB", (w, h), (9, 9, 11))
    d = ImageDraw.Draw(img)
    for gx in range(0, w, 26):
        d.line([gx, 0, gx, h], fill=(38, 38, 46))
    for gy in range(0, h, 16):
        d.line([0, gy, w, gy], fill=(38, 38, 46))
    pts = [(6, 12), (70, 18), (128, 15), (184, 32), (238, 38), (300, 54)]
    d.line(pts, fill=(225, 48, 38), width=3, joint="curve")
    d.polygon([(300, 54), (288, 52), (296, 44)], fill=(225, 48, 38))
    f = sans("Bold", 9)
    d.text((10, h - 13), "NIKKEI -5%", font=f, fill=(225, 120, 105))
    d.text((140, 4), "KOSPI -6%", font=f, fill=(225, 120, 105))
    d.text((238, 8), "TAIPEI -5%", font=f, fill=(225, 120, 105))
    return img


def scene_kyiv(w, h):
    img = Image.new("RGB", (w, h), (13, 19, 34))
    d = ImageDraw.Draw(img)
    _stars(d, w, h, 23, 18)
    # skyline blocks
    for x, bw, bh in ((4, 26, 20), (36, 18, 14), (238, 22, 17), (266, 30, 22), (300, 12, 12)):
        d.rectangle([x, h - 14 - bh, x + bw, h - 14], fill=(5, 7, 12))
    # river + three bridges
    d.rectangle([0, h - 16, w, h], fill=(24, 52, 86))
    for bx in (58, 138, 218):
        d.line([bx, h - 16, bx + 56, h - 16], fill=(215, 222, 235), width=3)
        d.arc([bx + 6, h - 25, bx + 50, h - 9], 180, 360, fill=(170, 180, 200), width=2)
    _trail(d, 40, -2, 84, 26)
    _trail(d, 128, -2, 160, 22)
    _trail(d, 214, -2, 196, 28)
    _trail(d, 292, -2, 262, 24)
    _burst(d, 84, 26, 7)
    _burst(d, 160, 22, 6)
    _burst(d, 196, 28, 7)
    _burst(d, 262, 24, 6)
    d.ellipse([96, 30, 128, 40], fill=(70, 76, 92))
    d.ellipse([180, 34, 214, 43], fill=(70, 76, 92))
    return img


def banner_peace(w, h):
    img = Image.new("RGB", (w, h), (22, 30, 50))
    d = ImageDraw.Draw(img)
    for x, col in ((16, (46, 84, 160)), (40, (200, 60, 50)), (64, (228, 186, 60))):
        d.line([x, 4, x, h - 4], fill=(200, 200, 200), width=1)
        d.rectangle([x + 1, 5, x + 19, 17], fill=col)
    # dove
    d.ellipse([112, 12, 154, 26], fill=(242, 242, 242))
    d.polygon([(122, 14), (138, 3), (148, 14)], fill=(242, 242, 242))
    d.ellipse([150, 13, 159, 20], fill=(242, 242, 242))
    d.polygon([(152, 17), (161, 14), (153, 21)], fill=(255, 190, 60))
    d.polygon([(114, 18), (104, 12), (106, 22)], fill=(220, 220, 220))
    return img


def banner_myanmar(w, h):
    img = Image.new("RGB", (w, h), (28, 34, 46))
    d = ImageDraw.Draw(img)
    d.polygon([(28, 4), (76, 4), (52, -2)], fill=(235, 232, 222))
    d.rectangle([30, 6, 74, 9], fill=(235, 232, 222))
    for x in (33, 45, 57, 69):
        d.rectangle([x, 11, x + 4, 27], fill=(235, 232, 222))
    d.rectangle([28, 28, 76, 31], fill=(235, 232, 222))
    d.line([118, 5, 152, 31], fill=RED, width=5)
    d.line([152, 5, 118, 31], fill=RED, width=5)
    return img


def banner_akvan(w, h):
    img = Image.new("RGB", (w, h), (18, 32, 48))
    d = ImageDraw.Draw(img)
    for i, r in enumerate((5, 10, 15, 20)):
        cx, cy = 46 + i * 2, 18 - i
        d.arc([cx - r, cy - r, cx + r, cy + r], 300, 200, fill=(130, 205, 225), width=2)
    d.line([0, h - 5, w, h - 5], fill=(214, 194, 142), width=3)
    d.line([140, h - 5, 146, 12], fill=(120, 90, 50), width=2)
    for a in (200, 250, 300):
        d.arc([128, 2, 162, 20], a, a + 70, fill=(70, 170, 84), width=2)
    return img


def banner_cop31(w, h):
    img = Image.new("RGB", (w, h), (24, 34, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([28, 14, 40, h], fill=(120, 124, 128))
    d.rectangle([48, 18, 58, h], fill=(120, 124, 128))
    for x, y, r in ((30, 8, 6), (40, 5, 8), (54, 11, 5)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=(168, 172, 176))
    d.polygon([(128, 5), (162, 18), (128, 31), (114, 18)], fill=(62, 172, 84))
    d.line([121, 26, 160, 9], fill=(40, 120, 56), width=2)
    return img


def banner_ukeu(w, h):
    img = Image.new("RGB", (w, h), (22, 28, 48))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([22, 6, 84, 30], 4, fill=(36, 60, 140))
    import math
    for i in range(8):
        a = i * math.pi / 4
        x, y = 53 + 10 * math.cos(a), 18 + 8 * math.sin(a)
        d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(250, 205, 60))
    d.rounded_rectangle([94, 6, 158, 30], 4, fill=(236, 236, 236))
    d.rectangle([121, 6, 131, 30], fill=(200, 40, 40))
    d.rectangle([94, 15, 158, 21], fill=(200, 40, 40))
    return img


def banner_hormuz(w, h):
    img = Image.new("RGB", (w, h), (16, 32, 50))
    d = ImageDraw.Draw(img)
    d.polygon([(0, h), (0, 22), (58, 27), (82, h)], fill=(74, 66, 48))
    d.polygon([(108, 0), (w, 0), (w, 13), (136, 7)], fill=(74, 66, 48))
    d.polygon([(74, 21), (116, 21), (108, 28), (82, 28)], fill=(150, 156, 166))
    d.rectangle([90, 15, 100, 21], fill=(150, 156, 166))
    d.polygon([(136, 24), (172, 24), (166, 29), (142, 29)], fill=(110, 70, 60))
    return img


def banner_haiti(w, h):
    img = Image.new("RGB", (w, h), (20, 38, 42))
    d = ImageDraw.Draw(img)
    d.ellipse([16, 22, 92, 35], fill=(216, 198, 148))
    d.line([52, 23, 56, 9], fill=(120, 90, 50), width=2)
    for a in (180, 230, 280, 320):
        d.arc([38, 0, 74, 16], a, a + 60, fill=(70, 170, 84), width=2)
    d.polygon([(128, 4), (152, 8), (152, 20), (140, 33), (128, 20)], fill=GOLD)
    d.polygon([(132, 8), (148, 11), (148, 19), (140, 28), (132, 19)], fill=(36, 78, 140))
    return img


def banner_saudi(w, h):
    img = Image.new("RGB", (w, h), (14, 24, 42))
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 8, w, h], fill=(5, 7, 12))
    for x, bw, bh in ((8, 16, 12), (150, 20, 15), (30, 12, 8)):
        d.rectangle([x, h - 8 - bh, x + bw, h - 8], fill=(5, 7, 12))
    d.polygon([(80, 3), (104, 7), (104, 19), (92, 32), (80, 19)], fill=GOLD)
    d.arc([6, 2, 84, 30], 300, 40, fill=(240, 120, 90), width=2)
    d.arc([100, 2, 178, 30], 140, 240, fill=(240, 120, 90), width=2)
    return img


def banner_microsoft(w, h):
    img = Image.new("RGB", (w, h), (8, 12, 18))
    d = ImageDraw.Draw(img)
    d.rectangle([26, 5, 88, 28], outline=(170, 178, 190), width=2)
    d.line([57, 28, 57, 32], fill=(170, 178, 190), width=2)
    d.line([34, 5, 80, 28], fill=RED, width=3)
    d.line([80, 5, 34, 28], fill=RED, width=3)
    d.rectangle([112, 10, 152, 24], outline=(240, 240, 240), width=2)
    d.line([112, 11, 132, 20], fill=(240, 240, 240), width=1)
    d.line([152, 11, 132, 20], fill=(240, 240, 240), width=1)
    return img


def banner_vietnam(w, h):
    img = Image.new("RGB", (w, h), (28, 26, 32))
    d = ImageDraw.Draw(img)
    d.line([58, 0, 58, 9], fill=(206, 182, 140), width=2)
    d.ellipse([46, 9, 70, 31], outline=(206, 182, 140), width=2)
    d.ellipse([108, 3, 148, 33], outline=RED, width=3)
    d.line([113, 29, 143, 7], fill=RED, width=3)
    return img


SCENES = {
    "poland": scene_poland, "markets": scene_markets, "kyiv": scene_kyiv,
}
BANNERS = {
    "peace": banner_peace, "myanmar": banner_myanmar, "akvan": banner_akvan,
    "cop31": banner_cop31, "ukeu": banner_ukeu, "hormuz": banner_hormuz,
    "haiti": banner_haiti, "saudi": banner_saudi, "microsoft": banner_microsoft,
    "vietnam": banner_vietnam,
}

# dot-matrix world map: land spans (col_start, col_end) per row
LAND = {
    0: [(2, 21), (70, 104)],
    1: [(2, 27), (58, 63), (66, 106)],
    2: [(4, 29), (56, 65), (66, 104)],
    3: [(5, 29), (57, 64), (68, 100), (106, 109)],
    4: [(6, 27), (55, 78), (82, 90), (94, 100), (107, 107)],
    5: [(10, 24), (24, 34), (57, 70), (84, 88), (95, 101), (98, 108)],
    6: [(25, 36), (58, 69), (96, 110)],
    7: [(26, 35), (59, 67), (102, 112)],
    8: [(27, 33), (60, 65), (101, 111)],
    9: [(28, 31), (103, 109), (113, 114)],
    10: [(29, 30)],
}
BADGES = {  # story number -> (col, row)
    1: (60, 2), 2: (107, 3), 3: (64, 2), 4: (102, 3), 5: (94, 4),
    6: (16, 3), 7: (76, 3), 8: (66, 3), 9: (22, 4), 10: (57, 2),
    11: (73, 4), 12: (99, 4), 13: (89, 4),
}


# ------------------------------------------------------------------- page

def build():
    global BF_B, BF_R
    BF_B = sans("Bold", 12)
    BF_R = sans("Regular", 12)

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # decide briefs first (counts feed the top bar and region tabs)
    brief_colw, brief_pitch, brief_lines_per_col = 310, 15, 9
    kept = select_briefs(d, brief_colw, brief_lines_per_col)
    counts = {r: 0 for r in REGIONS}
    for s in HEROES + CARDS:
        counts[s["region"]] += 1
    for b in kept:
        counts[b[3]] += 1
    total = 13 + len(kept)

    # 1. top bar
    d.text((MX, 13), "THE WORLD IN ONE DAY", font=sans("Bold", 15), fill=RED)
    right = "%d STORIES - 7 REGIONS - EVERY ONE DATED FRIDAY 20 NOVEMBER 2026" % total
    d.text((W - MX, 16), right, font=sans("Bold", 11), fill=INK, anchor="ra")
    d.line([MX, 38, W - MX, 38], fill=RULE, width=1)

    # 2. giant date
    d.text((W // 2, 42), "Friday 20 November 2026", font=serif("Bold", 64),
           fill=INK, anchor="ma")
    d.line([MX, 114, W - MX, 114], fill=RULE, width=1)

    # 3. dek
    dek = ("Missiles burn Kyiv's bridges - and fall in Poland; the AI trade "
           "routs world markets; three rivals sign a peace pledge.")
    d.text((W // 2, 120), dek, font=serif("Italic", 17), fill=RED, anchor="ma")

    # 4. numbers strip
    ny = 148
    colw = CW / 6.0
    for i, (fig, cap) in enumerate(NUMBERS):
        cx = MX + (i + 0.5) * colw
        d.text((cx, ny), fig, font=serif("Bold", 30), fill=INK, anchor="ma")
        d.text((cx, ny + 38), cap, font=sans("Regular", 11), fill=FAINT, anchor="ma")
        if i:
            lx = MX + i * colw
            d.line([lx, ny + 2, lx, ny + 48], fill=RULE, width=1)

    # 5. region tabs
    ty = 206
    tx = MX
    for r in REGIONS:
        label = "%s %d" % (r.upper(), counts[r])
        f = sans("Bold", 10)
        tw = d.textlength(label, font=f)
        d.rounded_rectangle([tx, ty, tx + tw + 16, ty + 20], 3, fill=TAB_COLORS[r])
        d.text((tx + 8, ty + 4), label, font=f, fill=(255, 255, 255))
        tx += tw + 22
    d.line([MX, ty + 27, W - MX, ty + 27], fill=RULE, width=1)

    # 6. hero panels
    hy = 240
    hw = 314
    for i, s in enumerate(HEROES):
        x = MX + i * (hw + 13)
        img.paste(SCENES[s["scene"]](hw, 64), (x, hy))
        cx, cy = x + 15, hy + 15
        d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=RED)
        d.text((cx, cy), str(s["n"]), font=sans("Bold", 13), fill=(255, 255, 255), anchor="mm")
        yy = hy + 68
        d.text((x, yy), s["tag"], font=sans("Bold", 10), fill=RED)
        yy += 15
        yy = draw_wrapped(d, x, yy, s["headline"], serif("Bold", 28), INK, hw, 30, 2)
        yy += 2
        draw_wrapped(d, x, yy, s["summary"], sans("Regular", 13), INK, hw, 16, 2)

    # 7. mid cards, two rows of five
    cy0 = 424
    cw2, ch2 = 184, 122
    for idx, s in enumerate(CARDS):
        x = MX + (idx % 5) * (cw2 + 12)
        y = cy0 + (idx // 5) * (ch2 + 8)
        img.paste(BANNERS[s["scene"]](cw2, 36), (x, y))
        yy = y + 40
        nf = sans("Bold", 11)
        d.text((x, yy), str(s["n"]), font=nf, fill=RED)
        nw = d.textlength(str(s["n"]), font=nf)
        d.text((x + nw + 4, yy + 1), s["tag"], font=sans("Bold", 9), fill=FAINT)
        yy += 14
        yy = draw_wrapped(d, x, yy, s["headline"], serif("Bold", 15), INK, cw2, 18, 2)
        draw_wrapped(d, x, yy, s["summary"], sans("Regular", 12), INK, cw2, 15, 2)

    # 8. dot-matrix map
    my = 690
    d.text((MX, my), "WHERE IT HAPPENED", font=sans("Bold", 12), fill=INK)
    map_y = my + 20
    pitch_x, pitch_y = 8.0, 6.2
    for row, spans in LAND.items():
        for a, b in spans:
            for c in range(a, b + 1):
                px, py = MX + c * pitch_x, map_y + row * pitch_y
                d.ellipse([px - 1.5, py - 1.5, px + 1.5, py + 1.5], fill=(96, 102, 112))
    bf = sans("Bold", 8)
    for n, (c, r) in BADGES.items():
        px, py = MX + c * pitch_x, map_y + r * pitch_y
        d.ellipse([px - 6.5, py - 6.5, px + 6.5, py + 6.5], fill=RED)
        d.text((px, py), str(n), font=bf, fill=(255, 255, 255), anchor="mm")
    d.text((MX, map_y + 74), "Red numbers match the stories above - 1 to 3 are the front-page leads.",
           font=sans("Regular", 11), fill=FAINT)

    # 9. briefs
    by = map_y + 96
    d.text((MX, by), "ALSO ON FRIDAY - %d MORE STORIES" % len(kept),
           font=serif("Bold", 15), fill=INK)
    d.line([MX, by + 21, W - MX, by + 21], fill=RULE, width=1)
    col_xs = [MX, MX + 328, MX + 656]
    col, used = 0, 0
    space = d.textlength(" ", font=BF_R)
    for b in kept:
        lines = wrap_rich(d, brief_tokens(b), brief_colw)
        if used + len(lines) > brief_lines_per_col:
            col += 1
            used = 0
        x = col_xs[col]
        yy = by + 27 + used * brief_pitch
        for line in lines:
            lx = x
            for word, f, colr in line:
                d.text((lx, yy), word, font=f, fill=colr)
                lx += d.textlength(word, font=f) + space
            yy += brief_pitch
        used += len(lines)

    # 10. date-check box
    dy = 950
    d.rectangle([MX, dy, W - MX, dy + 38], outline=RED, width=1)
    d.rectangle([MX + 1, dy + 1, W - MX - 1, dy + 37], fill=(250, 236, 231))
    draw_wrapped(d, MX + 10, dy + 5, DATE_CHECK, sans("Regular", 12), INK, CW - 20, 15, 2)

    # 11. footer
    d.text((MX, 996), "Every story here happened, or was first reported, on Friday "
                      "20 November 2026. Officials' counts are attributed.",
           font=sans("Regular", 11), fill=FAINT)
    d.text((W - MX, 996), "Sources named beside each story - original drawings",
           font=sans("Regular", 11), fill=FAINT, anchor="ra")

    out = os.path.join(HERE, "entry.png")
    img.save(out, optimize=True)
    return out


if __name__ == "__main__":
    print(build())
