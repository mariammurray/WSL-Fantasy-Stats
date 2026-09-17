# wsl-fantasy

An **unofficial** client and analysis toolkit for the Barclays WSL and
WSL2 Fantasy game (wslfootball.com/fantasy), reverse-engineered from
public network traffic in September 2026.

This is not affiliated with, endorsed by, or supported by WSL Football,
Sportz Interactive, or Opta. It does not access logged-in user
data or private league info.


## What's been mapped so far

| Feed | URL pattern | Auth needed | Notes |
|---|---|---|---|
| Manifest | `/feeds/live/mixapi/mixapi_{tourId}.json` | No | Cache-buster version string per feed name |
| Matchday roster | `/feeds/players/matchday_{lang}_{tourId}_{matchdayId}.json` | No | **Main dataset.** All ~744 players: price, ownership %, points, form |
| Player detail | `/feeds/popup/stats/player_{lang}_{tourId}_{playerId}.json` | No | Per-player season stat breakdown, recent form, upcoming fixtures |

`tourId` is `1` for the current season. `matchdayId` corresponds to
gameweek number 


MIT License
