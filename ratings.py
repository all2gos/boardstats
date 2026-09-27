"""Ranking ELO: przebieg partii po kolei przez elo.elo."""
import numpy as np
import pandas as pd
import streamlit as st

from data import player_columns
from elo import elo


def _hash_df(df):
    # Streamlit 1.52 nie rozpoznaje DataFrame z pandas 3 (klasa zgłasza się jako pandas.DataFrame),
    # więc hash liczymy sami: wartości + indeks + nazwy kolumn.
    return pd.util.hash_pandas_object(df).to_numpy().tobytes() + repr(list(df.columns)).encode()


@st.cache_data(hash_funcs={pd.DataFrame: _hash_df})
def compute_elo(df, year=None):
    """ELO po każdej partii (Open albo tylko partie z danego roku, startując od zera).

    Liczniki partii w elo.elo liczone są po dacie na całym arkuszu `df` (świadoma decyzja,
    patrz TODO „Poza zakresem”), także gdy liczymy jeden rok.

    Zwraca (history, current):
    - history: wiersz 0 = stan początkowy (NaN), wiersz i = stan po i-tej partii; kolumny = gracze,
    - current: aktualne ELO (kolumna 'elo'), malejąco, tylko gracze, którzy już grali.
    """
    rows = df if year is None else df[df['date'].dt.year == year]
    table = {p: np.nan for p in player_columns(df)}
    history = [table.copy()]
    for i in range(len(rows)):
        table = elo(rows.iloc[i], table, df)
        history.append(table.copy())
    history = pd.DataFrame(data=history)
    current = pd.DataFrame(history.iloc[-1]).rename(columns={len(history) - 1: 'elo'})
    current = current.sort_values(by='elo', ascending=False).dropna()
    return history, current


def elo_chart_data(history, df, year=None):
    """Historia ELO w formacie długim do wykresu: gracz, elo, numer_partii, data, gra.

    numer_partii liczony w obrębie wybranego zakresu (Open albo rok), od 1; wiersz 0 historii
    (stan początkowy) jest pomijany, a gracz pojawia się od swojej pierwszej partii.
    """
    rows = df if year is None else df[df['date'].dt.year == year]
    meta = pd.DataFrame({'numer_partii': range(1, len(rows) + 1), 'data': rows['date'].to_numpy(),
                         'gra': rows['game'].to_numpy()})
    steps = history.iloc[1:].reset_index(drop=True)
    steps['numer_partii'] = range(1, len(steps) + 1)
    long = steps.melt(id_vars='numer_partii', var_name='gracz', value_name='elo').dropna(subset=['elo'])
    return long.merge(meta, on='numer_partii')[['gracz', 'elo', 'numer_partii', 'data', 'gra']]


def max_elo_table(history, df, year=None):
    """Maksymalne ELO każdego gracza (kolumna max_elo, malejąco) i data partii, po której je osiągnął
    (pierwszy raz, jeśli to samo maksimum powtórzyło się później)."""
    table = pd.DataFrame(history.max()).rename(columns={0: 'max_elo'}).sort_values(by='max_elo', ascending=False)
    table = table.dropna()
    steps = elo_chart_data(history, df, year)
    first = steps.sort_values(['elo', 'numer_partii'], ascending=[False, True]).drop_duplicates('gracz')
    table['data'] = first.set_index('gracz')['data'].reindex(table.index)
    return table
