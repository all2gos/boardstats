import pandas as pd
import numpy as np
import streamlit as st
import copy
import matplotlib.pyplot as plt
import datetime as dt
from elo import elo
st.set_page_config(page_title='Boardstats', page_icon=':game_die:')

#do pobierania
@st.cache_data
def convert_df(df):    
    return df.to_csv().encode('utf-8')


#testowe wczytywanie excela
@st.cache_data(ttl=600)
def load_data(sheets_url):
    csv_url = sheets_url.replace("/edit#gid=", "/export?format=csv&gid=")
    return pd.read_csv(csv_url, on_bad_lines='skip', index_col=0)
df = load_data(st.secrets["public_gsheets_url"])


"""### Boardstats"""

main_dict = dict()

main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Statystyki', 'Program do proponowania gier'))

if main_menu == 'Wyświetl całą tabelę':
    st.write(df.dropna(axis='columns', how='all'))

if main_menu == 'Statystyki':
    stats_menu = st.radio('Jakie statystyki chcesz wyświetlić?',('Ogólne','Staty dla danego gracza','ELO','WSJG', 'Hall of Fame'))
    if stats_menu == 'Ogólne':
        rows = st.columns(2)
        rows[0].markdown("#### Najczęściej grane gry")
        rows[0].dataframe(df['game'].value_counts())
        rows[1].markdown("#### Najczęściej grający gracze ")
        df_modified = df.drop(['game', 'date', 'liczba_graczy'], axis=1).count().reset_index(name='count').sort_values(['count'], ascending=False)
        rows[1].dataframe(df_modified.reset_index(drop=True))
    if stats_menu == 'Staty dla danego gracza':
        player = st.text_input('Wybierz gracza')  
        
        if player in df.columns:               
            player_df = df[df[player].notna()]            
            filtr = st.checkbox('Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa, bo działa jeszcze bym z tego nie korzystał)')
            if filtr:
                games = st.multiselect('Wybierz grę, która Cię interesuje',player_df['game'].unique()) 
                if games in player_df['game'].unique():       
                    player_df = player_df[player_df['game'] ==  games[0]]
            """
            --------------------------------------------------
            """
            st.write('Spis wszystkich gier, w które zagrał dany gracz')
            st.write(player_df.dropna(axis='columns', how='all'))
            st.write('Najczęściej grane gry:', player_df['game'].value_counts())
            st.write('Statystyki odnośnie zajmowanego miejsca')
            position_dict = dict()
            for i in range(len(player_df)):
                row = player_df.iloc[i].dropna()            
                position_list = []
                for j in range(3,len(row.unique())):
                    position_list.append(row[j])
                position_list = sorted(position_list,reverse=True)

                for char in range(len(position_list)):                
                    if int(position_list[char]) == int(row[player]):
                        place = char+1
                        break
                if place in position_dict:
                    position_dict[place] += 1
                else:
                    position_dict[place] = 1    
            position_df = (pd.DataFrame(data = position_dict.items(),columns=['miejsce','tyle_razy_gracz_zajal_to_miejsce']))
            st.write(position_df)

            
            avg_place = player_df['liczba_graczy'].mean()/2
            
            your_place = 0
            for i in range(len(position_df)):
                your_place += position_df['miejsce'].iloc[i]*position_df['tyle_razy_gracz_zajal_to_miejsce'].iloc[i]
            your_place /= len(player_df)
            """
            ----------------------------------------------------
            """
            st.write(f"Współczynnik skuteczności jako gracz*{int(avg_place/your_place*100):.2f}")
            if st.button('*Chcę wiedzieć jak to jest liczone'):
                st.write('Współczynnik skuteczności jako gracz to stosunek dwóch składowych:')
                st.write('- średnio zajmowanego przez gracza miejsca')
                st.write('- miejsca jakie średnio POWINIEN zajmować dany gracz, gdyby w każdej grze był dokładnie w środku stawki (np. w grze 3 osobowej średnie miejsce to 2, a w grze 4 osobowej średnie miejsce to 2,5)')
                st.write('Finalny współczynnik to stosunek tej pierwszej wartości przez tą drugą pomnożony przez 100 i zaokrąglony do liczb całkowitych')
                """
                --------------------------------------------------------------------
                """
                st.write('Taka kolejność dzielenia wynika z chęci uzyskania proporcjonalności tego wskaźnika (im wyższy, tym lepszym jestem graczem)') 

                """
                ----------------------------------------------------------------------
                """
                st.write('Oznacza to, że współczynnik ten wynosi 100, gdy gracz gra DOKŁADNIE średnio')
                st.write('Przekracza 100 jeżeli gracz gra lepiej niż średnio')
                st.write('I wynosi poniżej 100, jeżeli gra gorzej niż średnio')
                st.write('Aktualnie (26.06.23) tylko dwie osoby w ogólnej klasyfikacji mają wskaźnik powyżej 100, czy to jest możliwe?')
    
    if stats_menu == 'WSJG':
        st.write('WSJG czyli współczynnik skuteczności jako gracz to pierwszy wskaźnik, który implementowaliśmy na potrzeby boardstatsa. Posiada jednak pewne ograniczenia, ze względu na które, postanowiliśmy zaimplementować system ELO. Obecnie traktujemy WSJG jako relikt przeszłości, ale po co go wyrzucać jak nikomu nie przeszkadza cnie')
        final_list = []
        game_filter = st.selectbox('Zawęź do jednej gry', ['wszystkie gry'] + list(df['game'].unique()))
        if game_filter is not 'wszystkie gry':
            df = df[df['game']==game_filter]
        for player in df.columns[3:]:
            player_df = df[df[player].notna()] 
            if len(player_df) == 0:
                continue
            else:
                position_dict = dict()
                for i in range(len(player_df)):
                    row = player_df.iloc[i].dropna()            
                    position_list = []
                    for j in range(3,len(row.unique())):
                        position_list.append(row[j])
                    position_list = sorted(position_list,reverse=True)

                    for char in range(len(position_list)):                
                        if int(position_list[char]) == int(row[player]):
                            place = char+1
                            break
                    if place in position_dict:
                        position_dict[place] += 1
                    else:
                        position_dict[place] = 1    
                position_df = (pd.DataFrame(data = position_dict.items(),columns=['miejsce','tyle_razy_gracz_zajal_to_miejsce']))
                
                avg_place = player_df['liczba_graczy'].mean()/2
                
                your_place = 0
                for i in range(len(position_df)):
                    your_place += position_df['miejsce'].iloc[i]*position_df['tyle_razy_gracz_zajal_to_miejsce'].iloc[i]
                your_place /= len(player_df)
                final_list.append([player,int(avg_place/your_place*100)])

        final_list.sort(key=lambda row: (row[1],row[0]),reverse=True)
        st.write(pd.DataFrame(data = final_list, columns=['gracz','pkt_skutecznosci']))


    if stats_menu == 'ELO':
        elo_button = st.radio('',('ELO Główna Tabela','Jak to działa?'))

        if elo_button == 'Jak to działa?':
            with open('elo_explanation.txt', 'r') as file:
                elo_explanation = file.read()
            st.markdown(elo_explanation)
        if elo_button == 'ELO Główna Tabela':
            elo_table = dict()
            for p in df.columns[3:]:
                elo_table[p] = np.nan

            elo_history = [copy.deepcopy(elo_table)]  # Używamy deepcopy do stworzenia głębokiej kopii


            league = st.radio('Wybierz, jeżeli chcesz zobaczyć ELO dla konkretnego roku',('Open','2023','2024','2025'))

            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')

            all_df = df.copy()
            if league != 'Open':
                df['year'] = df['date'].dt.to_period('Y')
                df = df[df['year'] == league]
                df = df.drop(['year'], axis=1)

            st.write(df)

            for i in range(len(df)):
                elo_table = elo(df.iloc[i], elo_table, all_df)
                elo_history.append(copy.deepcopy(elo_table))  # Znowu używamy deepcopy
                elo_df = pd.DataFrame(data=elo_history)

            elo_stat_button = st.radio('Dodatkowe statystyki',('Aktualne ELO','Maksymalne ELO w historii'))

            if elo_stat_button == 'Aktualne ELO':
                actual_elo = pd.DataFrame(elo_df.iloc[-1].transpose()).rename(columns = {len(elo_df)-1:'max elo'}).sort_values(by='max elo', ascending=False)
                st.write(actual_elo.dropna())

                
            if elo_stat_button == 'Maksymalne ELO w historii':
                max_elo = pd.DataFrame(elo_df.max()).rename(columns={0:'max_elo'}).sort_values(by='max_elo',ascending=False)
                st.write(max_elo[max_elo['max_elo']>1000])
            

            players = st.multiselect('Zaznacz, jakich graczy ELO chcesz śledzić na wykresie', elo_df.columns)

            if players != []: 
                fig, ax = plt.subplots()
                ax = elo_df[players].plot(ax=ax, legend=False)
                ax.set_ylim(elo_df[players].min().min()-10,elo_df[players].max().max()+10)
                ax.set_xlabel('Numer rozgrywki')
                ax.set_ylabel('ELO')
                st.pyplot(fig) 
            else: 
                st.write('Aby pojawił się wykres musisz wybrać conajmniej jednego gracza')
            st.write('Historia zmian ELO')
            st.write(elo_df)

if main_menu == 'Hall of Fame':

    st.write('Każda kategoria to podsumowanie wszystkich sezonów (poza tym aktualnie trwającym)')

    st.write('### Najwięcej rozegranych gier')

    years = [2023, 2024]

    df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')
    
    for year in years:
        year_df = df[df['date'].dt.year == year]
        print(year_df.value_counts()[:3])

if main_menu == 'Program do proponowania gier':
    st.write('To jest program, który proponuje gry na podstawie opcji, które zaznaczysz')
    st.write('Z oczywistych względów nie wprowadzam tutaj opcji wyboru nowych graczy i nowych gier, bo zakładam, że w takich sytuacjach będziecie wiedzieć w co chcecie grać')


    st.write('Wybierz graczy, których chcesz włączyć do propozycji gier')
    players = st.multiselect('Wybierz graczy', df.columns[3:].unique())

    st.write('Wybierz gry, które chcesz włączyć do propozycji gier')
    games = st.multiselect('Wybierz gry', df['game'].unique())