import pandas as pd
import numpy as np
import streamlit as st

"""### Boardstats"""

df = pd.read_csv('board_df.csv')
st.write(df)
