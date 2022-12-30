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
    develop_menu = st.radio('Co chcesz zrobić?', ('Usuń wybrany wiersz','Todolist','Coś innego'))
    if develop_menu == 'Usuń wybrany wiersz':
        id = st.text_input('Podaj id wiersza, który chcesz usunąć')

        if st.button('Usuń'):
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
        st.write('Tworzenie statystyk')
    
if main_menu == 'Statystyki':
    stats_menu = st.radio('Jakie statystyki chcesz wyświetlić?',('Listę najczęściej granych gier','Listę najczęściej grających graczy','Staty dla danego gracza'))
    if stats_menu == 'Listę najczęściej granych gier':
        st.write(df['game'].value_counts())
    if stats_menu == 'Listę najczęściej grających graczy':
        st.write(df.drop(['game','date'],axis=1).count())


        
