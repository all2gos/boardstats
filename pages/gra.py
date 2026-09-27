import streamlit as st
from data import DATE_FORMAT, fmt_num, load_raw, to_long
from stats import (MATURE_GAME_MATCHES, best_debut, game_best_per_player, game_counts, game_player_table,
                   game_summary, highest_losing_score, is_mature, lowest_winning_score, score_summary,
                   scores_by_table_size, top_scores, wsjg)

DATE_COLUMN = st.column_config.DateColumn('data', format='DD.MM.YYYY')

df = load_raw()
long = to_long(df)

counts = game_counts(long)
game = st.selectbox('Wybierz grę', counts.index, format_func=lambda g: f"{g} ({counts[g]} partii)")

summary = game_summary(long, game)
cols = st.columns(3)
cols[0].metric('Rozegrane partie', summary['partie'])
cols[1].metric('Pierwsza partia', summary['pierwsza'].strftime(DATE_FORMAT))
cols[2].metric('Ostatnia partia', summary['ostatnia'].strftime(DATE_FORMAT))

mature = is_mature(summary['partie'])
if mature:
    with st.expander(f'Więcej statystyk — gra dojrzała (ponad {MATURE_GAME_MATCHES} partii)'):
        st.info(f"Ta gra ma ponad {MATURE_GAME_MATCHES} partii, więc uznajemy ją za dojrzałą i prezentujemy więcej "
                "statystyk.")
        st.markdown('#### Typowy wynik')
        typical = score_summary(long, game)
        cols = st.columns(3)
        cols[0].metric('Średnia', fmt_num(typical['średnia']))
        cols[1].metric('Mediana', fmt_num(typical['mediana']))
        cols[2].metric('Średni wynik zwycięzcy', fmt_num(typical['średni wynik zwycięzcy']))
        st.caption(f"Połowa wyników mieści się w przedziale {fmt_num(typical['Q1'])}–{fmt_num(typical['Q3'])} "
                   "(IQR, Q1–Q3).")

        st.markdown('#### Wynik a liczba graczy')
        st.dataframe(scores_by_table_size(long, game), hide_index=True,
                     column_config={c: st.column_config.NumberColumn(format='%.1f')
                                    for c in ('średni wynik', 'średni wynik zwycięzcy')})

        st.markdown('#### Najlepszy debiut')
        st.caption('Najwyższy wynik osiągnięty w pierwszej partii gracza w tę grę.')
        st.dataframe(best_debut(long, game), hide_index=True, column_config={'data': DATE_COLUMN})
else:
    st.caption(f"Więcej statystyk pokażemy, gdy gra przekroczy {MATURE_GAME_MATCHES} partii "
               f"(teraz: {summary['partie']}).")

st.markdown('#### Gracze')
st.dataframe(game_player_table(long, game), hide_index=True,
             column_config={'% wygranych': st.column_config.NumberColumn(format='%.1f %%')})

st.markdown('#### Top 5 wyników wszech czasów')
st.dataframe(top_scores(long, game), hide_index=True, column_config={'data': DATE_COLUMN})

st.markdown('#### Najlepszy wynik każdego gracza')
st.dataframe(game_best_per_player(long, game), hide_index=True, column_config={'data': DATE_COLUMN})

st.markdown('#### Najniższy wynik, który wygrał')
st.dataframe(lowest_winning_score(long, game), hide_index=True, column_config={'data': DATE_COLUMN})

st.markdown('#### Najwyższy wynik, który nie wygrał')
st.dataframe(highest_losing_score(long, game), hide_index=True, column_config={'data': DATE_COLUMN})

st.markdown('#### Ranking WSJG w tej grze')
st.dataframe(wsjg(long, game), hide_index=True)
