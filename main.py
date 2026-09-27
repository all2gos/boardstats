import streamlit as st

st.set_page_config(page_title='Boardstats', page_icon=':game_die:')

nav = st.navigation({
    '': [
        st.Page('pages/tabela.py', title='Cała tabela', url_path='tabela', default=True),
        st.Page('pages/program.py', title='Program do proponowania gier', url_path='program'),
    ],
    'Statystyki': [
        st.Page('pages/ogolne.py', title='Ogólne', url_path='ogolne'),
        st.Page('pages/gracz.py', title='Staty dla danego gracza', url_path='gracz'),
        st.Page('pages/gra.py', title='Statystyki gry', url_path='gra'),
        st.Page('pages/ranking_elo.py', title='ELO', url_path='elo'),
        st.Page('pages/hall_of_fame.py', title='Hall of Fame', url_path='hall-of-fame'),
        st.Page('pages/wsjg.py', title='WSJG', url_path='wsjg'),
    ],
}, position='top')

"""### Boardstats"""

nav.run()
