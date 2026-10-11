# Cyclical Living

A small personal tool that emails a short brief before each new moon, full
moon, solstice, equinox and cross-quarter day: a little lore, why the moment
matters, a reflection prompt, a small ritual and a way to meet it outside.

Code computes the facts (dates, times, signs, nakshatras) with
[astronomy-engine](https://github.com/cosinekitty/astronomy). Claude only
writes the prose, and is given those facts as structured input.

## When briefs arrive

| Tier | Events | Lead time |
|---|---|---|
| anchor | solstices, equinoxes, Imbolc, Beltane, Lughnasadh, Samhain | 7 days |
| full_moon | full moons | 2 days |
| new_moon | new moons | 1 day |

That's about 33 emails a year. If a daily run is missed, the brief goes out on
the next run, up to the day of the event. Change lead times in
`src/cyclical_living/config.py` (`LEAD_DAYS`).

All local dates and times are America/Vancouver. Cross-quarter days are
computed as astronomical midpoints (the Sun at 315°, 45°, 135° and 225°); the
traditional fixed dates are included in the brief too.

## Setup

Requires [uv](https://docs.astral.sh/uv/). It installs Python 3.12 for you.

```sh
uv sync
uv run pytest
```

Environment variables:

| Variable | Needed for |
|---|---|
| `ANTHROPIC_API_KEY` | writing briefs (dry runs too) |
| `CLAUDE_MODEL` | optional, defaults to `claude-sonnet-5-5` |
| `RESEND_API_KEY` | sending email |
| `FROM_EMAIL` | sender, on a domain verified in Resend, e.g. `Moon <moon@yourdomain.com>` |
| `TO_EMAIL` | where briefs go |

## Commands

```sh
# Upcoming events and when each brief will send (default: next 92 days)
uv run cyclical-living events
uv run cyclical-living events --from 2027-01-01 --days 365

# Preview what would send on any day, without sending or archiving
uv run cyclical-living run --date 2026-10-23 --dry-run

# The real thing (what the GitHub Action runs each morning)
uv run cyclical-living run
```

## The archive

Every sent brief is saved as markdown in `archive/YYYY/`, e.g.
`archive/2026/2026-10-25-full-moon.md`. Over time it becomes an almanac.

The archive is also the state: a brief is written there only after it's
delivered, and the runner skips any event whose file already exists. The
`tradition_used` in each file's header lets the writer rotate traditions. To
resend a brief, delete its file.

## GitHub Action

`.github/workflows/daily-brief.yml` runs daily at 14:00 UTC (7 am Pacific) and
commits new archive files back to the repo.

1. Add repository secrets (Settings → Secrets and variables → Actions):
   `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `TO_EMAIL`, `FROM_EMAIL`.
2. Optionally add a repository variable `CLAUDE_MODEL`.
3. To test, run the workflow by hand (Actions → Daily brief → Run workflow)
   with a date. Dry run is on by default; the brief prints in the job log.
   With dry run off, it really sends and archives, so a later scheduled run
   won't send that event again.

## Future ideas

- Eclipses
- First-crescent events
- Exact Lahiri ayanamsa via pyswisseph (swap `lahiri_ayanamsa()` in `zodiac.py`)
- An ICS calendar feed
- A "used it / skipped it" feedback link
- More delivery channels, like ntfy or Telegram (add a class with a `send(brief)` method in `delivery.py`)
