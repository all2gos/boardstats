import pandas as pd
import streamlit as st
from charts import network_elements, network_html
from data import load_raw, to_long
from stats import game_connections, player_connections

HALF_LIVES = {'1 mies.': 30.44, '3 mies.': 91.31, '6 mies.': 182.62, '1 rok': 365.25, '2 lata': 730.5,
              '3 lata': 1095.75, 'bez zaniku': None}

df = load_raw()
long = to_long(df)

st.markdown('#### Kto z kim grał')
label = st.select_slider('Jak szybko stare partie tracą wagę (okres półtrwania)', list(HALF_LIVES), value='6 mies.')
st.caption('Grubość połączenia to suma wspólnych partii, w której każda partia waży tym mniej, im dawniej się '
           'odbyła: partia sprzed jednego okresu półtrwania liczy się w połowie, sprzed dwóch w 1/4 itd. '
           'Wielkość kółka to liczba partii gracza. Wierzchołki można przeciągać.')

nodes, edges = network_elements(long, now=pd.Timestamp.now().normalize(), half_life_days=HALF_LIVES[label])
theme = 'dark' if getattr(st.context.theme, 'type', None) == 'dark' else 'light'
st.iframe(network_html(nodes, edges, theme=theme, height=600), height=610)

st.markdown('#### Liczba połączeń')
st.caption('Każda rozegrana partia z każdą inną osobą to jedno połączenie (bez zaniku w czasie).')
cols = st.columns(2)
cols[0].dataframe(player_connections(long), hide_index=True)
cols[1].dataframe(game_connections(long), hide_index=True)
