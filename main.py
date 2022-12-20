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
    new_or_old_game = st.radio('No i rodzaj gry',('Istniejąca gra','Nowa gra'))

    if new_or_old_game == 'Istniejąca gra':
        game = st.multiselect('Kliknij, aby wybrać grę', list(df['game'].unique()))
    else:
        game = st.text_input('Kliknij, aby wpisać nową grę')

    df = pd.concat([df,[game,data]])
    st.write(df)
    number_of_players = st.number_input('Wprowadź liczbę graczy, którzy grali', min_value = 1, step=1)

    if number_of_players >0:
        new_or_old_player = st.radio('Wprowadź ID gracza (3 pierwsze litery imienia i nazwiska)',('Istniejący gracz','Nowy gracz'))

        if new_or_old_player == 'Istniejący gracz':
            player = st.multiselect('Kliknij, aby wybrać gracza',list(df.columns[1:]))
        
        else:
            player = st.text_input('Kliknij, aby wpisać gracza')
        
        score = st.number_input('Wprowadź wynik gracza (liczba zdobytych punktów lub wygranych partii, nie zajmowane miejsce')

        
