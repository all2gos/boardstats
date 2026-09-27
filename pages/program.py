import streamlit as st
from data import load_raw

df = load_raw()

st.write('To jest program, który proponuje gry na podstawie opcji, które zaznaczysz')
st.write('Z oczywistych względów nie wprowadzam tutaj opcji wyboru nowych graczy i nowych gier, bo zakładam, że w takich sytuacjach będziecie wiedzieć w co chcecie grać')


st.write('Wybierz graczy, których chcesz włączyć do propozycji gier')
players = st.multiselect('Wybierz graczy', df.columns[3:].unique())

st.write('Wybierz gry, które chcesz włączyć do propozycji gier')
games = st.multiselect('Wybierz gry', df['game'].unique())
