import pandas as pd
import numpy as np
import streamlit as st



# backend

df = pd.read_csv('board_df.csv')







#frontend
"""### Boardstats"""




main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Wprowadź wyniki przeprowadzonej gry'))

if main_menu == 'Wyświetl całą tabelę':
    st.write(df)


if main_menu == 'Wprowadź wyniki przeprowadzonej gry':    
    data = st.date_input('Na początku podaj datę rozgrywki')
    number_of_players = st.number_input('Wprowadź liczbę graczy, którzy grali')

    for i in range(int(number_of_players)):
        new_or_old_player = st.radio('Wprowadź ID gracza (3 pierwsze litery imienia i nazwiska)',('Istniejący gracz','Nowy gracz'))

        if new_or_old_player == 'Istniejący gracz':
            player = st.multiselect('Kliknij, aby wybrać gracza',df.columns)
