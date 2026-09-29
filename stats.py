"""Statystyki liczone na danych w formacie długim (data.to_long). Bez Streamlita.

Remisy w sortowaniu: tabele budowane są w kolejności graczy z arkusza, a potem sortowane,
tak jak wcześniej w main.py, żeby kolejność zremisowanych była taka sama jak w starych widokach.
"""
from collections import Counter
from itertools import combinations

import pandas as pd

PLACES_COLUMNS = ['miejsce', 'tyle_razy_gracz_zajal_to_miejsce']
MATURE_GAME_MATCHES = 10  # gra z WIĘCEJ niż tyloma partiami jest „dojrzała” (więcej statystyk)
NEMESIS_MIN_GAMES = 5  # minimalna liczba wspólnych partii dla nemezis względnego (decyzja właściciela)


def in_year(long_df, year):
    return long_df[long_df['date'].dt.year == year]


def matches(long_df):
    """Jeden wiersz na partię (match_id, date, game, n_players)."""
    return long_df.drop_duplicates('match_id')[['match_id', 'date', 'game', 'n_players']]


def game_counts(long_df):
    """Liczba rozegrań każdej gry, malejąco."""
    return matches(long_df)['game'].value_counts()


def player_game_counts(long_df, players):
    """Liczba partii każdego gracza (także 0), malejąco. Kolumny: index (gracz), count."""
    counts = long_df.groupby('player').size().reindex(players, fill_value=0)
    return counts.reset_index(name='count').rename(columns={'player': 'index'}).sort_values(['count'], ascending=False)


def player_places(long_df, player):
    """Ile razy gracz zajął każde miejsce. Indeks: miejsce."""
    places = long_df.loc[long_df['player'] == player, 'place']
    counts = places.value_counts(sort=False)
    table = pd.DataFrame({PLACES_COLUMNS[0]: counts.index, PLACES_COLUMNS[1]: counts.values})
    return table.sort_values(by='miejsce').set_index('miejsce')


def wsjg_value(player_long):
    """WSJG dla wierszy jednego gracza: środek stawki (n+1)/2 / średnie miejsce gracza * 100, zaokrąglone.

    Dla pustego wejścia rzuca ZeroDivisionError (strona gracza wcześniej pokazuje komunikat, TODO Z.8).
    """
    avg_place = (player_long['n_players'] + 1).mean() / 2
    your_place = int(player_long['place'].sum()) / len(player_long)
    return round(avg_place / your_place * 100)


def wsjg(long_df, game=None):
    """Ranking WSJG (gracz, pkt_skutecznosci), malejąco; opcjonalnie tylko dla jednej gry."""
    if game is not None:
        long_df = long_df[long_df['game'] == game]
    rows = [[player, wsjg_value(g)] for player, g in long_df.groupby('player', sort=False)]
    rows.sort(key=lambda row: (row[1], row[0]), reverse=True)
    return pd.DataFrame(data=rows, columns=['gracz', 'pkt_skutecznosci'])


def season_game_counts(long_df, year, players):
    """Liczba partii każdego gracza w danym roku (gracz, liczba_gier), malejąco."""
    counts = in_year(long_df, year).groupby('player').size().reindex(players, fill_value=0)
    table = pd.DataFrame({'gracz': players, 'liczba_gier': counts.values})
    return table.sort_values(by='liczba_gier', ascending=False)


def season_distinct_games(long_df, year, players):
    """Liczba różnych gier każdego gracza w danym roku (gracz, liczba_różnych_gier), malejąco."""
    counts = in_year(long_df, year).groupby('player')['game'].nunique().reindex(players, fill_value=0)
    table = pd.DataFrame({'gracz': players, 'liczba_różnych_gier': counts.values})
    return table.sort_values(by='liczba_różnych_gier', ascending=False)


