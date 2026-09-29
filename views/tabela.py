import streamlit as st
from data import load_raw, format_dates

df = load_raw()

st.write(format_dates(df.iloc[::-1]).dropna(axis='columns', how='all'))
