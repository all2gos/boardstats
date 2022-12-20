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