def win_streaks(long_df):
    """Najdłuższa seria wygranych każdego gracza (kolejne jego partie wg match_id, won == True).

    Kolumny: gracz, dlugosc, od, do (daty pierwszej i ostatniej partii serii). Przy równych
    seriach jednego gracza liczy się wcześniejsza. Gracze bez wygranej mają dlugosc 0 i puste daty.
    Sortowanie: dlugosc malejąco, potem gracz.
    """
    rows = []
    for player, g in long_df.sort_values('match_id', kind='stable').groupby('player', sort=False):
        best, start, current, cur_start = (0, None, 0, None)
        best_end = None
        for won, date in zip(g['won'], g['date']):
            if won:
                if current == 0:
                    cur_start = date
                current += 1
                if current > best:
                    best, start, best_end = current, cur_start, date
            else:
                current = 0
        rows.append({'gracz': player, 'dlugosc': best, 'od': start, 'do': best_end})
    table = pd.DataFrame(rows, columns=['gracz', 'dlugosc', 'od', 'do'])
    return table.sort_values(['dlugosc', 'gracz'], ascending=[False, True]).reset_index(drop=True)


def players_by_recency(long_df):
    """Gracze od najświeższej partii (ostatni match_id z ich udziałem). Kolumny: player, last_match_id, last_date.

    Przy tej samej ostatniej partii kolejność alfabetyczna.
    """
    last = long_df.sort_values('match_id').groupby('player', sort=False).tail(1)
    table = last[['player', 'match_id', 'date']].rename(columns={'match_id': 'last_match_id', 'date': 'last_date'})
    return table.sort_values(['last_match_id', 'player'], ascending=[False, True]).reset_index(drop=True)


def game_summary(long_df, game):
    """Liczba rozegrań gry oraz daty pierwszej i ostatniej partii."""
    m = matches(long_df[long_df['game'] == game])
    return {'partie': len(m), 'pierwsza': m['date'].min(), 'ostatnia': m['date'].max()}


def game_player_table(long_df, game):
    """Dla jednej gry: gracz, partie, wygrane, % wygranych (wspólne 1. miejsce = wygrana).

    Sortowanie: partie malejąco, potem wygrane malejąco, potem gracz.
    """
    g = long_df[long_df['game'] == game].groupby('player')['won'].agg(partie='size', wygrane='sum')
    table = g.reset_index().rename(columns={'player': 'gracz'})
    table['wygrane'] = table['wygrane'].astype(int)
    table['% wygranych'] = (100 * table['wygrane'] / table['partie']).round(1)
    return table.sort_values(['partie', 'wygrane', 'gracz'], ascending=[False, False, True]).reset_index(drop=True)


def top_scores(long_df, game, n=5):
    """Najwyższe wyniki w grze: miejsce, gracz, wynik, data. Jeden gracz może zajmować kilka miejsc.

    Miejsca w rankingu 1-1-3; wpisy zremisowane na granicy n są pokazywane wszystkie.
    Przy równym wyniku wcześniejsza partia jest wyżej.
    """
    g = long_df[long_df['game'] == game].sort_values(['score', 'match_id', 'player'], ascending=[False, True, True])
    g = g.assign(miejsce=g['score'].rank(method='min', ascending=False).astype(int))
    g = g[g['miejsce'] <= n]
    return g.rename(columns={'player': 'gracz', 'score': 'wynik', 'date': 'data'})[
        ['miejsce', 'gracz', 'wynik', 'data']].reset_index(drop=True)


def best_scores(long_df):
    """Najlepszy wynik dla każdej pary (gra, gracz): gra, gracz, wynik, data (pierwsza partia z tym
    wynikiem), partie (liczba partii gracza w tej grze)."""
    g = long_df.sort_values(['score', 'match_id'], ascending=[False, True])
    best = g.drop_duplicates(['game', 'player'])[['game', 'player', 'score', 'date']]
    counts = long_df.groupby(['game', 'player']).size().rename('partie').reset_index()
    best = best.merge(counts, on=['game', 'player'])
    return best.rename(columns={'game': 'gra', 'player': 'gracz', 'score': 'wynik', 'date': 'data'})


def game_best_per_player(long_df, game):
    """Najlepszy wynik każdego gracza w danej grze (gracz, wynik, data), malejąco."""
    best = best_scores(long_df[long_df['game'] == game])
    return best.sort_values(['wynik', 'gracz'], ascending=[False, True])[['gracz', 'wynik', 'data']].reset_index(drop=True)


