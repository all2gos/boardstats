import pandas as pd
import numpy as np
import streamlit as st
import copy
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

def elo(row, elo_table):

  #czynniki do dowolnej modyfikacji:
  alfa = 400
  k = 64
  l = dict(row.dropna())

  players = list(l)[3:]
  elo_change_list = {}
  max_positive_change = 0
  max_negative_change = 0
  for p in players:
    #liczenie aktualnego wyniku
    actual_score = 0
    expected_score = 0
    for oponent in players:

      if oponent != p:
        if np.isnan(elo_table[oponent]):
          elo_table[oponent] = 1000

          print(oponent, 'zyskał ranking 1000')
        elif np.isnan(elo_table[p]):
          elo_table[p] = 1000
          print(p, 'zyskał ranking 1000')

        if l[p] > l[oponent]:
          actual_score+=1
        elif l[p] == l[oponent]:
          actual_score +=0.5
        #liczenie oczekiwanego wyniku
        expected_score += 1/(1+10**((elo_table[oponent]-elo_table[p])/alfa))

        #oczekiwana zmiana elo

      elo_change_list[p] = k*(actual_score-expected_score)

      #print(f"Aktualny wynik {p} to {actual_score}, podczas gdy oczekiwany wynik to {round(expected_score,2)}, zmiana elo wynosi {round(elo_change_list[p],2)}")
  #aktualizacja elo: w nowej pętli, żeby wszystko odbywało się po wyliczeniu oczekiwanych wyników
  for p in players:

    #zliczanie, ktora to jest gra danego gracza overall
    game_played = len(df[p][df['date'] <= l['date']].dropna())
    #print(f"gracz {p} do dnia {l['date']} rozegrał {game_played} gier")

    #zliczanie, ktora to jest rozgrywka TEJ KONKRETNEJ gry TEGO KONKRETNEGO GRACZA
    that_game_played = len(df[p][(df['date'] <= l['date']) & (df['game'] == l['game'])].dropna())
    #czynnik amortyzujacy dla swiezych graczy:

    change_reduction = 0.2 if that_game_played == 1 else (0.5 if that_game_played == 2 else (0.8 if that_game_played == 3 else 1))
    #print(f"gracz {p} do dnia {l['date']} rozegrał {that_game_played} rozgrywek gry {l['game']}, ale w sumie rozgeral {game_played} gier, w zwiazku z czym redukcja zmiany wynosi {change_reduction}")
    #elo_table[p] += round(elo_change_list[p],2)
    elo_table[p] += round(max(np.log(1/game_played)+4,1)*elo_change_list[p]*change_reduction/(l['liczba_graczy']-1),1)
  return elo_table

"""### Boardstats"""

main_dict = dict()

main_menu = st.radio('Co chcesz zrobić?', ('Wyświetl całą tabelę','Statystyki'))

if main_menu == 'Wyświetl całą tabelę':
    st.write(df.dropna(axis='columns', how='all'))

