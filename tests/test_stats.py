"""Wartości oczekiwane policzone ręcznie dla tests/fixtures.py (patrz EXPECTED_PLACES)."""
import pandas as pd
import pytest

from data import to_long
from stats import (game_counts, in_year, matches, player_game_counts, player_places, players_by_recency,
                   season_distinct_games, season_game_counts, win_streaks, wsjg, wsjg_value, game_summary,
                   game_player_table, top_scores, best_scores, game_best_per_player, lowest_winning_score,
                   highest_losing_score, player_best_per_game, co_players, nemesis, nemesis_relative, nemesis_holders, nemesis_counts, is_mature, match_results, score_summary, scores_by_table_size, best_debut, game_player_counts, game_time_spans,
                   pair_matches, edge_weights, player_connections, game_connections,
                   medal_table, medal_frame, distinct_co_players, group_counts,
                   streak_podium, distinct_games_won, record_holders, record_counts, table_sizes)
from tests.fixtures import sheet

PLAYERS = ['Ania', 'Bartek', 'Celina', 'Darek']


@pytest.fixture
def long():
    return to_long(sheet())


def as_dict(table, key='gracz', value='pkt_skutecznosci'):
    return dict(zip(table[key], table[value]))


def test_wsjg_all_games(long):
    # Ania: (n+1)/2 = 27/14, średnie miejsce 10/7 -> 135; Darek: 1.9 / 2.4 -> 79
    table = wsjg(long)
    assert list(table['gracz']) == ['Ania', 'Bartek', 'Celina', 'Darek']
    assert as_dict(table) == {'Ania': 135, 'Bartek': 114, 'Celina': 104, 'Darek': 79}


def test_wsjg_single_game(long):
    assert as_dict(wsjg(long, 'azul')) == {'Ania': 200, 'Bartek': 100, 'Celina': 86}


def test_wsjg_rounding_half_to_even(long):
    # Bartek w brass: 2.25 / 2 * 100 = 112.5 -> round() -> 112; Darek w kaskadii: 87.5 -> 88
    assert as_dict(wsjg(long, 'brass')) == {'Celina': 150, 'Ania': 120, 'Bartek': 112, 'Darek': 75}
    assert as_dict(wsjg(long, 'kaskadia'))['Darek'] == 88


def test_wsjg_ties_sorted_by_name_descending():
    tie = pd.DataFrame({'match_id': [0, 0], 'player': ['Ala', 'Ola'], 'place': [1, 1], 'n_players': [2, 2],
                        'game': ['x', 'x']})
    assert list(wsjg(tie)['gracz']) == ['Ola', 'Ala']


def test_wsjg_value_empty_raises(long):
    with pytest.raises(ZeroDivisionError):  # strona gracza nie wywołuje tego dla pustych danych (Z.8)
        wsjg_value(long.iloc[0:0])


def test_player_places(long):
    table = player_places(long, 'Ania')
    assert table.index.name == 'miejsce'
    assert table['tyle_razy_gracz_zajal_to_miejsce'].to_dict() == {1: 4, 2: 3}
    assert player_places(long, 'Darek')['tyle_razy_gracz_zajal_to_miejsce'].to_dict() == {1: 2, 3: 2, 4: 1}


def test_counts(long):
    assert game_counts(long).to_dict() == {'azul': 3, 'brass': 3, 'kaskadia': 2}
    table = player_game_counts(long, PLAYERS)
    assert dict(zip(table['index'], table['count'])) == {'Ania': 7, 'Bartek': 6, 'Celina': 6, 'Darek': 5}
    assert table['count'].is_monotonic_decreasing
    assert len(matches(in_year(long, 2023))) == 4


def test_season_counts_include_zero_and_distinct_games(long):
    assert as_dict(season_game_counts(long, 2024, PLAYERS), value='liczba_gier') == \
        {'Ania': 3, 'Bartek': 2, 'Celina': 2, 'Darek': 2}
    assert as_dict(season_game_counts(long, 2022, PLAYERS), value='liczba_gier') == \
        {'Ania': 1, 'Bartek': 1, 'Celina': 1, 'Darek': 0}
    assert as_dict(season_distinct_games(long, 2024, PLAYERS), value='liczba_różnych_gier') == \
        {'Ania': 2, 'Bartek': 2, 'Celina': 2, 'Darek': 1}


