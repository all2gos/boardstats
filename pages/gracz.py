import streamlit as st
from data import DATE_FORMAT, load_raw, seasons, format_dates, plural, to_long
from stats import (NEMESIS_MIN_GAMES, co_players, game_counts, nemesis, nemesis_relative, player_best_per_game,
                   player_places, players_by_recency, table_sizes)

DATE_COLUMN = st.column_config.DateColumn('data', format='DD.MM.YYYY')

df = load_raw()
long = to_long(df)

recent = players_by_recency(long)
last_played = dict(zip(recent['player'], recent['last_date']))
player = st.selectbox('Wybierz gracza', recent['player'], index=None, placeholder='Wybierz gracza…',
                      format_func=lambda p: f"{p} (ostatnio {last_played[p].strftime(DATE_FORMAT)})")

if player is not None:
    player_long = long[long['player'] == player]
    filtr = st.checkbox('Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa!!!)')
    if filtr:
        games = st.multiselect('Wybierz grę, która Cię interesuje', player_long['game'].unique())
        player_long = player_long[player_long['game'].isin(games)]

    year_filter = st.checkbox('Zaznacz jeśli chcesz zobaczyć spis gier (gry) dla danego sezonu')

    if year_filter:
        years = st.multiselect('Wybierz rok', seasons(df))
        player_long = player_long[player_long['date'].dt.year.isin(years)]

    if filtr and not games:
        st.info('Wybierz co najmniej jedną grę.')
        st.stop()
    if year_filter and not years:
        st.info('Wybierz co najmniej jeden rok.')
        st.stop()
    if player_long.empty:
        st.info('Brak partii dla wybranych filtrów.')
        st.stop()

    player_df = df.iloc[player_long['match_id']]
    """
    --------------------------------------------------
    """
    st.write('Spis wszystkich gier, w które zagrał dany gracz')
    st.write(format_dates(player_df).dropna(axis='columns', how='all'))
    kinds, total = player_long['game'].nunique(), len(player_long)
    st.write(f"{player} zagrał(a) w {kinds} {plural(kinds, 'rodzaj gry', 'rodzaje gier', 'rodzajów gier')}, "
             f"łącznie {total} {plural(total, 'raz', 'razy', 'razy')}.")
    st.write('Najczęściej grane gry:', game_counts(player_long))
    avg_players = f"{player_long['n_players'].mean():.1f}".replace('.', ',')
    st.write(f'Średnio w partii {avg_players} graczy.')
    st.dataframe(table_sizes(player_long).reset_index(), hide_index=True)
    st.write('Statystyki odnośnie zajmowanego miejsca')
    st.write(player_places(player_long, player))
    st.markdown('#### Najlepszy wynik w każdej grze')
    st.caption('miejsce: który to wynik wśród najlepszych wyników wszystkich graczy w tej grze'
               + (' (w wybranych latach)' if year_filter else ''))
    ranking_scope = long[long['date'].dt.year.isin(years)] if year_filter else long
    best = player_best_per_game(ranking_scope, player)
    st.dataframe(best[best['gra'].isin(player_long['game'])], hide_index=True,
                 column_config={'data': DATE_COLUMN, '% wygranych': st.column_config.NumberColumn(format='%.1f %%')})
    st.markdown('#### Najczęstsi współgracze')
    mates = co_players(long[long['match_id'].isin(player_long['match_id'])], player)
    rival = nemesis(mates)
    if rival:
        st.write(f"Nemezis (nominalnie): **{', '.join(rival[0])}** (wyprzedził(a) Cię {rival[1]} "
                 f"{plural(rival[1], 'raz', 'razy', 'razy')})")
    rival_rel = nemesis_relative(mates, NEMESIS_MIN_GAMES)
    if rival_rel:
        names, pct = rival_rel
        detail = ''
        if len(names) == 1:
            row = mates.set_index('gracz').loc[names[0]]
            detail = f": {int(row['niżej'])} z {int(row['wspólne partie'])}"
        pct_text = f'{pct:.1f}'.replace('.', ',')
        st.write(f"Nemezis (względnie): **{', '.join(names)}** (wyprzedził(a) Cię w {pct_text}% wspólnych partii"
                 f"{detail})")
    st.caption(f'Względnie: odsetek wspólnych partii, w których ta osoba była wyżej; '
               f'liczą się współgracze z co najmniej {NEMESIS_MIN_GAMES} wspólnymi partiami.')
    st.caption('wyżej / niżej / remis: w ilu wspólnych partiach byłeś wyżej, niżej lub na równi z tą osobą')
    st.dataframe(mates, hide_index=True,
                 column_config={'% wyprzedzeń': st.column_config.NumberColumn(format='%.1f %%')})