if main_menu == 'Statystyki':
    stats_menu = st.radio('Jakie statystyki chcesz wyświetlić?',('Ogólne','Staty dla danego gracza','ELO','WSJG'))
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
                st.write('Weźmy np brassa: pkt skuteczności i ilość zagranych klej kolejno dla janka,mnie,mileny,gosii,kasi, zosi, matiego i taty janka to:')
                st.write('129:11,100:6,88:4,85:4,78:11,64:10,60:4,58:7')
    
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
        elo_button = st.radio('',('Jak to działa?','ELO Główna Tabela'))

        if elo_button == 'Jak to działa?':
            st.markdown("""
### Podstawowe zasady:
1. ELO startowe to 1000 pkt.
2. Każda rozgrywka na potrzeby ELO jest liczona jako pojedyncze pojedynki 1 vs 1 we wszystkich kombinacjach. Na przykład, gdy grają trzej gracze (A, B, C), skrypt sprawdza wyniki indywidualnych meczy A-B, B-C i A-C i traktuje je jako odbyte jednocześnie.
3. Ranking ELO nie uwzględnia tego, jak silna jest wygrana (podobnie jak w szachach, gdzie "siła" wygranej jest subiektywna, a tutaj mamy ją wyrażoną w punktach zwycięstwa).

### Wzory liczenia ELO:

Przykład:

Gracz A ma ranking 1613 i:
- przegrał z graczem 1603
- zremisował z graczem 1477
- wygrał z graczem 1388
- wygrał z graczem 1586
- przegrał z graczem 1720

Aktualny wynik tego gracza to (0+0,5+1+1+0) = 2.5

Podczas, gdy jego oczekiwany wynik powinien wynosić:

$$
E_A = \\frac{1}{1 + 10^{(R_B - R_A) / \\alpha}}
$$

gdzie:
- \( R_B, R_A \) to kolejno aktualne rankingi przeciwnika i gracza A
- wartość \( \\alpha \) jest wartością swobodną, którą można kalibrować, ale przyjmujemy sugerowaną wartość 400.

Przykładowo dla pojedynku A-B oczekiwany wynik to:

$$
E_A = \\frac{1}{1 + 10^{(1603 - 1613) / 400}} = 0.51
$$

Kolejne oczekiwane wyniki pojedynków to: 0.69, 0.79, 0.54, 0.35, co w całości sumuje się do 2.88.

Ranking gracza A zostaje zaktualizowany przy pomocy następującego wzoru:

$$
N_A = R_A + k (A_A - E_A) = 1613 + 64 (2.5 - 2.88) = 1601
$$

Wartość \( k \) została ustalona na 64.

### Zwiększanie zmiany ELO dla pierwszych rozgrywek

Celem tego mechanizmu jest szybkie umiejscowienie wszystkich graczy w dobrych przedziałach ELO. Stosujemy mnożnik w postaci:

$$
f(x) = \\max[\\log(\\frac{1}{x}) + 4, 1]
$$

Funkcja ta przyjmuje następujące wartości:

| x  | f(x) | x  | f(x) |
|----|------|----|------|
| 1  | 4.00 | 13 | 1.44 |
| 2  | 3.30 | 14 | 1.36 |
| 3  | 2.90 | 15 | 1.29 |
| 4  | 2.61 | 16 | 1.23 |
| 5  | 2.39 | 17 | 1.17 |
| 6  | 2.21 | 18 | 1.11 |
| 7  | 2.05 | 19 | 1.06 |
| 8  | 1.92 | 20 | 1.004|
| 9  | 1.80 | 21 | 1.00 |
| 10 | 1.70 | 22 | 1.00 |
| 11 | 1.60 | 23 | 1.00 |
| 12 | 1.52 | 24 | 1.00 |

Skrypt sprawdza, która to jest rozgrywka danego gracza wpisana do bazy i mnoży jego wyliczoną zmianę ELO przez odpowiadający czynnik.

### Amortyzacja zmiany ELO dla gier nowo rozgrywanych

W przypadku, gdy dany gracz rozgrywa swoją pierwszą wpisaną do bazy rozgrywkę danej planszówki, jego zmiana ELO zostaje pomniejszona o 80%. Dla drugiej i trzeciej rozgrywki tej samej gry redukcje tych zmian wynoszą kolejno: 50% oraz 20%. Mechanizm ten działa jako swoisty wentyl bezpieczeństwa dla graczy ze zbudowanym ELO, aby nieoczekiwane wygrane czy przegrane w nowej grze nie wpływały znacząco na ich ranking.

### Kalibracja parametrów

Kalibracja parametrów odbywała się poprzez dopisanie do bazy danych graczy teoretycznych: jeden z nich zawsze wygrywał, drugi zawsze przegrywał. Ich ELO po 86 grach wynosiło około 1500 i 500. Początkowo zamierzano stworzyć zakres 200-2000, ale okazało się, że rankingi tych graczy stają się tak skrajne, że nie zmieniają się znacząco przy pojedynkach z graczami o rankingu około 1000.

~Za konceptualizację odpowiada all2 i Jaho-Wojownik xD
                        """)
        if elo_button == 'ELO Główna Tabela':
            elo_table = dict()
            for p in df.columns[3:]:
                elo_table[p] = np.nan

            elo_history = [copy.deepcopy(elo_table)]  # Używamy deepcopy do stworzenia głębokiej kopii

            for i in range(len(df)):
                #print(all['game'].iloc[i], all['date'].iloc[i])
                #print(elo_table)
                elo_table = elo(df.iloc[i], elo_table)
                elo_history.append(copy.deepcopy(elo_table))  # Znowu używamy deepcopy
                elo_df = pd.DataFrame(data=elo_history)
                st.write(elo_df)
                