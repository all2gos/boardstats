import streamlit as st
from data import load_raw, player_columns, to_long
from stats import (NEMESIS_MIN_GAMES, NOMINAL, RECORD, RELATIVE, TOP_LOSING, distinct_co_players,
                   distinct_games_won, game_player_counts, game_time_spans, group_counts, in_year, matches,
                   medal_frame, nemesis_counts, nemesis_holders, record_counts, record_holders,
                   season_distinct_games, season_game_counts, streak_podium)
from titles import MIN_SEASON_GAMES, past_seasons, season_elo

DATE_COLUMNS = {c: st.column_config.DateColumn(c, format='DD.MM.YYYY') for c in ('od', 'do')}

df = load_raw()
long = to_long(df)
players = player_columns(df)


def positive(table, column):
    """Wyniki jako Series gracz -> wartość; 0 oznacza brak udziału, więc poza klasyfikacją."""
    values = table.set_index('gracz')[column]
    return values[values > 0]


st.write('Każda kategoria to podsumowanie wszystkich sezonów (poza tym aktualnie trwającym)')

st.write('### Liczba gier w sezonie')

years = past_seasons(df)

for year in years:
    st.write(f"W {year} roku rozegrano łącznie {len(matches(in_year(long, year)))} gier")

st.write('----------------------------------------------------------')
st.write('Gracze z najwiekszą liczbą rozegranych gier w sezonie')
st.write(medal_frame({year: positive(season_game_counts(long, year, players), 'liczba_gier') for year in years}))

st.write('### Najlepsze ELO w sezonie')
st.caption(f'Liczą się gracze z co najmniej {MIN_SEASON_GAMES} partiami w sezonie.')

st.write(medal_frame({year: season_elo(df, long, year) for year in years}))
st.write('### Największa liczba RÓŻNYCH gier w sezonie')

st.write(medal_frame({year: positive(season_distinct_games(long, year, players), 'liczba_różnych_gier')
                      for year in years}))

st.write('### Najwięcej różnych współgraczy w sezonie')
st.write(medal_frame({year: distinct_co_players(in_year(long, year)) for year in years}))

st.write('### Najczęściej grające razem')
for size, name in [(2, 'Duo'), (3, 'Trio'), (4, 'Czwórka')]:
    st.write(f'#### {name}')
    st.write(medal_frame({year: group_counts(in_year(long, year), size) for year in years}))

st.write('### Najdłuższa seria zwycięstw (wszech czasów)')
st.caption('Kolejne partie gracza (tylko te, w których grał), wszystkie wygrane; wspólne 1. miejsce też się liczy.')
st.dataframe(streak_podium(long), hide_index=True, column_config=DATE_COLUMNS)

st.write('### Kolekcjoner: najwięcej różnych gier WYGRANYCH w sezonie')
st.write(medal_frame({year: distinct_games_won(in_year(long, year)) for year in years}))

st.write('### Rekordy w grach (wszech czasów)')
st.caption('W ilu grach gracz ma rekord wyniku i w ilu najwyższy wynik, który nie wygrał partii. '
           'Liczone ze wszystkich partii, także z bieżącego sezonu; przy remisie gra liczy się każdemu.')
holders = record_holders(long)
st.dataframe(record_counts(holders), hide_index=True)
with st.expander('Które to gry'):
    games_list = holders.sort_values('gra').groupby(['gracz', 'rodzaj'])['gra'].agg(', '.join).unstack()
    games_list = games_list.reindex(columns=[RECORD, TOP_LOSING]).fillna('')
    games_list.columns.name = None
    games_list = games_list.reindex(record_counts(holders)['gracz']).reset_index()
    st.dataframe(games_list.rename(columns={RECORD: 'gry z rekordem',
                                            TOP_LOSING: 'gry z najwyższym niewygrywającym wynikiem'}),
                 hide_index=True)

st.write('### Nemezis (wszech czasów)')
st.caption('Dla ilu graczy ktoś jest nemezis, liczone ze wszystkich partii. Nominalnie: najwięcej razy wyprzedził '
           f'danego gracza; względnie: najwyższy odsetek wyprzedzeń we wspólnych partiach (min. {NEMESIS_MIN_GAMES} '
           'wspólnych partii). Przy remisie liczy się każdemu.')
nemeses = nemesis_holders(long)
for kind in (NOMINAL, RELATIVE):
    st.write(f'#### {kind.capitalize()}')
    counts = nemesis_counts(nemeses, kind)
    st.dataframe(counts[['gracz', 'liczba graczy']], hide_index=True)
    with st.expander(f'Dla kogo ({kind})'):
        st.dataframe(counts[['gracz', 'dla kogo']], hide_index=True)

st.write('## Hall of Fame gier')
st.caption('Liczone ze wszystkich partii, także z bieżącego sezonu.')
st.write('### Najwięcej różnych graczy')
st.write(medal_frame({'wszech czasów': game_player_counts(long)}))

st.write('### Najdłużej grane (od pierwszej do ostatniej partii)')
st.caption('W nawiasie liczba dni między pierwszą a ostatnią partią.')
st.write(medal_frame({'wszech czasów': game_time_spans(long)}))
