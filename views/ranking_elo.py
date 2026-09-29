import streamlit as st
from charts import elo_chart
from data import load_raw, player_columns, seasons
from ratings import compute_elo, elo_chart_data, max_elo_table

df = load_raw()

elo_button = st.radio('Widok ELO',('ELO Główna Tabela','Jak to działa?'), label_visibility='collapsed')

if elo_button == 'Jak to działa?':
    with open('elo_explanation.txt', 'r') as file:
        elo_explanation = file.read()
    st.markdown(elo_explanation)
if elo_button == 'ELO Główna Tabela':
    league = st.radio('Wybierz, jeżeli chcesz zobaczyć ELO dla konkretnego roku',('Open',) + tuple(str(y) for y in seasons(df)))
    year = None if league == 'Open' else int(league)

    elo_df, current_elo = compute_elo(df, year)

    elo_stat_button = st.radio('Dodatkowe statystyki',('Aktualne ELO','Maksymalne ELO w historii'))

    if elo_stat_button == 'Aktualne ELO':
        st.write(current_elo)

    if elo_stat_button == 'Maksymalne ELO w historii':
        st.dataframe(max_elo_table(elo_df, df, year),
                     column_config={'data': st.column_config.DateColumn('osiągnięte', format='DD.MM.YYYY')})
    
    chart_players = st.multiselect('Zaznacz, jakich graczy ELO chcesz śledzić na wykresie', list(current_elo.index),
                                   default=list(current_elo.index[:5]))
    x_axis = st.radio('Oś X', ('Numer partii', 'Data'), horizontal=True)

    if chart_players != []:
        theme = 'dark' if getattr(st.context.theme, 'type', None) == 'dark' else 'light'
        chart = elo_chart(elo_chart_data(elo_df, df, year), chart_players, player_columns(df),
                          x='numer_partii' if x_axis == 'Numer partii' else 'data', theme=theme)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.write('Aby pojawił się wykres musisz wybrać conajmniej jednego gracza')
    with st.expander('Historia zmian ELO'):
        st.write(elo_df)
