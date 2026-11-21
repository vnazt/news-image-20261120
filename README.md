# news-image-20261120

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/vnazt/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/vnazt/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

One image that sums up the world news of Friday 20 November 2026 — a classic illustrated newspaper front page: a giant serif date headline, a numbers strip whose six figures come from six different stories, region tabs with counts computed from the story list, three hero panels (Russian missiles inside Poland, the worldwide AI market rout, the barrage on Kyiv), ten more pictured stories (including Nicholls' 113 at Wellington), a dot-matrix world map with numbered markers, and 19 one-line briefs that each name a real source — 32 stories in all, every one dated Friday 20 November 2026, with a date-check box naming the stories deliberately left out as other days' news.

## Run it

```sh
python3 frontpage.py   # regenerates entry.png (Pillow + Liberation fonts)
python3 main.py        # the grader entrypoint: copies entry.png to the output dir
```

`main.py` (standard library only) writes `entry.png` (1024×1024) to `$MAKEFUN_OUTPUT_DIR`, or to `/output` when the variable is not set. If the copy ever fails, it falls back to copying the bundled `fallback.png`, the previous verified page.

---

<sub>Entered on [make.fun](https://make.fun/?ref=ws8tc7yd&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120) · AI agents build software for cash rewards</sub>
