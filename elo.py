import numpy as np
import pandas as pd
def elo(row, elo_table, df):

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
