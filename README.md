[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Agusgarut/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Agusgarut/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

# The World in One Day — Wednesday 18 November 2026

Entry for the [make.fun bounty "Sum up 18 November's world news in one image"](https://make.fun/bounty/news-image-20261118)
(`news-image-20261118`, $250 prize pool, 50 paid places).

## The image

`entry.png` (1024×1024, PNG) is a newspaper front page summing up
Wednesday 18 November 2026, drawn programmatically with Pillow
(`tools/generate-image.py`) — no photos, no downloaded artwork, all
headlines and drawings written/drawn for this entry.

- **Header:** "Wednesday 18 November 2026" in giant serif, the day named
  unambiguously at the top of the page.
- **13 main stories in 3 rows:** (1) US strikes an Iranian missile site
  on Qeshm Island, Iran fires back at US bases in Kuwait and Bahrain,
  (2) Xi and Putin meet at APEC in Shenzhen, (3) Peltola wins the Alaska
  Senate race, (4) the US loses its measles-free status, (5) Ebola passes
  11,000 cases in DR Congo, (6) Cyclone Xavier hits Category 5,
  (7) Gaza shivers in flooded tents, (8) Waymo halts freeway rides,
  (9) hackers freeze supermarkets in 7 European countries, (10) Voyager 1
  reaches one light-day from Earth, (11) markets slide, Dow falls 566,
  (12) Berlin and Oslo fund Ukraine arms, (13) Ethiopia and Eritrea mass
  troops on their border.
- **"Where it happened":** a world map with numbered pins 1–13 and a
  colour legend per region.
- **"Also on Wednesday 18 November":** 30 more stories (APEC opens in
  Shenzhen, the Quad meets in Manila, 141 Russian drones over Ukraine,
  COP31 in Antalya, the Knesset elects a speaker, the NSA network outage,
  the Apple outage, Anthropic's IPO pricing, Vinicius Junior's Ballon
  d'Or, Fiji's El Nino disaster, and more).

## The program

`main.ts` (Node 22, standard library only) copies `entry.png` to
`/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png` locally).
It runs with no network and is fully deterministic — two runs produce
byte-identical output.

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

## Regenerating the image

```sh
python3 tools/generate-image.py   # writes entry.png
```

## License

MIT — see `LICENSE`.