def test_win_streaks(long):
    table = win_streaks(long).set_index('gracz')
    assert list(table.index) == ['Ania', 'Darek', 'Bartek', 'Celina']
    assert table['dlugosc'].to_dict() == {'Ania': 2, 'Darek': 2, 'Bartek': 1, 'Celina': 1}
    # Ania ma dwie serie długości 2 -> liczy się wcześniejsza; wspólne 1. miejsce to wygrana
    assert (table.loc['Ania', 'od'], table.loc['Ania', 'do']) == (pd.Timestamp(2022, 12, 25), pd.Timestamp(2023, 1, 3))
    # seria Darka przechodzi przez partie innych graczy (m5) i koniec roku
    assert (table.loc['Darek', 'od'], table.loc['Darek', 'do']) == (pd.Timestamp(2023, 2, 5), pd.Timestamp(2024, 3, 2))


def test_win_streaks_player_without_win(long):
    table = win_streaks(long[long['player'] == 'Celina'].assign(won=False)).set_index('gracz')
    assert table.loc['Celina', 'dlugosc'] == 0 and pd.isna(table.loc['Celina', 'od'])


def test_players_by_recency(long):
    table = players_by_recency(long)
    # ostatnia partia (m7) — Ania, Bartek, Celina, Darek grali w niej wszyscy -> alfabetycznie
    assert list(table['player']) == ['Ania', 'Bartek', 'Celina', 'Darek']
    assert set(table['last_match_id']) == {7}
    few = players_by_recency(long[long['match_id'] <= 3])
    # Bartek, Celina, Darek w m3; Ania ostatnio w m2
    assert list(few['player']) == ['Bartek', 'Celina', 'Darek', 'Ania']
    assert few.set_index('player').loc['Ania', 'last_date'] == pd.Timestamp(2023, 1, 10)


def test_game_summary(long):
    assert game_summary(long, 'brass') == {'partie': 3, 'pierwsza': pd.Timestamp(2023, 1, 10),
                                           'ostatnia': pd.Timestamp(2024, 3, 20)}
    assert game_summary(long, 'kaskadia')['partie'] == 2  # dwie partie tego samego dnia


def test_game_player_table(long):
    table = game_player_table(long, 'brass')
    assert table.to_dict('records') == [
        {'gracz': 'Ania', 'partie': 3, 'wygrane': 1, '% wygranych': 33.3},
        {'gracz': 'Darek', 'partie': 3, 'wygrane': 1, '% wygranych': 33.3},
        {'gracz': 'Bartek', 'partie': 2, 'wygrane': 1, '% wygranych': 50.0},
        {'gracz': 'Celina', 'partie': 2, 'wygrane': 1, '% wygranych': 50.0},
    ]


def test_top_scores_with_ties_at_boundary(long):
    top5 = top_scores(long, 'brass')
    assert top5[['miejsce', 'gracz', 'wynik']].values.tolist() == [
        [1, 'Celina', 120.0], [2, 'Ania', 100.0], [3, 'Bartek', 90.0], [3, 'Darek', 90.0], [5, 'Bartek', 70.0]]
    assert top5['data'].iloc[0] == pd.Timestamp(2023, 1, 10)
    assert len(top_scores(long, 'brass', n=3)) == 4   # remis 90-90 na granicy: obaj
    assert len(top_scores(long, 'brass', n=6)) == 7   # remis 60-60 na 6. miejscu: obaj


def test_best_scores(long):
    best = best_scores(long).set_index(['gra', 'gracz'])
    assert best.loc[('azul', 'Ania')].tolist() == [50.0, pd.Timestamp(2024, 3, 1), 3]
    # remis wyniku z samym sobą: pierwsza partia z tym wynikiem
    assert best.loc[('brass', 'Darek'), 'data'] == pd.Timestamp(2023, 1, 10)
    assert best.loc[('kaskadia', 'Ania'), 'wynik'] == -5.0


def test_game_best_per_player(long):
    table = game_best_per_player(long, 'brass')
    assert table[['gracz', 'wynik']].values.tolist() == [['Celina', 120.0], ['Ania', 100.0], ['Bartek', 90.0],
                                                         ['Darek', 90.0]]


