"""Mały syntetyczny arkusz w formacie Google Sheeta (kolumna 0 = indeks, game, date, liczba_graczy, gracze).

Celowo zawiera: remis na 1. miejscu, remis w środku stawki, wynik równy liczbie graczy
(stary błąd z unique()), wyniki ułamkowe i ujemne, datę bez zera wiodącego,
zduplikowany indeks arkusza, partię z 2022 (poza sezonami) i grę drużynową
(liczba_graczy mniejsza niż liczba wyników).
"""
import io

import pandas as pd

from data import parse_sheet

SHEET_CSV = """\
,game,date,liczba_graczy,Ania,Bartek,Celina,Darek
1,azul,25.12.2022,3,40,30,20,
2,azul,3.01.2023,3,35,35,10,
3,brass,10.01.2023,4,100,90,120,90
4,kaskadia,05.02.2023,3,,23.5,23,3
4,kaskadia,05.02.2023,2,-5,,,0
6,azul,01.03.2024,3,50,20,50,
7,brass,02.03.2024,2,10,,,10
8,brass,20.03.2024,3,60,70,60,50
"""

# Oczekiwane miejsca: {match_id: {gracz: miejsce}}
EXPECTED_PLACES = {
    0: {'Ania': 1, 'Bartek': 2, 'Celina': 3},
    1: {'Ania': 1, 'Bartek': 1, 'Celina': 3},
    2: {'Celina': 1, 'Ania': 2, 'Bartek': 3, 'Darek': 3},
    3: {'Bartek': 1, 'Celina': 2, 'Darek': 3},
    4: {'Darek': 1, 'Ania': 2},
    5: {'Ania': 1, 'Celina': 1, 'Bartek': 3},
    6: {'Ania': 1, 'Darek': 1},
    7: {'Bartek': 1, 'Ania': 2, 'Celina': 2, 'Darek': 4},
}


def sheet_raw():
    """Arkusz tak, jak przychodzi z CSV (data jako tekst)."""
    return pd.read_csv(io.StringIO(SHEET_CSV), index_col=0)


def sheet():
    """Arkusz po parse_sheet (tak jak zwraca load_raw)."""
    return parse_sheet(sheet_raw())
