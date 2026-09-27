from pathlib import Path

import pandas as pd
import pytest

from data import fmt_num, format_dates, parse_sheet, player_columns, plural, seasons, to_long
from tests.fixtures import EXPECTED_PLACES, sheet, sheet_raw

SNAPSHOT = Path(__file__).parent / 'baseline' / 'sheet_snapshot.csv'


def legacy_place_in_match(row, player):
    """place_in_match z main.py po Fazie 0 (punkt odniesienia dla to_long)."""
    row = row.dropna()
    position_list = sorted((row.iloc[j] for j in range(3, len(row))), reverse=True)
    for char in range(len(position_list)):
        if position_list[char] == row[player]:
            return char + 1


def test_parse_sheet_dates():
    df = sheet()
    assert df['date'].iloc[1] == pd.Timestamp(2023, 1, 3)  # "3.01.2023" bez zera wiodącego
    assert df['date'].iloc[0] == pd.Timestamp(2022, 12, 25)
    assert sheet_raw()['date'].iloc[0] == '25.12.2022'  # parse_sheet nie modyfikuje wejścia


def test_format_dates_roundtrip():
    assert format_dates(sheet())['date'].iloc[1] == '03.01.2023'


def test_player_columns_and_seasons():
    df = sheet()
    assert player_columns(df) == ['Ania', 'Bartek', 'Celina', 'Darek']
    assert seasons(df) == [2023, 2024]  # 2022 nie jest sezonem


def test_to_long_columns_and_match_id():
    long = to_long(sheet())
    assert list(long.columns) == ['match_id', 'date', 'game', 'n_players', 'player', 'score', 'place', 'won']
    # match_id z pozycji wiersza, mimo zduplikowanego indeksu arkusza (4, 4)
    assert sorted(long['match_id'].unique()) == list(range(8))
    assert long['match_id'].is_monotonic_increasing
    assert len(long) == sum(len(p) for p in EXPECTED_PLACES.values())


def test_to_long_places_with_ties():
    long = to_long(sheet())
    got = {m: dict(zip(g['player'], g['place'])) for m, g in long.groupby('match_id')}
    assert got == EXPECTED_PLACES


def test_won_includes_shared_first_place():
    long = to_long(sheet()).set_index(['match_id', 'player'])
    assert long.loc[(1, 'Ania'), 'won'] and long.loc[(1, 'Bartek'), 'won']
    assert not long.loc[(1, 'Celina'), 'won']
    assert long.loc[(6, 'Ania'), 'won'] and long.loc[(6, 'Darek'), 'won']


def test_n_players_from_sheet():
    # decyzja właściciela: źródłem prawdy jest liczba_graczy z arkusza (gra drużynowa w match 7)
    long = to_long(sheet())
    assert long.loc[long['match_id'] == 7, 'n_players'].unique().tolist() == [3]


@pytest.mark.parametrize('df_factory', [sheet, lambda: parse_sheet(pd.read_csv(SNAPSHOT, index_col=0))],
                         ids=['fixture', 'snapshot'])
def test_places_equal_legacy_place_in_match(df_factory):
    df = df_factory()
    long = to_long(df).set_index(['match_id', 'player'])['place']
    for pos in range(len(df)):
        row = df.iloc[pos]
        for player in row.iloc[3:].dropna().index:
            assert long[(pos, player)] == legacy_place_in_match(row, player), (pos, player)


@pytest.mark.parametrize('n, expected', [(1, 'gra'), (2, 'gry'), (4, 'gry'), (5, 'gier'), (12, 'gier'),
                                         (22, 'gry'), (25, 'gier'), (0, 'gier'), (112, 'gier'), (104, 'gry')])
def test_plural(n, expected):
    assert plural(n, 'gra', 'gry', 'gier') == expected


def test_fmt_num():
    assert fmt_num(66.5) == '66,5' and fmt_num(200 / 3) == '66,7' and fmt_num(90) == '90,0'
