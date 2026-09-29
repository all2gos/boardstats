import streamlit as st

st.set_page_config(page_title='Boardstats', page_icon=':game_die:')

nav = st.navigation({
    '': [
        st.Page('views/tabela.py', title='Cała tabela', url_path='tabela', default=True),
        st.Page('views/program.py', title='Program do proponowania gier', url_path='program'),
    ],
    'Statystyki': [
        st.Page('views/ogolne.py', title='Ogólne', url_path='ogolne'),
        st.Page('views/gracz.py', title='Staty dla danego gracza', url_path='gracz'),
        st.Page('views/gra.py', title='Statystyki gry', url_path='gra'),
        st.Page('views/siec.py', title='Sieć graczy', url_path='siec'),
        st.Page('views/ranking_elo.py', title='ELO', url_path='elo'),
        st.Page('views/hall_of_fame.py', title='Hall of Fame', url_path='hall-of-fame'),
        st.Page('views/tytuly.py', title='Tytuły i odznaczenia', url_path='tytuly'),
        st.Page('views/wsjg.py', title='WSJG', url_path='wsjg'),
    ],
}, position='top')

"""### Boardstats"""

nav.run()
