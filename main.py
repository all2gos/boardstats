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
            """
            Zasada działania ELO:

1. ELO startowe to 1000 pkt
2. Każdorazowa rozgrywka na potrzeby ELO jest liczona jako pojedyczne pojedynki 1 vs 1 we wszystkich kombinacja: np. gdy grają trzej gracze (ABC) skrypt sprawdza wyniki indywidualnych meczy A-B, B-C, i A-C i traktuje je jako odbyte jednocześnie (analogia do meczy na pojedycznym turnieju szachowym)
3. Ranking ELO nie uwzględnia tego jak silna jest wygrana (podobnie jak w szachach, ale w szachach "siła" wygranej jest dość subiektywna, a tutaj mamy ją wyrażoną w pkt zwycięstwa najczęściej)

Wzory liczenia ELO:

Przykład:

Gracz A ma ranking 1613 i:

a) przegrał z graczem 1603

b) zremisował z graczem 1477

c) wygrał z graczem 1388

d) wygrał z graczem 1586

e) przegrał z graczem 1720

Aktualny wynik tego gracza to (0+0,5+1+1+0) = 2.5

Podczas, gdy jego faktyczny wynik powinien wynosić:

$$E_A = \frac{1}{1+10^{(R_B-R_A)/\alpha}}$$

gdzie:

$R_B, R_A$ to kolejno aktualne rankingi przeciwnika i gracza A

wartość $\alpha$ jest wartością swobodną i można ją dowolnie kalibrować, ja w tym miejscu jednak bym niczego nie próbował i zostawił ją na wartości sugerowanej czyli 400

Czyli przykładowo dla pojedynku A-B oczekiwany wynik to:

$$E_A = \frac{1}{1+10^{(1603-1613)/400}}=0.51$$

Kolejne oczekiwane wyniki pojedynkow to: 0.69, 0.79, 0.54, 0.35, co w całości sumuje się do 2,88

Ranking gracza A zostaje zaktualizowany przy pomocy następującego wzoru:

$$N_A = R_A + 32*(A_A-E_A) = 1613 + k*(2,5-2,88)=1601$$

Ponownie $k$, to wartość swobodna i może być dowolnie kalibrowana. Ja w tym miejscu chciałbym osiągnąć efekt podobny jak w szachach; czyli wygrana z osobą o zbliżonym rankingu to 8-10 oczek w górę. Należy tutaj jednak zwrócić uwagę na istotny czynnik: rozegranie pojedynczej planszówki zawsze składa się z kilku pojedynków. Efektem tego jest sytuacja, w której w przypadku gry trzyosobowej rozstęp zmiany ELO gracza to dwukrotność takiej zmiany w pojedycznym pojedynku, a w przypadku gry pięcioosobowej: czterokrotność. Czynnik ten został uwzględniony w skrypcie i każdorazowo wyznaczona zmiana ELO, która jest sumą zmian wszystkich takich pojedynków jest dzielona przez liczbę odbytych pojedynków.

Wartość $k$ została wyznaczona na 64

I to stanowi bazę wyliczania ELO, poza tym stosujemy następujące mechanizmy:

### Zwiększanie zmiany ELO dla pierwszych rozgrywek
Celem tego mechanizmu jest możliwie szybkie umiejscowienie wszystkich w dobrych przedziałach ELO (bo do bazy danych może być wpisana osoba, która właśnie rozgrywa swoją pierwszą planszówkę jak i osoba, która nie dość, że ma lata doświadczenia to jeszcze gra często i dobrze)

Moją propozycją jest stosowanie mnożnika w postaci:

$$f(x) = max\left[log\left(\frac{1}{x}\right)+4, 1]\right]$$

Funkcja ta przyjmuje następujące wartości:

|x|f(x)|x|f(x)|
|---|---|---|---|
|1|4.00|13|1.44|
|2|3.30|14|1.36|
|3|2.90|15|1.29|
|4|2.61|16|1.23|
|5|2.39|17|1.17|
|6|2.21|18|1.11|
|7|2.05|19|1.06|
|8|1.92|20|1.004|
|9|1.80|21|1.00|
|10|1.70|22|1.00|
|11|1.60|23|1.00|
|12|1.52|24|1.00|

Skrypt sprawdza każdorazowo, która to jest rozgrywka danego gracza wpisana do bazy i mnoży jego wyliczoną zmianę ELO przez odpowiadający czynnik.

### Amortyzacja zmiany ELO dla gier nowo rozgrywanych

W przypadku, gdy dany gracz rozgrywa swoją pierwsza wpisaną do bazy rozgrywkę danej planszówki jego zmiana ELO zostaje pomniejszona o 80%, dla drugiej i trzeciej rozgrywki tej samej gry redukcje tych zmian wynoszą kolejno: 50% oraz 20%. Mechanizm ten został zastosowany jako swoisty wentyl bezpieczeństwa dla graczy ze zbudowanym ELO, tak żeby nieoczekiwane wygrane czy przegrane w grze, której zasady dopiero przez tę osobę są poznawane nie wpływały w sposób znaczny na siłę gry.

Dokładnie w takiej formie ELO zostaje zaimplementowane na potrzeby boardstatsa.

Warto wspomnieć, że kalibrowanie parametrów odbywało się poprzez dopisane do bazy danych graczy teoretycznych: jeden z nich zawsze wygrywał, drugi zawsze przegrywał. Ich ELO po 86 grach wynosiło około 1500 i 500. Chciałem początkowo stworzyć zakres 200-2000, ale w trakcie testowania zorientowałem się, że od pewnego momentu rankingi tych graczy są tak skrajne, że nie ulegałyby żadnej większej zmianie przy pojedynkach z graczami, którzy jednak oscylują w okolicy siły gry ~1000.


            """
  