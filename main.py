import pandas as pd
import numpy as np
import streamlit as st
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

main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Statystyki'))

if main_menu == 'Wyświetl całą tabelę':
    st.write(df.dropna(axis='columns', how='all'))
    #pobieranie
    csv = convert_df(df)
    st.download_button(
    label="Pobierz backup",
    data=csv,
    file_name='board_df.csv',
    mime='text/csv',)

    
if main_menu == 'Statystyki':
    stats_menu = st.radio('Jakie statystyki chcesz wyświetlić?',('Staty dla danego gracza','Współczynniki skuteczności'))
    rows = st.columns(2)
    rows[0].markdown("#### Najczęściej grane gry")
    rows[0].dataframe(df['game'].value_counts())
    rows[1].markdown("#### Najczęściej grający gracze ")
    df_modified = df.drop(['game', 'date', 'liczba_graczy'], axis=1).count().reset_index(name='count').sort_values(['count'], ascending=False)
    rows[1].dataframe(df_modified.reset_index(drop=True, inplace=True))
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
                st.write('Weźmy np brassa: pkt skuteczności i ilość zagranych klej kolejno dla janka,mnie,mileny,gosii,kasi, zosi, matiego i taty janka to:')
                st.write('129:11,100:6,88:4,85:4,78:11,64:10,60:4,58:7')
    
    if stats_menu == 'Współczynniki skuteczności':
        final_list = []
        game_filter = st.text_input('Zawęź do jednej gry')
        st.write('Dostępne gry:',df['game'].unique())
        if game_filter:
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
                st.write(avg_place,your_place)
                final_list.append([player,int(avg_place/your_place*100)])

        final_list.sort(key=lambda row: (row[1],row[0]),reverse=True)
        st.write(pd.DataFrame(data = final_list, columns=['gracz','pkt_skutecznosci']))


  