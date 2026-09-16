"""
Self-contained snapshot orchestrator for the scheduled GitHub Actions job.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

BASE_URL = 'https://gaming.wslfootball.com'
TOUR_ID = 1
LANG = 'en'
OVERALL_LEAGUE_ID = 'dd46193a-44de-4dfe-9526-927feb7933a2'

DATA_DIR = Path('frontend/public/data')
STATE_PATH = DATA_DIR / 'state.json'
BEFORE_WINDOW_HOURS = 30

HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.wslfootball.com/',
    'User-Agent': 'Mozilla/5.0 (compatible; wsl-fantasy-dashboard-bot/0.1)',
}


def get_json(path: str, params: dict | None = None) -> dict:
    response = requests.get(f'{BASE_URL}{path}', params=params, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.json()


def get_tour_details() -> dict:
    payload = get_json(f'/feeds/home/widgets/{TOUR_ID}.json', params={'v': 2})
    details = payload.get('Data', {}).get('Value', {})
    if 'currMdId' not in details or 'deadlineDate' not in details:
        raise RuntimeError(
            'The WSL widgets feed did not include currMdId and deadlineDate.'
        )
    return details


def get_played_matchdays() -> list[dict]:
    return get_json(f'/fantasy/services/gameplay/{OVERALL_LEAGUE_ID}/played-matchdays')['Data']['Value']


def is_matchday_finalized(matchday_id: int) -> bool:
    return any(
        row.get('matchdayId') == matchday_id and row.get('totalPoints') is not None
        for row in get_played_matchdays()
    )


def get_matchday_players(matchday_id: int) -> list[dict]:
    return get_json(
        f'/feeds/players/matchday_{LANG}_{TOUR_ID}_{matchday_id}.json',
        params={'v': 3},
    )['Data']['Value']


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {'tracked_matchday': None, 'before_taken': False, 'after_taken': False}


def save_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def save_snapshot(matchday_id: int, label: str, players: list[dict]) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f'matchday_{matchday_id}_{label}.json'
    path.write_text(json.dumps(players, indent=2))
    canonical_path = DATA_DIR / f'matchday_{matchday_id}.json'
    canonical_path.write_text(json.dumps(players, indent=2))
    snapshots = sorted(
        (
            {'matchday': int(snapshot.stem.split('_')[1]), 'path': snapshot.name}
            for snapshot in DATA_DIR.glob('matchday_[0-9]*.json')
            if len(snapshot.stem.split('_')) == 2
        ),
        key=lambda snapshot: snapshot['matchday'],
    )
    (DATA_DIR / 'snapshots.json').write_text(json.dumps(snapshots, indent=2))
    print(f'Saved {len(players)} players -> {path}')
    return path


def main() -> None:
    tour = get_tour_details()
    current_matchday = tour['currMdId']
    deadline = datetime.fromisoformat(tour['deadlineDate'].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    state = load_state()

    if state.get('tracked_matchday') != current_matchday:
        print(f'New matchday detected: {current_matchday} (was {state.get("tracked_matchday")})')
        state = {'tracked_matchday': current_matchday, 'before_taken': False, 'after_taken': False}

    took_something = False

    if not state['before_taken'] and now <= deadline <= now + timedelta(hours=BEFORE_WINDOW_HOURS):
        save_snapshot(current_matchday, 'before', get_matchday_players(current_matchday))
        state['before_taken'] = True
        took_something = True

    if not state['after_taken'] and is_matchday_finalized(current_matchday):
        save_snapshot(current_matchday, 'after', get_matchday_players(current_matchday))
        state['after_taken'] = True
        took_something = True

    save_state(state)

    if not took_something:
        print(
            f"Nothing to do right now. Matchday {current_matchday}, "
            f"deadline {deadline.isoformat()}, now {now.isoformat()}, "
            f"before_taken={state['before_taken']}, after_taken={state['after_taken']}"
        )

    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as output:
            output.write(f"changed={'true' if took_something else 'false'}\n")


if __name__ == '__main__':
    main()