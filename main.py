import pandas as pd
import numpy as np
import streamlit as st



# backend

df = pd.read_csv('board_df.csv')



#frontend
"""### Boardstats"""

main_dict = dict()


main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Wprowadź wyniki przeprowadzonej gry'))
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
    scores = list(st.text_input('Wprowadź po kolei wyniki graczy oddzielone przecinkami').split(','))
    if st.button('Wprowadź dane'):
        if len(players) != len(scores):
            st.write('Ilość graczy i wyników jest różna, sprawdź czy zrobiłxś wszystko poprawnie')
        else:
            
                main_dict['date'] = data
                main_dict['game'] = game
                for i in range(len(players)):
                    main_dict[players[i]] = scores[i]
                    main_dict = pd.DataFrame(main_dict,index=[0])
                df_after = pd.concat([df,main_dict])
    
                open('board_df.csv','w').write(df_after.to_csv(index=False))
                st.write(df_after)
    




        