def test_lowest_winning_score(long):
    # brass: wygrane 120 (m2), 10 i 10 (m6, wspólne 1. miejsce), 70 (m7)
    assert lowest_winning_score(long, 'brass').values.tolist() == [
        ['Ania', 10.0, pd.Timestamp(2024, 3, 2)], ['Darek', 10.0, pd.Timestamp(2024, 3, 2)]]
    # kaskadia: Bartek wygrał 23.5, Darek wygrał 0 -> zero jest najniższe
    assert lowest_winning_score(long, 'kaskadia').values.tolist() == [['Darek', 0.0, pd.Timestamp(2023, 2, 5)]]


def test_highest_losing_score(long):
    assert highest_losing_score(long, 'brass').values.tolist() == [
        ['Ania', 100.0, pd.Timestamp(2023, 1, 10), 'Celina', 120.0]]
    # azul: najwyższy przegrany wynik 30 (Bartek, m0) i remis 35-35 na 1. miejscu w m1 nie jest porażką
    assert highest_losing_score(long, 'azul')[['gracz', 'wynik', 'zwycięzca']].values.tolist() == [
        ['Bartek', 30.0, 'Ania']]


def test_highest_losing_score_shared_winners():
    df = pd.DataFrame({'match_id': [0, 0, 0], 'game': ['x'] * 3, 'player': ['A', 'B', 'C'], 'score': [5.0, 5.0, 4.0],
                       'won': [True, True, False], 'date': [pd.Timestamp(2024, 1, 1)] * 3})
    assert highest_losing_score(df, 'x')[['gracz', 'zwycięzca', 'wynik zwycięzcy']].values.tolist() == [
        ['C', 'A, B', 5.0]]


def test_player_best_per_game(long):
    table = player_best_per_game(long, 'Ania')
    assert list(table.columns) == ['gra', 'najlepszy wynik', 'miejsce', 'data', 'partie', '% wygranych']
    # azul: najlepsze A 50, C 50, B 35 -> Ania ex aequo 1.; brass: C 120, A 100 -> 2.; kaskadia: A -5 ostatnia (4.)
    # wygrane Ani: azul 3/3, brass 1/3 (m6), kaskadia 0/1
    assert table[['gra', 'najlepszy wynik', 'miejsce', 'partie', '% wygranych']].values.tolist() == [
        ['azul', 50.0, 1, 3, 100.0], ['brass', 100.0, 2, 3, 33.3], ['kaskadia', -5.0, 4, 1, 0.0]]
    # remis na miejscu: Darek i Bartek mają w brass po 90 -> obaj 3.
    assert player_best_per_game(long, 'Darek').set_index('gra').loc['brass', 'miejsce'] == 3


def test_co_players(long):
    # kolumny: gracz, wspólne partie, wyżej, niżej, remis (z perspektywy wybranego gracza)
    # + ostatnia kolumna: % wyprzedzeń = niżej / wspólne partie
    assert co_players(long, 'Ania').values.tolist() == [['Bartek', 5, 3, 1, 1, 20.0], ['Celina', 5, 2, 1, 2, 20.0],
                                                        ['Darek', 4, 2, 1, 1, 25.0]]
    assert co_players(long, 'Darek').values.tolist() == [['Ania', 4, 1, 2, 1, 50.0], ['Bartek', 3, 0, 2, 1, 66.7],
                                                         ['Celina', 3, 0, 3, 0, 100.0]]


def test_nemesis(long):
    assert nemesis(co_players(long, 'Darek')) == (['Celina'], 3)
    assert nemesis(co_players(long, 'Ania')) == (['Bartek', 'Celina', 'Darek'], 1)  # remis
    only_wins = long[long['match_id'] == 0]
    assert nemesis(co_players(only_wins, 'Ania')) is None  # nikt Ani nie wyprzedził


def test_nemesis_relative(long):
    darek = co_players(long, 'Darek')
    assert nemesis_relative(darek, 3) == (['Celina'], 100.0)
    assert nemesis_relative(darek, 4) == (['Ania'], 50.0)   # próg odcina Celinę i Bartka (3 wspólne partie)
    assert nemesis_relative(darek, 5) is None               # nikt nie ma 5 wspólnych partii
    ania = co_players(long, 'Ania')
    assert nemesis_relative(ania, 4) == (['Darek'], 25.0)   # względnie Darek, choć nominalnie remis trzech
    assert nemesis_relative(ania, 5) == (['Bartek', 'Celina'], 20.0)


