import streamlit as st
from data import load_raw, to_long
from stats import wsjg

df = load_raw()
long = to_long(df)

st.write('WSJG czyli współczynnik skuteczności jako gracz to pierwszy wskaźnik, który implementowaliśmy na potrzeby boardstatsa. Posiada jednak pewne ograniczenia, ze względu na które, postanowiliśmy zaimplementować system ELO. Obecnie traktujemy WSJG jako relikt przeszłości, ale po co go wyrzucać jak nikomu nie przeszkadza cnie')
with st.expander('Jak to jest liczone?'):
    st.write('Współczynnik skuteczności jako gracz to stosunek dwóch składowych:')
    st.write('- miejsca jakie średnio POWINIEN zajmować dany gracz, gdyby w każdej grze był dokładnie w środku stawki (np. w grze 3 osobowej średnie miejsce to 2, a w grze 4 osobowej średnie miejsce to 2,5)')
    st.write('- średnio zajmowanego przez gracza miejsca')
    st.write('Finalny współczynnik to stosunek tej pierwszej wartości przez tą drugą pomnożony przez 100 i zaokrąglony do liczb całkowitych')
    st.write('Taka kolejność dzielenia wynika z chęci uzyskania proporcjonalności tego wskaźnika (im wyższy, tym lepszym jestem graczem)')
    st.write('Oznacza to, że współczynnik ten wynosi 100, gdy gracz gra DOKŁADNIE średnio')
    st.write('Przekracza 100 jeżeli gracz gra lepiej niż średnio')
    st.write('I wynosi poniżej 100, jeżeli gra gorzej niż średnio')

game_filter = st.selectbox('Zawęź do jednej gry', ['wszystkie gry'] + list(df['game'].unique()))
st.write(wsjg(long, None if game_filter == 'wszystkie gry' else game_filter))
