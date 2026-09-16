# wsl-fantasy

An **unofficial** client and analysis toolkit for the Barclays WSL and
WSL2 Fantasy game (wslfootball.com/fantasy), reverse-engineered from
public network traffic in September 2026.

This is not affiliated with, endorsed by, or supported by WSL Football,
Sportz Interactive, or Opta. It does not access logged-in user
data or private league info.

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
gameweek number 


## License

MIT for the code in this repo. The underlying data belongs to WSL
Football / Sportz Interactive / Opta — this project does not claim any
rights over it.