@pytest.mark.parametrize('values, expected', [
    ({'A': 5, 'B': 4, 'C': 3, 'D': 1}, {'gold': 'A (5)', 'silver': 'B (4)', 'bronze': 'C (3)'}),
    ({'B': 5, 'A': 5, 'C': 3, 'D': 1}, {'gold': 'A (5), B (5)', 'silver': '', 'bronze': 'C (3)'}),  # 2 złota
    ({'A': 5, 'B': 4, 'C': 4, 'D': 1}, {'gold': 'A (5)', 'silver': 'B (4), C (4)', 'bronze': ''}),  # 2 srebra
    ({'A': 5, 'B': 5, 'C': 5, 'D': 1}, {'gold': 'A (5), B (5), C (5)', 'silver': '', 'bronze': ''}),
    ({'A': 5, 'B': 4, 'C': 3, 'D': 3}, {'gold': 'A (5)', 'silver': 'B (4)', 'bronze': 'C (3), D (3)'}),
    ({'A': 5, 'B': None}, {'gold': 'A (5)', 'silver': '', 'bronze': ''}),                          # NaN / za mało
    ({}, {'gold': '', 'silver': '', 'bronze': ''}),
    ({'A': 1260.7, 'B': 1215.2}, {'gold': 'A (1261)', 'silver': 'B (1215)', 'bronze': ''}),         # ELO -> int
])
def test_medal_table_ties(values, expected):
    assert medal_table(pd.Series(values, dtype=float)) == expected


def test_medal_frame():
    frame = medal_frame({2023: pd.Series({'A': 2.0, 'B': 1.0}), 2024: pd.Series({'B': 3.0, 'A': 3.0})})
    assert frame.loc[2023].tolist() == ['A (2)', 'B (1)', ''] and frame.loc[2024].tolist() == ['A (3), B (3)', '', '']


def test_medal_frame_season_with_too_few_players(long):
    # sezon z jedną partią dwóch graczy (dawniej iloc[2] rzucał IndexError)
    tiny = long[long['match_id'] == 6]
    counts = season_game_counts(tiny, 2024, PLAYERS).set_index('gracz')['liczba_gier']
    frame = medal_frame({2024: counts[counts > 0]})
    assert frame.loc[2024].tolist() == ['Ania (1), Darek (1)', '', '']
    assert medal_frame({2024: pd.Series(dtype=float)}).loc[2024].tolist() == ['', '', '']


def test_distinct_co_players(long):
    two = long[long['match_id'].isin([1, 3])]  # m1: Ania, Bartek, Celina; m3: Bartek, Celina, Darek
    assert distinct_co_players(two).to_dict() == {'Ania': 2, 'Bartek': 3, 'Celina': 3, 'Darek': 2}


def test_group_counts(long):
    y2024 = in_year(long, 2024)  # m5: Ania, Bartek, Celina; m6: Ania, Darek; m7: wszyscy czworo
    assert group_counts(y2024, 2).to_dict() == {'Ania + Bartek': 2, 'Ania + Celina': 2, 'Bartek + Celina': 2,
                                                'Ania + Darek': 2, 'Bartek + Darek': 1, 'Celina + Darek': 1}
    assert group_counts(y2024, 3)['Ania + Bartek + Celina'] == 2
    assert group_counts(y2024, 4).to_dict() == {'Ania + Bartek + Celina + Darek': 1}
    assert group_counts(long[long['match_id'] == 6], 3).empty  # partia dwuosobowa nie tworzy trójki


def test_streak_podium(long):
    all_time = streak_podium(long)
    assert all_time[['miejsce', 'gracz', 'długość']].values.tolist() == [
        [1, 'Ania', 2], [1, 'Darek', 2], [3, 'Bartek', 1], [3, 'Celina', 1]]
    # w sezonie 2024 seria Darka z 2023 się nie liczy: każdy sezon osobno
    season = streak_podium(in_year(long, 2024))
    assert season[['miejsce', 'gracz', 'długość']].values.tolist() == [
        [1, 'Ania', 2], [2, 'Bartek', 1], [2, 'Celina', 1], [2, 'Darek', 1]]
    assert (season.loc[0, 'od'], season.loc[0, 'do']) == (pd.Timestamp(2024, 3, 1), pd.Timestamp(2024, 3, 2))


