from datetime import date, timedelta

import pytest

from proxy.metrics import window

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
