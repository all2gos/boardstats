"""Smoke testy stron (streamlit AppTest) na zamrożonym snapshocie arkusza."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

REPO = Path(__file__).resolve().parent.parent
SNAPSHOT = REPO / 'tests' / 'baseline' / 'sheet_snapshot.csv'
PAGES = ['main.py', 'pages/tabela.py', 'pages/ogolne.py', 'pages/gracz.py', 'pages/gra.py', 'pages/ranking_elo.py',
         'pages/hall_of_fame.py', 'pages/wsjg.py', 'pages/program.py']

_read_csv = pd.read_csv


@pytest.fixture(autouse=True)
def snapshot_sheet(monkeypatch):
    def read_csv(path, *args, **kwargs):
        if isinstance(path, str) and 'docs.google.com' in path:
            path = SNAPSHOT
        return _read_csv(path, *args, **kwargs)
    monkeypatch.setattr(pd, 'read_csv', read_csv)
    monkeypatch.chdir(REPO)


def run(page):
    at = AppTest.from_file(str(REPO / page), default_timeout=120)
    at.run()
    return at


def widget(at, label):
    for coll in (at.radio, at.selectbox, at.multiselect, at.checkbox, at.text_input):
        for w in coll:
            if w.label == label:
                return w
    raise KeyError(label)


@pytest.mark.parametrize('page', PAGES)
def test_page_renders(page):
    assert not run(page).exception


def open_player(name):
    at = run('pages/gracz.py')
    widget(at, 'Wybierz gracza').set_value(name).run()
    return at


def info_texts(at):
    return [i.value for i in at.info]


def test_player_page_shows_stats():
    at = open_player('Raf Stottko')
    assert not at.exception
    assert not any('Współczynnik skuteczności' in m.value for m in at.markdown)  # WSJG usunięte ze strony gracza
    assert not at.button
    assert any('najlepszy wynik' in d.value.columns for d in at.dataframe)


@pytest.mark.parametrize('checkbox, message', [
    ('Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa!!!)', 'Wybierz co najmniej jedną grę.'),
    ('Zaznacz jeśli chcesz zobaczyć spis gier (gry) dla danego sezonu', 'Wybierz co najmniej jeden rok.'),
])
def test_player_page_empty_filter_shows_message(checkbox, message):
    at = open_player('Raf Stottko')
    widget(at, checkbox).check().run()
    assert not at.exception
    assert info_texts(at) == [message]


def test_player_page_filters_without_matches_show_message():
    at = open_player('Mati Stottko')
    widget(at, 'Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa!!!)').check().run()
    widget(at, 'Wybierz grę, która Cię interesuje').set_value(['ankh']).run()
    widget(at, 'Zaznacz jeśli chcesz zobaczyć spis gier (gry) dla danego sezonu').check().run()
    widget(at, 'Wybierz rok').set_value([2026]).run()
    assert not at.exception
    assert info_texts(at) == ['Brak partii dla wybranych filtrów.']


def test_table_newest_first():
    table = run('pages/tabela.py').dataframe[0].value
    sheet = pd.read_csv(SNAPSHOT, index_col=0)
    assert table['game'].iloc[0] == sheet['game'].iloc[-1]
    assert list(table.index) == list(sheet.index[::-1])


def test_player_select_placeholder_and_recency_order():
    at = run('pages/gracz.py')
    select = widget(at, 'Wybierz gracza')
    assert select.value is None and not at.checkbox and not at.dataframe
    # ostatnia partia snapshotu: kaskadia 26.09.2026 (Bezia, Hanza, Kasia i Tomek Wierczek) -> alfabetycznie
    assert list(select.options[:4]) == ['Bezia (ostatnio 26.09.2026)', 'Hanza (ostatnio 26.09.2026)',
                                        'Kasia Wierczek (ostatnio 26.09.2026)', 'Tomek Wierczek (ostatnio 26.09.2026)']
    assert select.options[4].endswith('(ostatnio 16.09.2026)')
    assert len(select.options) == 35


def test_elo_page_tables():
    at = run('pages/ranking_elo.py')
    current = at.dataframe[0].value
    assert list(current.columns) == ['elo']
    expected = pd.read_csv(REPO / 'tests' / 'baseline' / 'elo_current_open.csv', index_col=0,
                           float_precision='round_trip')
    pd.testing.assert_frame_equal(current, expected, check_names=False)
    widget(at, 'Dodatkowe statystyki').set_value('Maksymalne ELO w historii').run()
    max_elo = at.dataframe[0].value
    assert len(max_elo) == len(expected)  # także gracze, którzy nie przebili 1000
    assert (max_elo['max_elo'] <= 1000).any()
    assert max_elo['data'].notna().all()


def test_elo_history_in_expander():
    at = run('pages/ranking_elo.py')
    expander = next(e for e in at.expander if e.label == 'Historia zmian ELO')
    assert len(expander.dataframe) == 1 and len(expander.dataframe[0].value) == 297


def test_elo_chart_defaults_to_top5():
    at = run('pages/ranking_elo.py')
    select = widget(at, 'Zaznacz, jakich graczy ELO chcesz śledzić na wykresie')
    expected = pd.read_csv(REPO / 'tests' / 'baseline' / 'elo_current_open.csv')['gracz'].head(5).tolist()
    assert select.value == expected
    widget(at, 'Oś X').set_value('Data').run()
    assert not at.exception


def test_game_page_select_sorted_by_count():
    at = run('pages/gra.py')
    options = widget(at, 'Wybierz grę').options
    counts = [int(o.rsplit('(', 1)[1].split()[0]) for o in options]
    assert counts == sorted(counts, reverse=True)
    assert widget(at, 'Wybierz grę').value == options[0].rsplit(' (', 1)[0]


def test_game_page_summary():
    at = run('pages/gra.py')
    widget(at, 'Wybierz grę').set_value('brass').run()
    metrics = {m.label: m.value for m in at.metric}
    sheet = pd.read_csv(SNAPSHOT, index_col=0)
    brass = sheet[sheet['game'] == 'brass']
    metrics = {k: v for k, v in metrics.items() if k in ('Rozegrane partie', 'Pierwsza partia', 'Ostatnia partia')}
    assert metrics == {'Rozegrane partie': str(len(brass)), 'Pierwsza partia': '27.12.2022',
                       'Ostatnia partia': pd.to_datetime(brass['date'], format='%d.%m.%Y').max().strftime('%d.%m.%Y')}


def test_game_page_wsjg_matches_baseline():
    at = run('pages/gra.py')
    widget(at, 'Wybierz grę').set_value('kaskadia').run()
    expected = pd.read_csv(REPO / 'tests' / 'baseline' / 'wsjg_by_game.csv')
    expected = expected[expected['gra'] == 'kaskadia'][['gracz', 'pkt_skutecznosci']].reset_index(drop=True)
    got = next(d.value for d in at.dataframe if 'pkt_skutecznosci' in d.value.columns)
    pd.testing.assert_frame_equal(got.reset_index(drop=True), expected)


def test_player_page_best_per_game():
    at = open_player('Raf Stottko')
    best = next(d.value for d in at.dataframe if 'najlepszy wynik' in d.value.columns)
    assert best['partie'].is_monotonic_decreasing
    assert best['partie'].sum() == len(pd.read_csv(SNAPSHOT, index_col=0)['Raf Stottko'].dropna())
    assert list(best.columns) == ['gra', 'najlepszy wynik', 'miejsce', 'data', 'partie', '% wygranych']
    assert (best['miejsce'] >= 1).all() and best['% wygranych'].between(0, 100).all()


def test_player_page_best_per_game_game_filter():
    at = open_player('Raf Stottko')
    widget(at, 'Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa!!!)').check().run()
    widget(at, 'Wybierz grę, która Cię interesuje').set_value(['brass']).run()
    best = next(d.value for d in at.dataframe if 'najlepszy wynik' in d.value.columns)
    assert best['gra'].tolist() == ['brass']


def test_player_page_co_players_and_nemesis():
    at = open_player('Raf Stottko')
    mates = next(d.value for d in at.dataframe if 'wspólne partie' in d.value.columns)
    assert (mates['wyżej'] + mates['niżej'] + mates['remis'] == mates['wspólne partie']).all()
    top = mates.loc[mates['niżej'].idxmax()]
    assert any(m.value.startswith('Nemezis (nominalnie): ') and top['gracz'] in m.value for m in at.markdown)
    eligible = mates[mates['wspólne partie'] >= 5]
    rel = eligible.loc[(eligible['niżej'] / eligible['wspólne partie']).idxmax()]
    line = next(m.value for m in at.markdown if m.value.startswith('Nemezis (względnie): '))
    assert rel['gracz'] in line and f"{rel['niżej']} z {rel['wspólne partie']}" in line
    assert mates['% wyprzedzeń'].between(0, 100).all()


def test_hall_of_fame_shared_medals():
    at = run('pages/hall_of_fame.py')
    games = at.dataframe[0].value
    # 2023: Gosia i Mati po 56 partii -> wspólne srebro, brak brązu
    assert games.loc[2023].tolist() == ['Raf Stottko (62)', 'Gosia Stottko (56), Mati Stottko (56)', '']


def test_hall_of_fame_elo_min_games():
    at = run('pages/hall_of_fame.py')
    assert any('co najmniej 5 partiami' in c.value for c in at.caption)
    elo = at.dataframe[1].value
    # Dawid Węgrzyk ma w 2023 dokładnie 5 partii -> mieści się w progu (>= 5)
    assert elo.loc[2023, 'silver'].startswith('Dawid Węgrzyk (')


def test_hall_of_fame_records_section():
    at = run('pages/hall_of_fame.py')
    counts = next(d.value for d in at.dataframe if 'gry z rekordem' in d.value.columns
                  and d.value['gry z rekordem'].dtype.kind == 'i')
    games = pd.read_csv(SNAPSHOT, index_col=0)['game'].nunique()
    assert counts['gry z rekordem'].sum() >= games  # każda gra ma co najmniej jednego rekordzistę
    expander = next(e for e in at.expander if e.label == 'Które to gry')
    listing = expander.dataframe[0].value
    assert listing['gracz'].tolist() == counts['gracz'].tolist()
    first = listing.iloc[0]
    assert len(first['gry z rekordem'].split(', ')) == counts.iloc[0]['gry z rekordem']


def test_player_page_play_summary():
    at = open_player('Raf Stottko')
    raf = pd.read_csv(SNAPSHOT, index_col=0).dropna(subset=['Raf Stottko'])
    expected = f"Raf Stottko zagrał(a) w {raf['game'].nunique()} rodzajów gier, łącznie {len(raf)} razy."
    assert expected in [m.value for m in at.markdown]


def test_player_page_table_size_summary():
    at = open_player('Raf Stottko')
    raf = pd.read_csv(SNAPSHOT, index_col=0).dropna(subset=['Raf Stottko'])
    avg = f"{raf['liczba_graczy'].mean():.1f}".replace('.', ',')
    assert f'Średnio w partii {avg} graczy.' in [m.value for m in at.markdown]
    sizes = next(d.value for d in at.dataframe if list(d.value.columns) == ['liczba graczy', 'partie'])
    assert dict(zip(sizes['liczba graczy'], sizes['partie'])) == raf['liczba_graczy'].value_counts().to_dict()
    assert sizes['liczba graczy'].is_monotonic_increasing

def test_hall_of_fame_nemesis_section():
    at = run('pages/hall_of_fame.py')
    for kind in ('nominalnie', 'względnie'):
        expander = next(e for e in at.expander if e.label == f'Dla kogo ({kind})')
        listing = expander.dataframe[0].value
        counts = next(d.value for d in at.dataframe if list(d.value.columns) == ['gracz', 'liczba graczy']
                      and d.value['gracz'].tolist() == listing['gracz'].tolist())
        assert counts['liczba graczy'].is_monotonic_decreasing
        assert (listing['dla kogo'].str.split(', ').str.len() == counts['liczba graczy']).all()


def test_wsjg_page_has_explanation():
    at = run('pages/wsjg.py')
    expander = next(e for e in at.expander if e.label == 'Jak to jest liczone?')
    assert any('środku stawki' in m.value for m in expander.markdown)


def open_game(name):
    at = run('pages/gra.py')
    widget(at, 'Wybierz grę').set_value(name).run()
    return at


def game_counts_in_snapshot():
    return pd.read_csv(SNAPSHOT, index_col=0)['game'].value_counts()


def test_game_page_maturity_message():
    counts = game_counts_in_snapshot()
    mature_game = counts.index[0]
    young_game = counts[counts <= 10].index[0]
    assert any('uznajemy ją za dojrzałą' in i.value for i in open_game(mature_game).info)
    young = open_game(young_game)
    assert not young.info and any(f'(teraz: {counts[young_game]})' in c.value for c in young.caption)


def test_game_page_typical_score():
    counts = game_counts_in_snapshot()
    mature = open_game(counts.index[0])
    labels = [m.label for m in mature.metric]
    assert {'Średnia', 'Mediana', 'Średni wynik zwycięzcy'} <= set(labels)
    young = open_game(counts[counts <= 10].index[0])
    assert 'Mediana' not in [m.label for m in young.metric]


def test_game_page_scores_by_table_size():
    counts = game_counts_in_snapshot()
    table = next(d.value for d in open_game(counts.index[0]).dataframe if 'średni wynik zwycięzcy' in d.value.columns)
    assert table['partie'].sum() == counts.iloc[0]


def test_game_page_best_debut():
    counts = game_counts_in_snapshot()
    at = open_game(counts.index[0])
    assert any('pierwszej partii gracza' in c.value for c in at.caption)
    assert not any('pierwszej partii gracza' in c.value for c in open_game(counts[counts <= 10].index[0]).caption)


def test_game_page_mature_stats_in_expander():
    counts = game_counts_in_snapshot()
    at = open_game(counts.index[0])
    panel = next(e for e in at.expander if e.label.startswith('Więcej statystyk'))
    assert {m.label for m in panel.metric} == {'Średnia', 'Mediana', 'Średni wynik zwycięzcy'}
    scores = pd.read_csv(SNAPSHOT, index_col=0)
    scores = scores[scores['game'] == counts.index[0]].iloc[:, 3:].stack().dropna()
    fmt = lambda x: f'{x:.1f}'.replace('.', ',')
    iqr = f'{fmt(scores.quantile(0.25))}–{fmt(scores.quantile(0.75))}'
    assert any(f'w przedziale {iqr} (IQR, Q1–Q3)' in c.value for c in panel.caption)
    assert any('pierwszej partii gracza' in c.value for c in panel.caption)
    assert not any(e.label.startswith('Więcej statystyk') for e in open_game(counts[counts <= 10].index[0]).expander)


def test_hall_of_fame_games_player_counts():
    at = run('pages/hall_of_fame.py')
    frame = next(d.value for d in at.dataframe if list(d.value.index) == ['wszech czasów'])
    sheet = pd.read_csv(SNAPSHOT, index_col=0)
    per_game = {g: rows.iloc[:, 3:].notna().any().sum() for g, rows in sheet.groupby('game')}
    top = max(per_game.values())
    assert frame.loc['wszech czasów', 'gold'] == ', '.join(f'{g} ({top})' for g in sorted(per_game)
                                                           if per_game[g] == top)


def test_hall_of_fame_games_time_span():
    at = run('pages/hall_of_fame.py')
    frames = [d.value for d in at.dataframe if list(d.value.index) == ['wszech czasów']]
    assert len(frames) == 2
    sheet = pd.read_csv(SNAPSHOT, index_col=0)
    dates = pd.to_datetime(sheet['date'], format='%d.%m.%Y').groupby(sheet['game'])
    spans = (dates.max() - dates.min()).dt.days
    best = spans.idxmax()
    assert frames[1].loc['wszech czasów', 'gold'] == f'{best} ({spans[best]})'
