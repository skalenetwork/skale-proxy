import json
import sqlite3
from datetime import UTC, date, datetime, timedelta

import pytest
import requests

from proxy import metrics
from proxy.metrics import COUNTER_FIELDS, SCHEMA, MetricsFile, collect, window

D = date(2026, 9, 28)
FULL = {D - timedelta(30): 100, D - timedelta(7): 400, D - timedelta(1): 900, D: 1000}


@pytest.mark.parametrize(
    ('history', 'days', 'expected'),
    [
        ({D: 5000}, 7, 0),
        (FULL, 7, 600),
        ({D - timedelta(9): 100, D: 300}, 7, 200),
        ({D - timedelta(1): 500, D: 400}, 1, 0),
    ],
)
def test_window(history: dict[date, int], days: int, expected: int) -> None:
    assert window(history, days) == expected


def test_collect(monkeypatch: pytest.MonkeyPatch) -> None:
    fetched = dict.fromkeys(COUNTER_FIELDS, '5')
    monkeypatch.setattr(metrics, 'counters', lambda *_: fetched)
    monkeypatch.setattr(metrics, 'get_json', lambda *_: None)
    monkeypatch.setattr(metrics, 'block_field', lambda *_: None)
    db = sqlite3.connect(':memory:')
    db.execute(SCHEMA)
    yesterday = str(datetime.now(UTC).date() - timedelta(1))
    db.execute(
        'INSERT INTO counters VALUES (?, ?, ?, ?)',
        ('c', '0xa', yesterday, json.dumps(fetched | {'transactions_count': '2'})),
    )
    meta = {'c': {'apps': {'app': {'contracts': ['0xa']}, 'site': {'alias': 's'}}}}
    previous: MetricsFile = {
        'metrics': {'c': {'chain_stats': {'n': 1}, 'apps_counters': {}}},
        'gas': 7,
        'last_updated': 0,
    }
    data = collect(requests.Session(), db, 'mainnet', ['c', 'd'], meta, previous, '')
    assert data is not None
    windows = ('transactions_today', 'transactions_last_7_days', 'transactions_last_30_days')
    counter = fetched | dict.fromkeys(windows, 3)
    assert data['metrics'] == {
        'c': {'chain_stats': {'n': 1}, 'apps_counters': {'app': {'0xa': counter}}}
    }
    assert data['gas'] == 7
    assert collect(requests.Session(), db, 'mainnet', ['c'], meta, data, '') is None
