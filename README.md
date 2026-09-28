To celebrate the first ever official WSL fantasy football game, I sifted through the network requests and minified JS bundles until I had enough data to make my own, auto-updating fun-fact dashboard.  This is for fun and does not access logged-in user data or private league info, nor is it affiliated with, endorsed by, or supported by WSL Football.

Especially useful for spotlighting high-scoring WSL2 players who I might have missed otherwise, it starts with the players who scored the most while being selected the least (and vice versa), and includes superlatives like points per million £ pricetag and biggest change in ownership %. 

I used GitHub Actions to automate taking data snapshots before/after gamedays and then trigger a re-render, so that I could host the whole thing on GitHub Pages.  Standings from previous weeks can be toggled through at any time, and I made layouts which work for mobile and desktop.


### What I'm accessing

Public feeds (`gaming.wslfootball.com/feeds/...`):

| Feed | URL pattern | Notes |
|---|---|---|
| Manifest | `/feeds/live/mixapi/mixapi_{tourId}.json` | Cache-buster version string per feed name; no data itself |
| Matchday roster | `/feeds/players/matchday_{lang}_{tourId}_{matchdayId}.json?v=3` | **Main dataset.** All ~744 players: price, ownership %, cumulative points, form |
| Player detail | `/feeds/popup/stats/player_{lang}_{tourId}_{playerId}.json` | Per-player season stat breakdown, recent form, upcoming fixtures |
| Config | `/feeds/config/web/configurations.json` | Club colour hex codes, image paths, player list columns |
| Teams/competitions | `/feeds/filters/teams/competition/{lang}_{tourId}.json` | Canonical team + competition names, IDs, crest/imagery paths |
| Live scoring | `/feeds/live/score/scoring.json` | In-play per-player scoring breakdown; empty array when no match is live |
| Home widget | `/feeds/home/widgets/1.json?v=2` | Current matchday/leg IDs, deadlines, top-3 overall leaderboard; shape needs re-verifying |
| Fixtures | `/feeds/fixtures/fixtures_{lang}_{tourId}.json?v=3` | Inferred only, not yet confirmed; full fixture list |

Gated feeds (`gaming.wslfootball.com/fantasy/services/...`, require `x-game-token`):

| Feed | URL pattern | Notes |
|---|---|---|
| Public league standings | `/fantasy/services/leagues/public/{leagueId}/global` | e.g. "Barclays Season Race" overall league |
| Matchday scoring status | `/fantasy/services/gameplay/{OVERALL_LEAGUE_ID}/played-matchdays` | `totalPoints: null` means that matchday isn't officially finalized yet |

`tourId` is `1` for the current season. `matchdayId` corresponds to
gameweek number

### How it updates
All displayed numbers are calculated using the data from a set of json files which represent how the data looked before and after each game week.  These snapshots are kept and updated via the below process:

[`scripts/take_snapshot.py`](scripts/take_snapshot.py) runs daily at 06:00
UTC via [GitHub Actions](.github/workflows/data-snapshot.yml) 
Each run:

- Fetches current matchday and its deadline from the home widget feed.
- If the matchday has changed, that's the cue to take an "after" snapshot for the matchday
  that just ended
- If the current matchday's deadline is within the next 30 hours, a
  "before" snapshot is saved.
- Commits any new/changed files under `frontend/public/data/` back to the repo

So data is only updated once a day at most, and only around matchday deadlines/rollovers.


MIT License