def lowest_winning_score(long_df, game):
    """Najniższy wynik, który dał wygraną w grze (gracz, wynik, data); przy remisie wszystkie wpisy."""
    won = long_df[(long_df['game'] == game) & long_df['won']]
    low = won[won['score'] == won['score'].min()].sort_values(['match_id', 'player'])
    return low.rename(columns={'player': 'gracz', 'score': 'wynik', 'date': 'data'})[
        ['gracz', 'wynik', 'data']].reset_index(drop=True)


def highest_losing_score(long_df, game):
    """Najwyższy wynik, który nie wygrał: gracz, wynik, data, zwycięzca, wynik zwycięzcy.

    Przy remisie wszystkie wpisy; kilku zwycięzców partii (wspólne 1. miejsce) wypisanych po przecinku.
    """
    g = long_df[long_df['game'] == game]
    lost = g[~g['won']]
    high = lost[lost['score'] == lost['score'].max()].sort_values(['match_id', 'player'])
    winners = g[g['won']].groupby('match_id').agg(zwycięzca=('player', ', '.join), **{'wynik zwycięzcy': ('score', 'first')})
    high = high.merge(winners, left_on='match_id', right_index=True)
    return high.rename(columns={'player': 'gracz', 'score': 'wynik', 'date': 'data'})[
        ['gracz', 'wynik', 'data', 'zwycięzca', 'wynik zwycięzcy']].reset_index(drop=True)


def player_best_per_game(long_df, player):
    """Najlepszy wynik gracza w każdej grze: gra, najlepszy wynik, miejsce, data, partie, % wygranych.

    long_df: partie wszystkich graczy (zakres, w którym liczymy ranking). miejsce = pozycja najlepszego
    wyniku gracza wśród najlepszych wyników wszystkich graczy w tej grze (ranking 1-1-3).
    Sortowanie malejąco po partiach.
    """
    best = best_scores(long_df)
    best['miejsce'] = best.groupby('gra')['wynik'].rank(method='min', ascending=False).astype(int)
    best = best[best['gracz'] == player].rename(columns={'wynik': 'najlepszy wynik'})
    won = long_df[long_df['player'] == player].groupby('game')['won'].mean().mul(100).round(1)
    best['% wygranych'] = best['gra'].map(won)
    return best.sort_values(['partie', 'gra'], ascending=[False, True])[
        ['gra', 'najlepszy wynik', 'miejsce', 'data', 'partie', '% wygranych']].reset_index(drop=True)


def co_players(long_df, player):
    """Współgracze i bilans bezpośredni: gracz, wspólne partie, wyżej / niżej / remis
    (z perspektywy `player`: „wyżej” = byłem wyżej w tej partii). Malejąco po wspólnych partiach."""
    mine = long_df.loc[long_df['player'] == player, ['match_id', 'place']].rename(columns={'place': 'my_place'})
    others = long_df[long_df['player'] != player].merge(mine, on='match_id')
    table = others.assign(wyżej=others['my_place'] < others['place'], niżej=others['my_place'] > others['place'],
                          remis=others['my_place'] == others['place'])
    table = table.groupby('player').agg(**{'wspólne partie': ('match_id', 'size'), 'wyżej': ('wyżej', 'sum'),
                                          'niżej': ('niżej', 'sum'), 'remis': ('remis', 'sum')})
    table = table.astype(int).reset_index().rename(columns={'player': 'gracz'})
    table['% wyprzedzeń'] = (100 * table['niżej'] / table['wspólne partie']).round(1)
    return table.sort_values(['wspólne partie', 'gracz'], ascending=[False, True]).reset_index(drop=True)


def nemesis(co_players_table):
    """Kto najczęściej mnie wyprzedzał: (gracze, ile razy) z tabeli co_players; przy remisie kilku graczy.

    Zwraca None, gdy nikt mnie nie wyprzedził.
    """
    most = co_players_table['niżej'].max() if len(co_players_table) else 0
    if most == 0:
        return None
    names = sorted(co_players_table.loc[co_players_table['niżej'] == most, 'gracz'])
    return names, int(most)


