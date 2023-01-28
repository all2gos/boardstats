import pandas as pd
import numpy as np
import streamlit as st
st.set_page_config(page_title='Boardstats', page_icon=':game_die:')

#do pobierania
@st.cache
def convert_df(df):    
    return df.to_csv().encode('utf-8')

df = pd.read_csv('board_df.csv')
if 'Unnamed: 0' in df.columns:
    df = df.drop(['Unnamed: 0'],axis=1)

"""### Boardstats"""

main_dict = dict()

main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Wprowadź wyniki przeprowadzonej gry','Statystyki','Tryb deweloperski'))

if main_menu == 'Wyświetl całą tabelę':
    st.write(df)

if main_menu == 'Wprowadź wyniki przeprowadzonej gry':    
    data = st.date_input('Na początku podaj datę rozgrywki')    
    new_or_old_game = st.radio('No i rodzaj gry',('Istniejąca gra','Nowa gra'))

    if new_or_old_game == 'Istniejąca gra':
        game = st.multiselect('Kliknij, aby wybrać grę', list(df['game'].unique()))
    else:
        game = st.text_input('Kliknij, aby wpisać nową grę')
    numbers_of_players = st.text_input('Wprowadź liczbę graczy')
    players = list(st.multiselect('Wprowadź po kolei dane graczy', df.columns[2:]))
    var = list(st.text_input('Wprowadź po kolei wyniki graczy oddzielone przecinkami').split(','))
     
    scores = []
    for i in range(len(var)):
        try:
            scores.append(sum(list(map(lambda x: int(x),var[i].split('+')))))   
        except:
            continue 

    if st.button('Wprowadź dane'):
        if len(players) != len(scores):
            st.write('Ilość graczy i wyników jest różna, sprawdź czy zrobiłxś wszystko poprawnie')
        else:
            
                main_dict['date'] = data
                main_dict['game'] = game
                main_dict['liczba_graczy'] = numbers_of_players
                for i in range(len(players)):
                    main_dict[players[i]] = int(scores[i])
                    main_dict = pd.DataFrame(main_dict,index=[0])
                df_after = pd.concat([df,main_dict])
    
                open('board_df.csv','w').write(df_after.to_csv(index=False))
                st.write(df_after)

                #pobieranie
                csv = convert_df(df_after)
                st.download_button(
                label="Pobierz backup",
                data=csv,
                file_name='board_df.csv',
                mime='text/csv',)

if main_menu == 'Tryb deweloperski':
    password = st.text_input('Wprowadź hasło')
    st.write('Jeżeli nie znasz hasła znaczy, że nie jesteś adminem więc żeby coś zrobić w trybie deweloperskim musisz się z nim skontaktować')
    if password == 'dunderystyczny':
        develop_menu = st.radio('Co chcesz zrobić?', ('Usuń wybrany wiersz','Todolist','Coś innego'))
        if develop_menu == 'Usuń wybrany wiersz':
            id = st.text_input('Podaj id wiersza, który chcesz usunąć')

            if st.button('Usuń'):
                if id == '-1':
                    df_after = df.drop([-1])
                else:
                    df_after = df.drop([int(id)])

                open('board_df.csv','w').write(df_after.to_csv(index=False))
                st.write(df_after)

                #pobieranie
                csv = convert_df(df_after)
                st.download_button(
                label="Pobierz backup",
                data=csv,
                file_name='board_df.csv',
                mime='text/csv',)

        if develop_menu == 'Todolist':
            st.write('Opcja dodawania nowego gracza')
            st.write('Poprawienie filtrowania ze względu na grę')
            st.write('Dodanie opcji Statystyki dla danej gry')
            
    
if main_menu == 'Statystyki':
    stats_menu = st.radio('Jakie statystyki chcesz wyświetlić?',('Listę najczęściej granych gier','Listę najczęściej grających graczy','Staty dla danego gracza','Współczynnik skuteczności jako gracz'))
    if stats_menu == 'Listę najczęściej granych gier':
        st.write(df['game'].value_counts())
    if stats_menu == 'Listę najczęściej grających graczy':
        st.write(df.drop(['game','date','liczba_graczy'],axis=1).count().reset_index(name='count').sort_values(['count'],ascending=False))
    if stats_menu == 'Staty dla danego gracza':
        player = st.text_input('Wybierz gracza')  
        
        if player in df.columns:               
            player_df = df[df[player].notna()]            
            filtr = st.checkbox('Zaznacz jeśli chcesz zobaczyć statystyki dla wybranej gry (działa, bo działa jeszcze bym z tego nie korzystał)')
            if filtr:
                games = st.multiselect('Wybierz grę, która Cię interesuje',player_df['game'].unique()) 
                if games != 'Wybierz grę, która Cię interesuje':       
                    player_df = player_df[player_df['game'] ==  games[0]]
            """
            --------------------------------------------------
            """
            st.write('Spis wszystkich gier, w które zagrał dany gracz')
            st.write(player_df)
            st.write('Frekwencja: (nie działa filtrowanie growe)',int(len(player_df)/len(df)*100),'%')
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
            st.write('Współczynnik skuteczności jako gracz*',int(avg_place/your_place*100))
            if st.button('*Chcę wiedzieć jak to jest liczone'):
                st.write('Współczynnik skuteczności jako gracz to stosunek dwóch składowych')
                st.write('Średnio zajmowanego przez gracza miejsca')
                st.write('Miejsce jakie średnio POWINIEN zajmować dany gracz, gdyby w każdej grze był dokładnie w środku stawki (np. w grze 3 osobowej średnie miejsce to 2, a w grze 4 osobowej średnie miejsce to 2,5)')
                st.write('Finalny współczynnik to stosunek tej pierwszej wartości przez tą drugą pomnożony przez 100 i zaokrąglony do liczb całkowitych')
                """
                --------------------------------------------------------------------
                """
                st.write('Taka kolejność dzielenia wynika z chęci uzyskania proporcjonalności tego wskaźnika (im wyższy, tym lepszym jestem graczem)') 

                """
                ----------------------------------------------------------------------
                """
                st.write('Możnaby zadać pytanie jakie są wartości brzegowe tego parametru')
                st.write('Maksymalny współczynnik to (50+50*n), gdzie n to liczba graczy')
                st.write('Minimalny współczynnik jest znacznie bardziej skomplikowany dla 3,4,5 graczy wynosi kolejno 67,62,60')
    
    if stats_menu == 'Współczynnik skuteczności jako gracz':
        final_list = []
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
        st.write(final_list)
