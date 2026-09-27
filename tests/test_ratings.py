from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from data import parse_sheet
from elo import elo
from ratings import compute_elo
from tests.fixtures import sheet

BASELINE = Path(__file__).parent / 'baseline'


def legacy_elo_tab(df, year=None):
    """Pętla z zakładki ELO sprzed refaktoru (punkt odniesienia)."""
    elo_table = {p: np.nan for p in df.columns[3:]}
    elo_history = [elo_table.copy()]
    rows = df if year is None else df[df['date'].dt.year == year]
    for i in range(len(rows)):
        elo_table = elo(rows.iloc[i], elo_table, df)
        elo_history.append(elo_table.copy())
    return pd.DataFrame(data=elo_history)


def compute(df, year=None):
    return compute_elo.__wrapped__(df, year) if hasattr(compute_elo, '__wrapped__') else compute_elo(df, year)


def test_first_match_by_hand():
    # 3 nowych graczy po 1000: Ania wygrywa 2 pojedynki przy oczekiwanym 1 -> 64 * 1,
    # mnożnik nowicjusza max(ln(1/1)+4, 1) = 4, pierwsza partia w tę grę -> 0.2, dzielone przez (3-1)
    history, _ = compute(sheet())
    assert history.iloc[0].isna().all()
    assert history.iloc[1][['Ania', 'Bartek', 'Celina']].tolist() == [1025.6, 1000.0, 974.4]
    assert np.isnan(history.iloc[1]['Darek'])


@pytest.mark.parametrize('year', [None, 2023, 2024])
def test_matches_legacy_loop(year):
    df = sheet()
    history, current = compute(df, year)
    expected = legacy_elo_tab(df, year)
    pd.testing.assert_frame_equal(history, expected, check_exact=True)
    assert current.columns.tolist() == ['elo']
    assert current['elo'].is_monotonic_decreasing and current['elo'].notna().all()
    assert current['elo'].to_dict() == expected.iloc[-1].dropna().to_dict()


def test_season_starts_from_zero_but_counts_games_by_date():
    df = sheet()
    history, _ = compute(df, 2024)
    assert len(history) == 1 + (df['date'].dt.year == 2024).sum()
    assert history.iloc[0].isna().all()
    # Liczniki partii po dacie na całym arkuszu: w 2024 Ania nie jest już nowicjuszem,
    # więc jej zmiana w pierwszej partii 2024 różni się od startu całkiem od zera.
    fresh = compute(df[df['date'].dt.year == 2024], None)[0]
    assert history.iloc[1]['Ania'] != fresh.iloc[1]['Ania']


@pytest.fixture(scope='module')
def snapshot():
    return parse_sheet(pd.read_csv(BASELINE / 'sheet_snapshot.csv', index_col=0))


@pytest.mark.parametrize('tag', ['open', '2023', '2024', '2025', '2026'])
def test_matches_baseline(snapshot, tag):
    history, current = compute(snapshot, None if tag == 'open' else int(tag))
    expected_history = pd.read_csv(BASELINE / f'elo_history_{tag}.csv', index_col=0, float_precision='round_trip')
    pd.testing.assert_frame_equal(history, expected_history, check_exact=True, check_names=False)
    expected_current = pd.read_csv(BASELINE / f'elo_current_{tag}.csv', index_col=0, float_precision='round_trip')
    pd.testing.assert_frame_equal(current, expected_current, check_exact=True, check_names=False)


def test_elo_chart_data():
    from ratings import elo_chart_data
    df = sheet()
    history, _ = compute(df, 2024)
    data = elo_chart_data(history, df, 2024)
    assert list(data.columns) == ['gracz', 'elo', 'numer_partii', 'data', 'gra']
    assert sorted(data['numer_partii'].unique()) == [1, 2, 3]  # trzy partie w 2024
    first = data[data['numer_partii'] == 1].set_index('gracz')
    assert set(first.index) == {'Ania', 'Bartek', 'Celina'}  # Darek jeszcze nie grał w 2024
    assert (first['gra'] == 'azul').all() and (first['data'] == pd.Timestamp(2024, 3, 1)).all()
    assert first.loc['Ania', 'elo'] == history.iloc[1]['Ania']
    # po wejściu gracz ma wartość w każdym kolejnym kroku
    assert len(data[data['gracz'] == 'Darek']) == 2


def test_max_elo_table():
    from ratings import max_elo_table
    df = sheet()
    history, _ = compute(df)
    table = max_elo_table(history, df)
    assert list(table.columns) == ['max_elo', 'data']
    assert table['max_elo'].to_dict() == history.max().dropna().to_dict()
    assert table['max_elo'].is_monotonic_decreasing
    for player, row in table.iterrows():
        # data = pierwsza partia, po której gracz miał swoje maksimum
        step = history.index[history[player] == row['max_elo']][0]
        assert row['data'] == df['date'].iloc[step - 1]