def nemesis_relative(co_players_table, min_games):
    """Kto najczęściej mnie wyprzedzał względnie (niżej / wspólne partie), spośród współgraczy z co najmniej
    min_games wspólnymi partiami: (gracze, % wyprzedzeń) albo None. Przy remisie kilku graczy."""
    eligible = co_players_table[co_players_table['wspólne partie'] >= min_games]
    if eligible.empty or eligible['niżej'].max() == 0:
        return None
    share = eligible['niżej'] / eligible['wspólne partie']
    names = sorted(eligible.loc[share == share.max(), 'gracz'])
    return names, round(100 * share.max(), 1)


MEDALS = ['gold', 'silver', 'bronze']


def medal_table(values):
    """Medale dla jednej kategorii i sezonu. values: Series gracz -> wynik (wyżej = lepiej, NaN = poza klasyfikacją).

    Ranking 1-1-3: zremisowani dzielą medal (wypisani alfabetycznie, po przecinku), a następny medal
    jest pomijany (dwa złota -> brak srebra, jest brąz). Brak kandydata -> pusta komórka.
    Obok gracza wynik zaokrąglony do liczby całkowitej, np. "Ania (47)".
    """
    values = values.dropna()
    return {medal: ', '.join(f"{name} ({round(values[name])})" for name in names)
            for medal, names in medal_winners(values).items()}


def medal_winners(values):
    """Kto dostaje który medal: {'gold': [...], 'silver': [...], 'bronze': [...]} (ranking 1-1-3, alfabetycznie).

    values: Series nazwa -> wynik (wyżej = lepiej, NaN = poza klasyfikacją).
    """
    values = values.dropna()
    ranks = values.rank(method='min', ascending=False)
    return {medal: sorted(values.index[ranks == place]) for place, medal in enumerate(MEDALS, start=1)}


def medal_frame(values_by_year):
    """Tabela medali: wiersze = sezony, kolumny = gold / silver / bronze."""
    return pd.DataFrame([medal_table(v) for v in values_by_year.values()], index=list(values_by_year),
                        columns=MEDALS)


def distinct_co_players(long_df):
    """Liczba różnych osób, z którymi gracz zagrał (Series gracz -> liczba)."""
    pairs = long_df[['match_id', 'player']].merge(long_df[['match_id', 'player']], on='match_id')
    pairs = pairs[pairs['player_x'] != pairs['player_y']]
    return pairs.groupby('player_x')['player_y'].nunique().rename_axis('gracz')


def group_counts(long_df, size):
    """Ile razy każda grupa `size` osób grała razem (wszyscy w tej samej partii, inni też mogli grać).

    Series: etykieta "A + B + ..." (alfabetycznie) -> liczba partii.
    """
    counter = Counter()
    for _, players in long_df.groupby('match_id')['player']:
        counter.update(combinations(sorted(players), size))
    return pd.Series({' + '.join(group): n for group, n in counter.items()}, dtype=float).rename_axis('grupa')


def streak_podium(long_df, n=3):
    """Podium najdłuższych serii wygranych (ranking 1-1-3, remisy wszystkie): miejsce, gracz, długość, od, do."""
    streaks = win_streaks(long_df)
    streaks = streaks[streaks['dlugosc'] > 0]
    streaks = streaks.assign(miejsce=streaks['dlugosc'].rank(method='min', ascending=False).astype(int))
    streaks = streaks[streaks['miejsce'] <= n].rename(columns={'dlugosc': 'długość'})
    return streaks[['miejsce', 'gracz', 'długość', 'od', 'do']].reset_index(drop=True)


def distinct_games_won(long_df):
    """Liczba różnych gier, które gracz wygrał (Series gracz -> liczba; tylko gracze z wygraną)."""
    return long_df[long_df['won']].groupby('player')['game'].nunique().rename_axis('gracz')


RECORD = 'rekord'
TOP_LOSING = 'najwyższy niewygrywający'


