import pandas as pd
import numpy as np
import streamlit as st
st.set_page_config(page_title='Boardstats', page_icon=':game_die:')

#do pobierania
@st.cache
def convert_df(df):    
    return df.to_csv().encode('utf-8')


#testowe wczytywanie excela
@st.cache_data(ttl=600)
def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url,on_bad_lines=False)

test = load_data(st.secrets["public_gsheets_url"])

# Print results.
for row in test.itertuples():
    st.write(f"{row.name} has a :{row.pet}:")

