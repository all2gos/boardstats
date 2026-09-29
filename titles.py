"""Tytuły łączące medale z kategorii Hall of Fame (strona „Tytuły i odznaczenia”)."""
import datetime as dt

import pandas as pd

from data import player_columns, seasons
from ratings import compute_elo
from stats import (MEDALS, NOMINAL, RELATIVE, distinct_co_players, distinct_games_won, group_counts, in_year,
                   medal_winners, nemesis_counts, nemesis_holders, record_counts, record_holders,
                   season_distinct_games, season_game_counts, win_streaks)

MIN_SEASON_GAMES = 5  # minimalna liczba partii w sezonie, żeby liczyć się do medalu za sezonowe ELO
ALL_TIME = 'wszech czasów'
MEDAL_ICONS = {'gold': '🥇', 'silver': '🥈', 'bronze': '🥉'}

GAMES = 'Liczba gier w sezonie'
ELO = 'Najlepsze ELO w sezonie'
DISTINCT_GAMES = 'Najwięcej różnych gier w sezonie'
DISTINCT_MATES = 'Najwięcej różnych współgraczy w sezonie'
DUO, TRIO, QUAD = 'Duo', 'Trio', 'Czwórka'
COLLECTOR = 'Kolekcjoner (różne gry wygrane)'
STREAK = 'Najdłuższa seria zwycięstw'
RECORDS = 'Rekordy w grach'
NEMESIS_NOM = 'Nemezis (nominalnie)'
NEMESIS_REL = 'Nemezis (względnie)'
GROUPS = {DUO: 2, TRIO: 3, QUAD: 4}

TITLES = {
    'OMNIBUS': ('różnorodność', [DISTINCT_GAMES, DISTINCT_MATES, COLLECTOR]),
    'MARATOŃCZYK': ('aktywność', [GAMES, DUO, TRIO, QUAD]),
    'ARCYMISTRZ': ('skuteczność', [ELO, STREAK, RECORDS, NEMESIS_NOM, NEMESIS_REL]),
}
GENERAL = 'Klasyfikacja generalna'


def past_seasons(df, today=None):
    """Zakończone sezony (bez bieżącego roku), jak w Hall of Fame."""
    year = (today or dt.date.today()).year
    return [y for y in seasons(df) if y < year]


def season_elo(df, long_df, year):
    """Sezonowe ELO graczy, którzy rozegrali w sezonie co najmniej MIN_SEASON_GAMES partii."""
    elo = compute_elo(df, year)[1]['elo']
    games = season_game_counts(long_df, year, player_columns(df)).set_index('gracz')['liczba_gier']
    return elo[games.reindex(elo.index) >= MIN_SEASON_GAMES]


def _positive(table, column):
    values = table.set_index('gracz')[column]
    return values[values > 0]


def season_categories(df, long_df, years):
    """{kategoria: {sezon: Series nazwa -> wynik}} dla kategorii sezonowych."""
    players = player_columns(df)
    cats = {
        GAMES: {y: _positive(season_game_counts(long_df, y, players), 'liczba_gier') for y in years},
        ELO: {y: season_elo(df, long_df, y) for y in years},
        DISTINCT_GAMES: {y: _positive(season_distinct_games(long_df, y, players), 'liczba_różnych_gier')
                         for y in years},
        DISTINCT_MATES: {y: distinct_co_players(in_year(long_df, y)) for y in years},
        COLLECTOR: {y: distinct_games_won(in_year(long_df, y)) for y in years},
    }
    for name, size in GROUPS.items():
        cats[name] = {y: group_counts(in_year(long_df, y), size) for y in years}
    return cats


def alltime_categories(long_df):
    """{kategoria: Series gracz -> wynik} dla kategorii wszech czasów (wszystkie partie)."""
    streaks = win_streaks(long_df).set_index('gracz')['dlugosc']
    records = record_counts(record_holders(long_df)).set_index('gracz')['gry z rekordem']
    nemeses = nemesis_holders(long_df)
    return {
        STREAK: streaks[streaks > 0],
        RECORDS: records[records > 0],
        NEMESIS_NOM: nemesis_counts(nemeses, NOMINAL).set_index('gracz')['liczba graczy'],
        NEMESIS_REL: nemesis_counts(nemeses, RELATIVE).set_index('gracz')['liczba graczy'],
    }


def medal_records(df, long_df, years):
    """Wszystkie medale: kategoria, okres (sezon albo ALL_TIME), medal, gracz.

    W kategoriach grupowych (duo/trio/czwórka) medal grupy dostaje każdy jej członek, ale gracz
    ma w danej kategorii i okresie najwyżej jeden medal danego koloru.
    """
    per_period = [(cat, year, values) for cat, by_year in season_categories(df, long_df, years).items()
                  for year, values in by_year.items()]
    per_period += [(cat, ALL_TIME, values) for cat, values in alltime_categories(long_df).items()]
    rows = []
    for cat, period, values in per_period:
        for medal, names in medal_winners(values).items():
            for name in names:
                members = name.split(' + ') if cat in GROUPS else [name]
                rows.extend((cat, period, medal, member) for member in members)
    records = pd.DataFrame(rows, columns=['kategoria', 'okres', 'medal', 'gracz'])
    return records.drop_duplicates(ignore_index=True)


def medal_tally(records):
    """Klasyfikacja olimpijska: gracz, 🥇, 🥈, 🥉, razem (najpierw złota, potem srebra, brązy, potem alfabet)."""
    icons = [MEDAL_ICONS[m] for m in MEDALS]
    counts = pd.crosstab(records['gracz'], records['medal']).reindex(columns=MEDALS, fill_value=0)
    counts.columns = icons
    counts['razem'] = counts.sum(axis=1)
    table = counts.reset_index().rename(columns={'index': 'gracz'})
    table.columns.name = None
    return table.sort_values(icons + ['gracz'], ascending=[False, False, False, True], ignore_index=True)


def title_records(records, title):
    """Medale składające się na tytuł (GENERAL = wszystkie)."""
    if title == GENERAL:
        return records
    return records[records['kategoria'].isin(TITLES[title][1])]


def season_champions(records, years):
    """Zdobywca(y) tytułu w każdym sezonie: najlepszy wg klasyfikacji olimpijskiej z medali tego sezonu."""
    rows = []
    for year in years:
        tally = medal_tally(records[records['okres'] == year])
        if tally.empty:
            rows.append((year, ''))
            continue
        icons = [MEDAL_ICONS[m] for m in MEDALS]
        best = tuple(tally.iloc[0][icons])
        top = tally[tally[icons].apply(tuple, axis=1) == best]
        medals = ' '.join(f'{icon}{n}' for icon, n in zip(icons, best) if n)
        rows.append((year, ', '.join(f'{name} ({medals})' for name in top['gracz'])))
    return pd.DataFrame(rows, columns=['sezon', 'zdobywca tytułu']).set_index('sezon')