def record_holders(long_df):
    """Kto w której grze ma rekord wyniku i najwyższy niewygrywający wynik (remisy: wszyscy).

    Kolumny: gra, gracz, rodzaj (RECORD albo TOP_LOSING); jedna gra liczy się graczowi raz.
    """
    rows = []
    for game, g in long_df.groupby('game'):
        for player in g.loc[g['score'] == g['score'].max(), 'player'].unique():
            rows.append((game, player, RECORD))
        for player in highest_losing_score(long_df, game)['gracz'].unique():
            rows.append((game, player, TOP_LOSING))
    return pd.DataFrame(rows, columns=['gra', 'gracz', 'rodzaj'])


def record_counts(holders):
    """Tabela gracz -> liczba gier z rekordem / z najwyższym niewygrywającym wynikiem, malejąco."""
    counts = pd.crosstab(holders['gracz'], holders['rodzaj']).reindex(columns=[RECORD, TOP_LOSING], fill_value=0)
    table = counts.reset_index().rename(columns={RECORD: 'gry z rekordem',
                                                 TOP_LOSING: 'gry z najwyższym niewygrywającym wynikiem'})
    table.columns.name = None
    return table.sort_values(['gry z rekordem', 'gry z najwyższym niewygrywającym wynikiem', 'gracz'],
                             ascending=[False, False, True]).reset_index(drop=True)


def table_sizes(player_long):
    """Ile partii gracz rozegrał przy danej liczbie graczy (liczba_graczy z arkusza). Series n -> partie."""
    return player_long['n_players'].value_counts().sort_index().rename_axis('liczba graczy').rename('partie')


NOMINAL = 'nominalnie'
RELATIVE = 'względnie'


def nemesis_holders(long_df, min_games=NEMESIS_MIN_GAMES):
    """Dla każdego gracza jego nemezis nominalny i względny: kolumny nemezis, dla, rodzaj (NOMINAL / RELATIVE).

    Przy remisie każdy z zremisowanych jest nemezis tej osoby.
    """
    rows = []
    for player in long_df['player'].unique():
        mates = co_players(long_df, player)
        for kind, found in ((NOMINAL, nemesis(mates)), (RELATIVE, nemesis_relative(mates, min_games))):
            for name in (found[0] if found else []):
                rows.append((name, player, kind))
    return pd.DataFrame(rows, columns=['nemezis', 'dla', 'rodzaj'])


def nemesis_counts(holders, kind):
    """Dla ilu graczy każdy jest nemezis danego rodzaju: gracz, liczba graczy, dla kogo (malejąco)."""
    h = holders[holders['rodzaj'] == kind]
    table = h.groupby('nemezis')['dla'].agg(**{'liczba graczy': 'size', 'dla kogo': lambda s: ', '.join(sorted(s))})
    table = table.reset_index().rename(columns={'nemezis': 'gracz'})
    return table.sort_values(['liczba graczy', 'gracz'], ascending=[False, True]).reset_index(drop=True)


def is_mature(n_matches):
    """Czy gra jest „dojrzała”: więcej niż MATURE_GAME_MATCHES partii."""
    return n_matches > MATURE_GAME_MATCHES


def match_results(long_df, game):
    """Każda partia gry: match_id, data, liczba graczy (z arkusza), średni wynik, wynik zwycięzcy."""
    g = long_df[long_df['game'] == game]
    per = g.groupby('match_id').agg(data=('date', 'first'), **{'liczba graczy': ('n_players', 'first'),
                                                              'średni wynik': ('score', 'mean'),
                                                              'wynik zwycięzcy': ('score', 'max')})
    return per.reset_index()


def score_summary(long_df, game):
    """Typowy wynik w grze: średnia, mediana, Q1, Q3, IQR wszystkich wyników i średni wynik zwycięzcy."""
    scores = long_df.loc[long_df['game'] == game, 'score']
    q1, q3 = scores.quantile(0.25), scores.quantile(0.75)
    return {'średnia': scores.mean(), 'mediana': scores.median(), 'Q1': q1, 'Q3': q3, 'IQR': q3 - q1,
            'średni wynik zwycięzcy': match_results(long_df, game)['wynik zwycięzcy'].mean()}


