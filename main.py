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


#df = load_data(st.secrets["public_gsheets_url"])
df = load_data('https://docs.google.com/spreadsheets/d/1AbYEJT47wMhofqjcFlakU6KA-tsOlajh/edit#gid=1838830373')

"""### Boardstats"""

main_dict = dict()

main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Statystyki', 'Program do proponowania gier'))

if main_menu == 'Wyświetl całą tabelę':
    st.write(df.dropna(axis='columns', how='all'))

if main_menu == 'Statystyki':
    stats_menu = st.radio('Jakie statystyki chcesz wyświetlić?',('Ogólne','Staty dla danego gracza','ELO', 'Hall of Fame', 'WSJG'))
    if stats_menu == 'Ogólne':

        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')

        all_df = df.copy()

        league = st.radio('Wybierz, jeżeli chcesz zobaczyć ogólne informacje dla konkretnego roku',('Open','2023','2024','2025','2026'))

        if league != 'Open':
            df['year'] = df['date'].dt.to_period('Y')
            df = df[df['year'] == league]
            df = df.drop(['year'], axis=1)

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
            filtr = st.checkbox('Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa!!!)')
            if filtr:
                games = st.multiselect('Wybierz grę, która Cię interesuje',player_df['game'].unique()) 

                try:
                    player_df = player_df[player_df['game'].isin(games)]
                except ValueError:
                    st.write('Czekam aż wybierzesz grę')

            
            year_filter = st.checkbox('Zaznacz jeśli chcesz zobaczyć spis gier (gry) dla danego sezonu')

            if year_filter:
                years = st.multiselect('Wybierz rok', [2023, 2024, 2025, 2026])

                try:
                    player_df['date'] = pd.to_datetime(player_df['date'], format='%d.%m.%Y')

                    player_df['year'] = player_df['date'].dt.year
                    player_df = player_df[player_df['year'].isin(years)].drop('year',axis=1)
                except ValueError:
                    st.write('Czekam, aż wybierzesz rok')
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
            position_df = (pd.DataFrame(data = position_dict.items(),columns=['miejsce','tyle_razy_gracz_zajal_to_miejsce'])).sort_values(by='miejsce')
            st.write(position_df.set_index('miejsce'))

            
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

            league = st.radio('Wybierz, jeżeli chcesz zobaczyć ELO dla konkretnego roku',('Open','2023','2024','2025','2026'))

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

    if stats_menu == 'Hall of Fame':

        st.write('Każda kategoria to podsumowanie wszystkich sezonów (poza tym aktualnie trwającym)')

        st.write('### Liczba gier w sezonie')

        years = [2023, 2024, 2025, 2026]

        df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')
        
        medals = {'gold': [], 'silver': [], 'bronze': []}
        for year in years:
            year_df = df[df['date'].dt.year == year]
            st.write(f"W {year} roku rozegrano łącznie {len(year_df)} gier")

            player_cnt = dict()
            for player in df.columns[3:]:
                count = len(year_df[player].dropna())
                player_cnt[player] = count

            player_cnt_df = pd.DataFrame(data=player_cnt.items(), columns=['gracz', 'liczba_gier']).sort_values(by='liczba_gier', ascending=False)

            first_place = player_cnt_df.iloc[0]
            second_place = player_cnt_df.iloc[1]
            third_place = player_cnt_df.iloc[2]

            medals['gold'].append(first_place['gracz'])
            medals['silver'].append(second_place['gracz'])
            medals['bronze'].append(third_place['gracz'])   

        st.write('----------------------------------------------------------')
        st.write('Gracze z najwiekszą liczbą rozegranych gier w sezonie')
        st.write(pd.DataFrame(medals, index=years))

        st.write('### Najlepsze ELO w sezonie')

        medals = {'gold': [], 'silver': [], 'bronze': []}
        elo_table = dict()
        for p in df.columns[3:]:
            elo_table[p] = np.nan


        for year in years:
            elo_history = [copy.deepcopy(elo_table)]  # Używamy deepcopy do stworzenia głębokiej kopii

            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')

            all_df = df.copy()
            df['year'] = df['date'].dt.to_period('Y')
            year_df = df[df['year'] == str(year)].drop(columns='year')

            for i in range(len(year_df)):
                elo_table = elo(year_df.iloc[i], elo_table, all_df)
                elo_history.append(copy.deepcopy(elo_table))  # Znowu używamy deepcopy
                elo_df = pd.DataFrame(data=elo_history)


            actual_elo = pd.DataFrame(elo_df.iloc[-1].transpose()).rename(columns = {len(elo_df)-1:'max elo'}).sort_values(by='max elo', ascending=False)
            #st.write(actual_elo.dropna()[:3])

            actual_elo = actual_elo.reset_index(names='gracz')
            first_place = actual_elo.iloc[0]
            second_place = actual_elo.iloc[1]
            third_place = actual_elo.iloc[2]

            medals['gold'].append(first_place['gracz'])
            medals['silver'].append(second_place['gracz'])
            medals['bronze'].append(third_place['gracz'])  

        st.write(pd.DataFrame(medals, index=years))
        st.write('### Największa liczba RÓŻNYCH gier w sezonie')

        for year in years:
            medals = {'gold': [], 'silver': [], 'bronze': []}

            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y')

            all_df = df.copy()
            df['year'] = df['date'].dt.to_period('Y')
            year_df = df[df['year'] == str(year)]

            different_games_cnt = dict()

            for player in df.columns[3:-1]:
                different_games_cnt[player] = len(year_df[['game',player]].dropna()['game'].value_counts())

            different_games_cnt = pd.DataFrame(data=different_games_cnt.items(), columns=['gracz', 'liczba_różnych_gier']).sort_values(by='liczba_różnych_gier', ascending=False)

            first_place = different_games_cnt.iloc[0]
            second_place = different_games_cnt.iloc[1]
            third_place = different_games_cnt.iloc[2]

            medals['gold'].append(first_place['gracz'])
            medals['silver'].append(second_place['gracz'])
            medals['bronze'].append(third_place['gracz'])  

        st.write(pd.DataFrame(medals, index=years))

        st.write('### Unikalna gra kolekcja medalowa?')
        st.write('To póki co tylko koncept, ażeby liczyć najlepszy performance w każdym typie gry i brać taką najlepszą dla danego gracza rozgrywkę i w ten sposób przeprowadzać klasyfikację medalową')


if main_menu == 'Program do proponowania gier':
    st.write('To jest program, który proponuje gry na podstawie opcji, które zaznaczysz')
    st.write('Z oczywistych względów nie wprowadzam tutaj opcji wyboru nowych graczy i nowych gier, bo zakładam, że w takich sytuacjach będziecie wiedzieć w co chcecie grać')


    st.write('Wybierz graczy, których chcesz włączyć do propozycji gier')
    players = st.multiselect('Wybierz graczy', df.columns[3:].unique())

    st.write('Wybierz gry, które chcesz włączyć do propozycji gier')
    games = st.multiselect('Wybierz gry', df['game'].unique())