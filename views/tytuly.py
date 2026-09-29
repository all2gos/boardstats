import streamlit as st
from data import load_raw, to_long
from titles import (ALL_TIME, GENERAL, MEDAL_ICONS, MIN_SEASON_GAMES, TITLES, medal_records, medal_tally,
                    past_seasons, season_champions, title_records)


@st.cache_data(ttl=600)
def all_medals():
    df = load_raw()
    years = past_seasons(df)
    return medal_records(df, to_long(df), years), years


records, years = all_medals()

st.caption('Tytuły zbierają medale z kategorii Hall of Fame. Kolejność olimpijska: najpierw liczba złotych '
           'medali, przy remisie srebrnych, potem brązowych. Kategorie sezonowe liczą zakończone sezony, '
           'kategorie wszech czasów wszystkie partie. W duo/trio/czwórce medal grupy dostaje każdy jej członek; '
           f'w sezonowym ELO liczą się gracze z co najmniej {MIN_SEASON_GAMES} partiami.')

for title in [*TITLES, GENERAL]:
    if title == GENERAL:
        st.markdown(f'### {GENERAL}')
        st.caption('Wszystkie medale ze wszystkich kategorii powyżej.')
    else:
        theme, categories = TITLES[title]
        st.markdown(f'### {title} — {theme}')
        st.caption('Kategorie: ' + ', '.join(categories) + '.')
    medals = title_records(records, title)
    st.dataframe(medal_tally(medals), hide_index=True)
    st.markdown('**Zdobywca tytułu w sezonie** (tylko kategorie sezonowe)')
    st.dataframe(season_champions(medals, years))
    with st.expander(f'Skąd te medale ({title})'):
        detail = medals.assign(medal=medals['medal'].map(MEDAL_ICONS), okres=medals['okres'].astype(str),
                               _kolejnosc=medals['okres'].replace({ALL_TIME: 9999}))  # wszech czasów na końcu
        detail = detail.sort_values(['gracz', '_kolejnosc', 'kategoria'])
        st.dataframe(detail[['gracz', 'medal', 'kategoria', 'okres']], hide_index=True)
