"""Wczytywanie arkusza z wynikami i przekształcenie go do formatu długiego."""
import pandas as pd
import streamlit as st

SHEET_URL = 'https://docs.google.com/spreadsheets/d/1AbYEJT47wMhofqjcFlakU6KA-tsOlajh/edit#gid=1838830373'
DATE_FORMAT = '%d.%m.%Y'
META_COLUMNS = ['game', 'date', 'liczba_graczy']
FIRST_SEASON = 2023  # 2022 (kilka partii świątecznych) nie jest osobnym sezonem


def parse_sheet(df):
    """Arkusz w formacie szerokim z datą sparsowaną do datetime."""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], format=DATE_FORMAT)
    return df


@st.cache_data(ttl=600)
def load_raw(sheets_url=SHEET_URL):
    """Arkusz w formacie szerokim: kolumny game, date, liczba_graczy, potem jedna kolumna na gracza."""
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return parse_sheet(pd.read_csv(csv_url, on_bad_lines='skip', index_col=0))


def player_columns(df):
    return list(df.columns[len(META_COLUMNS):])


def seasons(df):
    """Lata (sezony) występujące w danych, od FIRST_SEASON."""
    return sorted(int(y) for y in df['date'].dt.year.unique() if y >= FIRST_SEASON)


def format_dates(df):
    """Kopia do wyświetlenia: data jako tekst dd.mm.rrrr."""
    df = df.copy()
    df['date'] = df['date'].dt.strftime(DATE_FORMAT)
    return df


def to_long(df):
    """Jeden wiersz na (partia, gracz).

    match_id to pozycja wiersza w arkuszu (chronologia; indeks arkusza bywa zduplikowany),
    place: 1 = najwyższy wynik, remis = ta sama pozycja (1-1-3), won: place == 1.
    """
    wide = df.reset_index(drop=True)
    wide['match_id'] = range(len(wide))
    long = wide.melt(id_vars=['match_id', 'date', 'game', 'liczba_graczy'], value_vars=player_columns(df),
                     var_name='player', value_name='score').dropna(subset=['score'])
    long = long.sort_values('match_id', kind='stable').rename(columns={'liczba_graczy': 'n_players'})
    long['place'] = long.groupby('match_id')['score'].rank(method='min', ascending=False).astype(int)
    long['won'] = long['place'] == 1
    return long[['match_id', 'date', 'game', 'n_players', 'player', 'score', 'place', 'won']].reset_index(drop=True)


def plural(n, one, few, many):
    """Polska odmiana liczebnika: plural(1, 'gra', 'gry', 'gier') -> 'gra', 3 -> 'gry', 5 -> 'gier'."""
    if n == 1:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def fmt_num(x, decimals=1):
    """Liczba do wyświetlenia po polsku: przecinek dziesiętny, np. 66.5 -> '66,5'."""
    return f'{x:.{decimals}f}'.replace('.', ',')