def test_distinct_games_won(long):
    # 2024: Ania wygrała azul (m5) i brass (m6); Bartek brass (m7); Celina azul (m5); Darek brass (m6)
    assert distinct_games_won(in_year(long, 2024)).to_dict() == {'Ania': 2, 'Bartek': 1, 'Celina': 1, 'Darek': 1}


def test_record_holders_and_counts(long):
    holders = record_holders(long)
    records = holders[holders['rodzaj'] == 'rekord']
    # azul: rekord 50 ex aequo Ania i Celina (m5); brass: Celina 120; kaskadia: Bartek 23.5
    assert sorted(map(tuple, records[['gra', 'gracz']].values)) == [
        ('azul', 'Ania'), ('azul', 'Celina'), ('brass', 'Celina'), ('kaskadia', 'Bartek')]
    losing = holders[holders['rodzaj'] == 'najwyższy niewygrywający']
    assert sorted(map(tuple, losing[['gra', 'gracz']].values)) == [
        ('azul', 'Bartek'), ('brass', 'Ania'), ('kaskadia', 'Celina')]
    table = record_counts(holders)
    assert table.values.tolist() == [['Celina', 2, 1], ['Ania', 1, 1], ['Bartek', 1, 1]]  # Darek bez żadnego
    assert list(table.columns) == ['gracz', 'gry z rekordem', 'gry z najwyższym niewygrywającym wynikiem']


def test_table_sizes(long):
    sizes = table_sizes(long[long['player'] == 'Ania'])
    assert sizes.to_dict() == {2: 2, 3: 4, 4: 1}


def test_nemesis_holders_and_counts(long):
    holders = nemesis_holders(long, min_games=3)
    nominal = nemesis_counts(holders, 'nominalnie')
    # nominalnie: Ania -> Bartek, Celina, Darek (remis); Bartek -> Ania; Celina -> Bartek; Darek -> Celina
    assert nominal.values.tolist() == [['Bartek', 2, 'Ania, Celina'], ['Celina', 2, 'Ania, Darek'],
                                       ['Ania', 1, 'Bartek'], ['Darek', 1, 'Ania']]
    relative = nemesis_counts(holders, 'względnie')
    # względnie (min. 3 wspólne): Ania -> Darek 25%; Bartek -> Ania 60%; Celina -> Bartek 66.7%; Darek -> Celina 100%
    assert relative.values.tolist() == [['Ania', 1, 'Bartek'], ['Bartek', 1, 'Celina'], ['Celina', 1, 'Darek'],
                                        ['Darek', 1, 'Ania']]
    # domyślny próg 5: Darek ma najwyżej 4 wspólne partie, więc nie ma nemezis względnego i sam nim nie jest;
    # Ania -> Bartek i Celina (po 20%), Bartek -> Ania (60%), Celina -> Bartek (66.7%)
    assert nemesis_counts(nemesis_holders(long), 'względnie').values.tolist() == [
        ['Bartek', 2, 'Ania, Celina'], ['Ania', 1, 'Bartek'], ['Celina', 1, 'Ania']]


def test_is_mature_boundary():
    assert not is_mature(10) and is_mature(11)  # „powyżej 10 partii”


def test_match_results_and_score_summary(long):
    # brass: m2 (100, 90, 120, 90), m6 (10, 10), m7 (60, 70, 60, 50)
    results = match_results(long, 'brass')
    assert results[['match_id', 'liczba graczy', 'średni wynik', 'wynik zwycięzcy']].values.tolist() == [
        [2, 4, 100.0, 120.0], [6, 2, 10.0, 10.0], [7, 3, 60.0, 70.0]]
    summary = score_summary(long, 'brass')
    assert summary['średnia'] == 66.0 and summary['mediana'] == 65.0
    assert (summary['Q1'], summary['Q3'], summary['IQR']) == (52.5, 90.0, 37.5)
    assert summary['średni wynik zwycięzcy'] == pytest.approx(200 / 3)


def test_scores_by_table_size(long):
    table = scores_by_table_size(long, 'brass')
    assert list(table.columns) == ['liczba graczy', 'partie', 'średni wynik', 'średni wynik zwycięzcy']
    assert table.values.tolist() == [[2, 1, 10.0, 10.0], [3, 1, 60.0, 70.0], [4, 1, 100.0, 120.0]]
    azul = scores_by_table_size(long, 'azul')  # trzy partie w trójkę: 40/30/20, 35/35/10, 50/20/50
    assert azul.values.tolist() == [[3, 3, pytest.approx(290 / 9), pytest.approx(125 / 3)]]