def scores_by_table_size(long_df, game):
    """Dla każdej liczby graczy (z arkusza): partie, średni wynik (wszystkie wyniki), średni wynik zwycięzcy."""
    g = long_df[long_df['game'] == game]
    results = match_results(long_df, game)
    table = results.groupby('liczba graczy').agg(partie=('match_id', 'size'),
                                                 **{'średni wynik zwycięzcy': ('wynik zwycięzcy', 'mean')})
    table.insert(1, 'średni wynik', g.groupby('n_players')['score'].mean())
    return table.reset_index()


def best_debut(long_df, game):
    """Najwyższy wynik w pierwszej partii gracza w tę grę (gracz, wynik, data); przy remisie wszyscy."""
    g = long_df[long_df['game'] == game].sort_values('match_id')
    debuts = g.drop_duplicates('player')
    best = debuts[debuts['score'] == debuts['score'].max()].sort_values(['match_id', 'player'])
    return best.rename(columns={'player': 'gracz', 'score': 'wynik', 'date': 'data'})[
        ['gracz', 'wynik', 'data']].reset_index(drop=True)


def game_player_counts(long_df):
    """Ilu różnych graczy kiedykolwiek zagrało w każdą grę (Series gra -> liczba)."""
    return long_df.groupby('game')['player'].nunique().rename_axis('gra')


def game_time_spans(long_df):
    """Liczba dni między pierwszą a ostatnią partią każdej gry (Series gra -> dni)."""
    dates = long_df.groupby('game')['date']
    return (dates.max() - dates.min()).dt.days.rename_axis('gra')


def pair_matches(long_df):
    """Każda para graczy w każdej wspólnej partii: gracz_a, gracz_b (alfabetycznie), match_id, date, game."""
    rows = []
    for match_id, g in long_df.groupby('match_id'):
        date, game = g['date'].iloc[0], g['game'].iloc[0]
        rows.extend((a, b, match_id, date, game) for a, b in combinations(sorted(g['player']), 2))
    return pd.DataFrame(rows, columns=['gracz_a', 'gracz_b', 'match_id', 'date', 'game'])


def edge_weights(pairs, now, half_life_days=None):
    """Krawędzie grafu współgraczy: gracz_a, gracz_b, partie, waga, ostatnia (data ostatniej wspólnej partii).

    waga = suma po wspólnych partiach 0.5 ** (wiek w dniach / half_life_days); bez zaniku (None) waga = partie.
    """
    age = ((pd.Timestamp(now) - pairs['date']).dt.total_seconds() / 86400).clip(lower=0)
    decay = 1.0 if half_life_days is None else 0.5 ** (age / half_life_days)
    edges = pairs.assign(waga=decay).groupby(['gracz_a', 'gracz_b']).agg(
        partie=('match_id', 'size'), waga=('waga', 'sum'), ostatnia=('date', 'max'))
    return edges.reset_index().sort_values(['waga', 'gracz_a', 'gracz_b'], ascending=[False, True, True],
                                           ignore_index=True)


def player_connections(long_df):
    """Połączenia gracza: każda partia z każdą inną osobą = 1 połączenie. Kolumny: gracz, połączenia, partie."""
    sizes = long_df.groupby('match_id')['player'].transform('size')
    table = long_df.assign(połączenia=sizes - 1).groupby('player').agg(
        połączenia=('połączenia', 'sum'), partie=('match_id', 'size'))
    table = table.reset_index().rename(columns={'player': 'gracz'})
    return table.sort_values(['połączenia', 'gracz'], ascending=[False, True], ignore_index=True)


def game_connections(long_df):
    """Połączenia w grze: w każdej partii każda para uczestników = 1 połączenie. Kolumny: gra, połączenia, partie."""
    sizes = long_df.groupby('match_id').agg(game=('game', 'first'), k=('player', 'size'))
    sizes['połączenia'] = sizes['k'] * (sizes['k'] - 1) // 2
    table = sizes.groupby('game').agg(połączenia=('połączenia', 'sum'), partie=('k', 'size'))
    table = table.reset_index().rename(columns={'game': 'gra'})
    return table.sort_values(['połączenia', 'gra'], ascending=[False, True], ignore_index=True)
