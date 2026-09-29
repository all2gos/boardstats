import datetime as dt

import pandas as pd
import pytest

from data import to_long
from tests.fixtures import sheet
from titles import (ALL_TIME, GAMES, GENERAL, TITLES, TRIO, medal_records, medal_tally, past_seasons,
                    season_champions, title_records)


@pytest.fixture(scope='module')
def records():
    df = sheet()
    return medal_records(df, to_long(df), past_seasons(df, today=dt.date(2026, 9, 29)))


def medals_of(records, category, period):
    r = records[(records['kategoria'] == category) & (records['okres'] == period)]
    return {m: sorted(r.loc[r['medal'] == m, 'gracz']) for m in ('gold', 'silver', 'bronze')}


def test_past_seasons_skip_2022_and_current_year():
    assert past_seasons(sheet(), today=dt.date(2026, 9, 29)) == [2023, 2024]
    assert past_seasons(sheet(), today=dt.date(2024, 5, 1)) == [2023]


def test_season_category_medals(records):
    # 2024: Ania 3 partie, Bartek/Celina/Darek po 2 -> złoto Ania, trzy srebra, bez brązu
    assert medals_of(records, GAMES, 2024) == {'gold': ['Ania'], 'silver': ['Bartek', 'Celina', 'Darek'],
                                               'bronze': []}


def test_group_medals_go_to_members_once(records):
    # trio 2024: Ania+Bartek+Celina 2 razy (złoto); ABD, ACD, BCD po 1 (wspólne srebro)
    # -> Ania ma srebro z dwóch trójek, ale liczy się raz
    assert medals_of(records, TRIO, 2024) == {'gold': ['Ania', 'Bartek', 'Celina'],
                                              'silver': ['Ania', 'Bartek', 'Celina', 'Darek'], 'bronze': []}
    assert not records.duplicated().any()


def test_alltime_categories_present(records):
    assert set(records.loc[records['okres'] == ALL_TIME, 'kategoria']) >= {'Najdłuższa seria zwycięstw',
                                                                          'Rekordy w grach'}


def test_titles_partition_all_categories(records):
    categories = [c for _, cats in TITLES.values() for c in cats]
    assert len(categories) == len(set(categories))                   # każda kategoria w jednym tytule
    assert set(records['kategoria']) <= set(categories)
    assert len(title_records(records, GENERAL)) == sum(len(title_records(records, t)) for t in TITLES)


def test_medal_tally_olympic_order():
    r = pd.DataFrame({'kategoria': 'k', 'okres': 1, 'medal': ['gold', 'silver', 'silver', 'silver', 'gold', 'bronze',
                                                               'bronze', 'bronze', 'bronze'],
                      'gracz': ['A', 'A', 'A', 'A', 'B', 'B', 'C', 'C', 'C']})
    tally = medal_tally(r)
    # A i B po 1 złocie, A ma więcej srebra; C ma 3 medale, ale bez złota jest za A i B
    assert tally.values.tolist() == [['A', 1, 3, 0, 4], ['B', 1, 0, 1, 2], ['C', 0, 0, 3, 3]]
    assert list(tally.columns) == ['gracz', '🥇', '🥈', '🥉', 'razem']


def test_season_champions():
    r = pd.DataFrame({'kategoria': 'k', 'okres': [2023, 2023, 2023, 2024, 2024],
                      'medal': ['gold', 'gold', 'silver', 'gold', 'gold'], 'gracz': ['A', 'B', 'B', 'A', 'B']})
    champions = season_champions(r, [2023, 2024, 2025])
    assert champions.loc[2023, 'zdobywca tytułu'] == 'B (🥇1 🥈1)'
    assert champions.loc[2024, 'zdobywca tytułu'] == 'A (🥇1), B (🥇1)'   # remis: obaj
    assert champions.loc[2025, 'zdobywca tytułu'] == ''                  # brak medali