def test_best_debut(long):
    # brass: wszyscy debiutowali w m2 (100, 90, 120, 90) -> Celina 120
    assert best_debut(long, 'brass').values.tolist() == [['Celina', 120.0, pd.Timestamp(2023, 1, 10)]]
    # azul: debiuty w m0 (Ania 40, Bartek 30, Celina 20); późniejsze 50 Ani się nie liczy
    assert best_debut(long, 'azul')[['gracz', 'wynik']].values.tolist() == [['Ania', 40.0]]
    # kaskadia: Bartek 23.5 (m3) — wyższe niż debiut Ani -5 (m4)
    assert best_debut(long, 'kaskadia')['gracz'].tolist() == ['Bartek']


def test_game_player_counts_medals(long):
    counts = game_player_counts(long)
    assert counts.to_dict() == {'azul': 3, 'brass': 4, 'kaskadia': 4}
    assert medal_frame({'wszech czasów': counts}).loc['wszech czasów'].tolist() == [
        'brass (4), kaskadia (4)', '', 'azul (3)']


def test_game_time_spans_medals(long):
    # azul: 25.12.2022 -> 01.03.2024 = 432 dni; brass: 10.01.2023 -> 20.03.2024 = 435; kaskadia: jeden dzień = 0
    spans = game_time_spans(long)
    assert spans.to_dict() == {'azul': 432, 'brass': 435, 'kaskadia': 0}
    assert medal_frame({'wszech czasów': spans}).loc['wszech czasów'].tolist() == [
        'brass (435)', 'azul (432)', 'kaskadia (0)']


def test_pair_matches_and_edges(long):
    pairs = pair_matches(long)
    assert len(pairs) == 26  # 3 + 3 + 6 + 3 + 1 + 3 + 1 + 6
    edges = edge_weights(pairs, now=pd.Timestamp(2024, 3, 20)).set_index(['gracz_a', 'gracz_b'])
    # bez zaniku waga = liczba wspólnych partii (zgodnie z co_players)
    assert edges['partie'].to_dict() == {('Bartek', 'Celina'): 6, ('Ania', 'Bartek'): 5, ('Ania', 'Celina'): 5,
                                         ('Ania', 'Darek'): 4, ('Bartek', 'Darek'): 3, ('Celina', 'Darek'): 3}
    assert (edges['waga'] == edges['partie']).all()
    assert edges.loc[('Ania', 'Darek'), 'ostatnia'] == pd.Timestamp(2024, 3, 20)


def test_edge_weights_decay(long):
    now = pd.Timestamp(2024, 3, 20)
    edges = edge_weights(pair_matches(long), now=now, half_life_days=182.5).set_index(['gracz_a', 'gracz_b'])
    # Ania–Darek: m2 10.01.2023, m4 05.02.2023, m6 02.03.2024, m7 20.03.2024
    ages = [(now - pd.Timestamp(d)).days for d in ('2023-01-10', '2023-02-05', '2024-03-02', '2024-03-20')]
    assert edges.loc[('Ania', 'Darek'), 'waga'] == pytest.approx(sum(0.5 ** (a / 182.5) for a in ages))
    assert edges.loc[('Ania', 'Darek'), 'partie'] == 4
    # partia z dziś waży 1, sprzed pół roku 0.5
    today = pd.DataFrame({'gracz_a': ['X', 'X'], 'gracz_b': ['Y', 'Y'], 'match_id': [0, 1],
                          'date': [now, now - pd.Timedelta(days=182.5)], 'game': ['g', 'g']})
    assert edge_weights(today, now, 182.5)['waga'].iloc[0] == pytest.approx(1.5)


def test_player_and_game_connections(long):
    players = player_connections(long)
    assert players.values.tolist() == [['Ania', 14, 7], ['Bartek', 14, 6], ['Celina', 14, 6], ['Darek', 10, 5]]
    games = game_connections(long)
    assert games.values.tolist() == [['brass', 13, 3], ['azul', 9, 3], ['kaskadia', 4, 2]]
    assert players['połączenia'].sum() == 2 * games['połączenia'].sum()  # każde połączenie ma dwa końce
