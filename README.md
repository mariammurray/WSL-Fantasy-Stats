# wsl-fantasy

An **unofficial** client and analysis toolkit for the Barclays WSL and
WSL2 Fantasy game (wslfootball.com/fantasy), reverse-engineered from
public network traffic in September 2026.

This is not affiliated with, endorsed by, or supported by WSL Football,
Sportz Interactive, or Opta. It talks only to the game's public,
unauthenticated static feed tier — the same JSON any visitor's browser
already loads to render the site. It does not access logged-in user
data, private league info, or anything behind the `x-game-token`
authenticated tier.

## Why this exists

Public tooling for men's football (Premier League, FPL) is abundant —
open APIs, community wrappers, dashboards. Equivalent tooling for
women's leagues is much thinner on the ground, and WSL Fantasy launched
too recently (Aug 2026) for any community wrapper to exist yet. This is
a first attempt at one, built in the open.

## What's been mapped so far

| Feed | URL pattern | Auth needed | Notes |
|---|---|---|---|
| Manifest | `/feeds/live/mixapi/mixapi_{tourId}.json` | No | Cache-buster version string per feed name |
| Matchday roster | `/feeds/players/matchday_{lang}_{tourId}_{matchdayId}.json` | No | **Main dataset.** All ~744 players: price, ownership %, points, form |
| Player detail | `/feeds/popup/stats/player_{lang}_{tourId}_{playerId}.json` | No | Per-player season stat breakdown, recent form, upcoming fixtures |
| League standings | `/fantasy/services/leagues/public/{leagueId}/global` | **Yes** (`x-game-token`) | Not currently used by this project |

`tourId` is `1` for the current season. `matchdayId` corresponds to
gameweek number (confirm exact numbering as the season progresses —
matchday 1 should hold the completed opening gameweek's real results).

## Usage

```bash
pip install -r requirements.txt

# Pull and save a snapshot of a matchday's full player data
python -m wsl_fantasy.client 2

# Analyze the most recent snapshot for underrated picks
python -m wsl_fantasy.analyze "data/snapshots/matchday_*.json"
```

```python
from wsl_fantasy.client import WSLFantasyClient

client = WSLFantasyClient()
players = client.get_matchday_players(matchday_id=2)
```

## Roadmap / open questions

- [ ] Confirm whether `buster` query param is actually required or just
      a CDN cache hint
- [ ] Find/confirm the `fixtures`, `tourDetails`, `leaderboard` feeds
      from the manifest (same pattern, not yet individually verified)
- [ ] Automate "what's the current matchday" instead of passing it
      manually
- [ ] Set up a scheduled snapshot job (GitHub Actions cron) to build
      season-long history
- [ ] Expand `analyze.py` into a proper differential/value dashboard

## A note on responsible use

- This hits a small operator's infrastructure. Snapshot once or twice a
  day at most — there's no need for anything faster for a
  season-long fantasy game.
- Don't use this to build anything that resells the data or misrepresents
  itself as an official WSL/Sportz Interactive product.
- If WSL Football publishes an official API in the future, prefer that
  over this.

## License

MIT for the code in this repo. The underlying data belongs to WSL
Football / Sportz Interactive / Opta — this project does not claim any
rights over it.
