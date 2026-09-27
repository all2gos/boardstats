import streamlit as st
from data import load_raw, seasons, player_columns, to_long
from stats import game_counts, in_year, player_game_counts

df = load_raw()
long = to_long(df)
players = player_columns(df)

league = st.radio('Wybierz, jeżeli chcesz zobaczyć ogólne informacje dla konkretnego roku',('Open',) + tuple(str(y) for y in seasons(df)))

league_long = long if league == 'Open' else in_year(long, int(league))

rows = st.columns(2)
rows[0].markdown("#### Najczęściej grane gry")
rows[0].dataframe(game_counts(league_long))
rows[1].markdown("#### Najczęściej grający gracze ")
rows[1].dataframe(player_game_counts(league_long, players).reset_index(drop=True))
