"""Regresja na prawdziwych danych: zamrożony snapshot arkusza vs pliki w tests/baseline/."""
from pathlib import Path

import pandas as pd
import pytest

from data import parse_sheet, to_long
from stats import wsjg

BASELINE = Path(__file__).parent / 'baseline'


@pytest.fixture(scope='module')
def sheet():
    return parse_sheet(pd.read_csv(BASELINE / 'sheet_snapshot.csv', index_col=0))


def test_wsjg_all_games_matches_baseline(sheet):
    expected = pd.read_csv(BASELINE / 'wsjg_all.csv')
    pd.testing.assert_frame_equal(wsjg(to_long(sheet)), expected)


def test_wsjg_per_game_matches_baseline(sheet):
    expected = pd.read_csv(BASELINE / 'wsjg_by_game.csv')
    long = to_long(sheet)
    got = pd.concat([wsjg(long, game).assign(gra=game) for game in expected['gra'].unique()])
    pd.testing.assert_frame_equal(got[['gra', 'gracz', 'pkt_skutecznosci']].reset_index(drop=True), expected)
