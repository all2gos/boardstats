# Boardstats — TODO dla agenta

Repo: `main.py` (Streamlit, cała aplikacja), `elo.py` (funkcja `elo`), `elo_explanation.txt`.
Dane: Google Sheet w formacie szerokim. Kolumna 0 to indeks, potem `game`, `date` (`%d.%m.%Y`) i `liczba_graczy`, a dalej jedna kolumna na gracza z liczbą punktów (NaN = nie grał). Wyższy wynik jest lepszy.

## Zasady pracy (przeczytaj najpierw)

- **Jedno zadanie = jeden commit.** Po każdym zadaniu pokaż diff i krótko opisz zmianę. Właściciel repo chce śledzić zmiany na bieżąco, więc nie łącz kilku zadań w jedną dużą zmianę.
- **Nie zmieniaj semantyki ELO.** Aktualne wartości ELO muszą zostać identyczne. Wyjątkiem jest tylko punkt 0.7 (reset sezonowego ELO w Hall of Fame), który nie dotyka głównej tabeli. Wszystko w sekcji „Decyzje do podjęcia” wymaga zgody właściciela przed implementacją.
- Nie zmieniaj formatu Google Sheeta. Ludzie wpisują wyniki ręcznie w obecnym formacie.
- Teksty w UI mają być po polsku.
- Przed pierwszą zmianą uruchom aplikację (`streamlit run main.py`) i sprawdź, czy dane się ładują. Jeśli któraś zakładka się wywala, zanotuj to i porównaj z listą poniżej.
- Do testów zrób mały syntetyczny DataFrame w tym samym formacie co arkusz (`tests/fixtures.py`) i testy w `pytest`. Pokryj nim co najmniej miejsca, remisy, WSJG, ELO i serie zwycięstw.

---

## Faza 0 — błędy (zrób najpierw, każdy osobno)

- [x] **0.1 Zależności.** `requirements.txt`: usuń `gsheetsdb`, dodaj `streamlit`, `pandas`, `numpy` i `altair` z przypiętymi wersjami. Usuń `*.toml` z `.gitignore`, a zostaw `secrets.toml` (inaczej ignorowany jest też `.streamlit/config.toml`).
- [x] **0.2 Indeksowanie pozycyjne (pandas 3.x).** `row[j]` w liniach 95 i 154 rzuca `KeyError` na pandas ≥ 3. Zamień na `row.iloc[j]`.
- [x] **0.3 Gubienie graczy przy liczeniu miejsc.** `range(3, len(row.unique()))` w liniach 94 i 153 → `range(3, len(row))`. `unique()` skraca listę przy remisach albo gdy czyjś wynik równa się `liczba_graczy`. Wtedy ostatni gracz wypada, a `place` zostaje z poprzedniej iteracji. Najlepiej od razu wydziel wspólną funkcję `place_in_match(row, player)` (patrz Faza 1).
- [x] **0.4 Wzór WSJG.** `avg_place = liczba_graczy.mean()/2` (linie 110 i 167) → `(liczba_graczy + 1).mean() / 2`. Środek stawki to `(n+1)/2`. Obecny wzór zaniża wynik przeciętnego gracza do ok. 80. Usuń też `int(...)` przed formatowaniem `:.2f` (linia 119) i zdanie z datą 26.06.23 w objaśnieniu (linia 136).
- [x] **0.5 `is not` na stringu.** Linia 142: `game_filter is not 'wszystkie gry'` → `!=`.
- [x] **0.6 Hall of Fame: crash w „Największa liczba RÓŻNYCH gier”.** `medals = {...}` jest resetowane wewnątrz pętli (linia 307), więc powstaje DataFrame o długości 1 z 4-elementowym indeksem i leci `ValueError`. Przenieś inicjalizację przed pętlę.
- [x] **0.7 Hall of Fame: ELO sezonowe nie jest sezonowe.** `elo_table` jest tworzone raz przed pętlą po latach (linie 271–273), więc każdy rok startuje ze stanu końca poprzedniego. Resetuj je na początku każdego roku, tak jak robi zakładka ELO przy wyborze roku.
- [x] **0.8 Lata na sztywno.** `[2023, 2024, 2025, 2026]` i `('Open','2023',...)` występują w 4 miejscach. Wyznaczaj lata z danych: `sorted(df['date'].dt.year.unique())`.
- [x] **0.9 Hall of Fame: bieżący sezon.** Opis mówi „poza aktualnie trwającym”, ale bieżący rok jest liczony. Wyklucz bieżący rok (`dt.date.today().year`) albo zmień opis. Domyślnie: wyklucz.
- [x] **0.10 Porządki.** Usuń nieużywane `convert_df`, `main_dict` i `import copy` (wystarczy `dict.copy()`). Nadaj etykietę `st.radio('', ...)` w linii 180 albo użyj `label_visibility="collapsed"`.

## Faza 1 — refaktor pod nowe statystyki (zalecany, przed Fazą 3+)

Prawie wszystkie nowe statystyki (duety, serie, rekordy, najczęstsi współgracze) to jedno `groupby`, jeśli dane są w formacie długim. W formacie szerokim to pętle po kolumnach.

- [x] **1.1 `data.py`:** `load_raw()` (obecne `load_data`, cache) i `to_long(df)`. Ta druga zwraca `match_id` (kolejność wiersza w arkuszu = chronologia), `date`, `game`, `n_players`, `player`, `score`, `place` (1 = najlepszy; przy remisie ta sama pozycja, ranking typu 1-1-3), `won` (`place == 1`; wspólne 1. miejsce też liczy się jako wygrana). Datę parsuj raz, tutaj, a nie w każdej zakładce.
- [x] **1.2 `stats.py`:** czyste funkcje bez Streamlita, np. `wsjg(long_df, game=None)`, `player_places(...)`, `win_streaks(...)` itd. Testy w `pytest`.
- [x] **1.3 `ratings.py`:** `compute_elo(df, year=None) -> (history_df, current)` z `@st.cache_data`. Dziś ELO liczy się od nowa przy każdym kliknięciu, a `pd.DataFrame(elo_history)` jest budowany w każdej iteracji pętli (linie 208 i 288), czyli kwadratowo. Buduj go raz po pętli. Obie zakładki (ELO i Hall of Fame) mają używać tej samej funkcji.
- [x] **1.4** Zakładki UI zostają w `main.py` (albo w `pages/`, do decyzji właściciela) i tylko wywołują funkcje z `stats.py` i `ratings.py`.

Wyniki liczbowe po refaktorze muszą być identyczne jak po Fazie 0. Sprawdź to na prawdziwych danych przed i po (zrzut tabel ELO i WSJG do CSV i porównanie).

## Faza 2 — zmiany w istniejących widokach

- [x] **2.1 „Wyświetl całą tabelę”:** pokazuj od najnowszego wiersza (`df.iloc[::-1]`), żeby łatwo sprawdzić, czy ostatnia gra się wczytała.
- [x] **2.2 „Staty dla danego gracza” — wybór gracza:** zamień `st.text_input` na `st.selectbox`. Kolejność: od gracza z najświeższą grą (ostatni `match_id` z jego udziałem), więc kto grał przed chwilą, jest na górze. Etykieta np. `Ania (ostatnio 25.09.2026)`. Domyślnie pusty placeholder (decyzja właściciela).
- [x] **2.3 Zakładka ELO:** usuń `st.write(df)` z linii 203 (duplikat tabeli z danymi). Kolumna w „Aktualne ELO” nazywa się dziś `max elo`, zmień na `elo`. W „Maksymalne ELO w historii” usuń filtr `> 1000`, który ukrywa graczy, którzy nie przebili startu.
- [x] **2.4 Historia zmian ELO:** schowaj pod `st.expander("Historia zmian ELO")`. Nie używaj `st.button`, bo w Streamlicie stan przycisku znika przy następnej interakcji.
- [x] **2.5 Wykres ELO:** zamień matplotlib na Altair (`st.altair_chart`). Wymagania:
  - interaktywny tooltip (gracz, ELO, data, gra, numer partii),
  - oś X z wyborem przez radio: numer partii / data,
  - przerywana linia odniesienia na 1000,
  - domyślnie zaznaczonych 5 graczy z najwyższym aktualnym ELO zamiast pustego wykresu,
  - legenda włączona, spójne kolory graczy (ten sam gracz ma ten sam kolor niezależnie od zaznaczenia; kolory przypisane do listy wszystkich graczy),
  - linie z `interpolate="step-after"` albo zwykłe (pokaż właścicielowi obie wersje i niech wybierze). **Wybór właściciela: schodki (`step-after`).**.
- [x] **2.6 WSJG zostaje wskaźnikiem „per gra”, a ELO ogólnym.** Nie implementuj ELO dla pojedynczej gry. Ranking WSJG dla danej gry pokaż też w nowej zakładce gry (3.1).

## Faza 3 — nowe statystyki

Definicje wspólne dla całej fazy:
- **wygrana** = `place == 1`, wspólne 1. miejsce też się liczy;
- chronologia = kolejność wierszy w arkuszu (`match_id`), bo data nie rozróżnia partii z tego samego wieczoru.

### 3.1 Nowa zakładka „Statystyki gry”

- [x] Wybór gry (`selectbox`, posortowany po liczbie rozegrań malejąco).
- [x] Liczba rozegrań, data pierwszej i ostatniej partii.
- [x] Tabela: gracz → liczba partii w tej grze, liczba wygranych, % wygranych.
- [x] **Top 5 wyników wszech czasów.** Jeden gracz może zajmować kilka miejsc. Kolumny: miejsce, gracz, wynik, data. Remisy na granicy top 5: pokaż wszystkie zremisowane wpisy.
- [x] **Najlepszy wynik każdego gracza** w tej grze (gracz, wynik, data), posortowane malejąco.
- [x] **Najniższy wynik, który wygrał:** min `score` wśród wierszy z `won == True`, plus kto i kiedy.
- [x] **Najwyższy wynik, który nie wygrał:** max `score` wśród wierszy z `won == False`, plus kto, kiedy i kto wtedy wygrał z jakim wynikiem.
- [x] Ranking WSJG dla tej gry (funkcja z 1.2).

### 3.2 Zakładka gracza — rozszerzenia

- [x] **Najlepszy wynik w każdej grze**, w którą grał: gra, najlepszy wynik, data, liczba partii w tej grze.
- [x] **Najczęstsi współgracze:** gracz → liczba wspólnych partii, posortowane malejąco.
- [x] *(propozycja, do akceptacji)* Do tabeli współgraczy dodaj bilans bezpośredni: w ilu wspólnych partiach byłem wyżej, niżej lub na równi. Daje to „nemezis” (kto najczęściej mnie wyprzedza) praktycznie za darmo. **Decyzja (27.09.2026): tak, z bilansem i wskazaniem nemezis.**

### 3.3 Hall of Fame — remisy i wyniki

- [x] **Remisy w medalach.** Dziś `iloc[0]`, `iloc[1]` i `iloc[2]` na posortowanej tabeli wybierają przypadkową osobę przy równej wartości. Zasada: ranking 1-1-3. Zremisowani dzielą medal i wszyscy są wypisani w komórce, np. `Ania, Bartek`, a następny medal jest pomijany (dwa złota → brak srebra, jest brąz). Wspólna funkcja `medal_table(values: pd.Series)` używana przez wszystkie kategorie.
- [x] **Wynik obok gracza** w każdej komórce: `Ania (47)`, dla ELO z zaokrągleniem do liczby całkowitej.
- [x] Sezonowe ELO: próg minimalnej liczby partii w sezonie, żeby ktoś po 2 grach nie wygrał sezonu. Domyślnie 10, jako stała na górze pliku. **Wartość do potwierdzenia przez właściciela.** **Decyzja: 5 partii.**
- [x] Rok bez wystarczającej liczby graczy lub partii → pusta komórka zamiast crasha (dziś `iloc[2]` rzuci `IndexError`).

### 3.4 Hall of Fame — nowe kategorie (per sezon, jak istniejące)

- [x] **Najwięcej różnych współgraczy:** liczba unikalnych osób, z którymi gracz zagrał w sezonie.
- [x] **Najczęściej grające razem duo / trio / czwórka:** dla każdej partii wszystkie kombinacje 2-, 3- i 4-osobowe jej uczestników (`itertools.combinations`), zliczenie i top 3 dla każdego rozmiaru. Kombinacja liczy się, gdy wszyscy jej członkowie grali w tej partii (inni też mogli grać).
- [x] **Najdłuższa nieprzerwana seria zwycięstw:** kolejne partie danego gracza (tylko te, w których grał, w kolejności `match_id`), w których `won == True`. Pokaż długość serii oraz datę początku i końca. Do decyzji: czy seria liczy się w obrębie sezonu, czy wszech czasów. Domyślnie w sezonie, a wszech czasów osobno na górze. **Decyzja: w sezonie + rekord wszech czasów osobno na górze.**
- *(propozycje — decyzja właściciela 27.09.2026)*
- ~~**Największy jednorazowy skok ELO** w sezonie: kto, w jakiej grze i kiedy. **Przyjęte, liczone z sezonowego ELO.**~~ **Usunięte w 5.4 (decyzja właściciela).**
- [x] **Kolekcjoner:** najwięcej różnych gier wygranych w sezonie (w odróżnieniu od „rozegranych”). **Przyjęte.**
- ~~**Maraton:** najwięcej partii rozegranych jednego dnia.~~ **Odrzucone.**

## Faza 4 — dodatkowe życzenia (27.09.2026)

- [x] **4.1 Strona gracza, „Najlepszy wynik w każdej grze”:** dodać miejsce tego wyniku w rankingu najlepszych wyników wszystkich graczy w tej grze (ranking 1-1-3) oraz % wygranych gracza w tej grze.
- [x] **4.2 Hall of Fame, wszech czasów:** tabela gracz → liczba gier, w których ma rekord wyniku, i liczba gier, w których ma najwyższy niewygrywający wynik (przy remisie liczy się każdemu), malejąco; pod nią rozwijana lista, które to gry.

## Faza 5 — poprawki właściciela (27.09.2026)

- [x] **5.1 Strona gracza, nad „Najczęściej grane gry”:** podsumowanie „zagrał w N rodzajów gier, łącznie M razy”.
- [x] **5.2 Strona gracza, nad „Statystyki odnośnie zajmowanego miejsca”:** średnia liczba graczy w partii oraz ile razy grał w danym składzie liczbowym (w dwójkę, w trójkę…).
- [x] **5.3 Hall of Fame:** usunąć „Najdłuższa seria zwycięstw — w sezonach” (zostaje rekord wszech czasów).
- [x] **5.4 Hall of Fame:** usunąć całkowicie „Największy jednorazowy skok ELO” (sekcja, funkcje i testy).
- [x] **5.5 Hall of Fame:** usunąć opis konceptu „Unikalna gra kolekcja medalowa?”.
- [x] **5.6 Zakładka ELO, „Maksymalne ELO w historii”:** obok wartości data, kiedy maksimum zostało osiągnięte (pierwszy raz).
- [x] **5.7 Strona gracza, nemezis nominalny i względny:** względny = wyprzedzenia / wspólne partie, tylko współgracze z min. 5 wspólnymi partiami (decyzja właściciela); kolumna „% wyprzedzeń” w tabeli współgraczy.
- [x] **5.8 Hall of Fame, nemezis:** dla ilu graczy ktoś jest nemezis (osobno nominalnie i względnie, wszech czasów) + rozwijana lista, dla kogo.
- [x] **5.9 Strona gracza bez WSJG:** usunięty współczynnik i przycisk z dołu strony; wyjaśnienie, jak liczone jest WSJG, przeniesione do zakładki WSJG (rozwijany panel).
- [x] **5.10 Strona gracza, liczba graczy w partiach:** tabela liczba graczy → partie, nad nią „Średnio w partii X graczy.” (bez dopisku o innych osobach).

## Faza 6 — więcej statystyk dla „dojrzałych” gier (27.09.2026)

- [x] **6.1 Próg dojrzałości:** gra z więcej niż 10 partiami jest „dojrzała”; wtedy komunikat, że prezentujemy więcej statystyk, i poniższe sekcje. Próg jako stała.
- [x] **6.2 Typowy wynik:** średnia, mediana, IQR (Q1–Q3) wszystkich wyników i średni wynik zwycięzcy.
- [x] **6.3 Wynik a liczba graczy:** dla każdej liczby graczy (z arkusza): partie, średni wynik, średni wynik zwycięzcy.
- [x] **6.4 Najlepszy debiut:** najwyższy wynik w pierwszej partii gracza w tę grę (remisy: wszyscy).
- ~~**6.5 Wynik w czasie:** wykres średniego wyniku partii i wyniku zwycięzcy w kolejnych partiach (oś X: data).~~ **Usunięte w 6.6 (decyzja właściciela).**
- [x] **6.6** Usunąć wykres „Wynik w czasie” (sekcja, funkcja, testy).
- [x] **6.7** Sekcje dla dojrzałych gier przenieść na górę, tuż pod liczbę partii i daty pierwszej/ostatniej partii.
- [x] **6.8** Sekcje dla dojrzałych gier w zwijanym panelu.
- [x] **6.9** IQR pokazywany jako przedział „Q1–Q3”, a nie jego szerokość.
- [x] **6.10** IQR bez osobnej metryki (nie mieściła się); przedział Q1–Q3 tylko w szarym podpisie pod metrykami.

## Faza 7 — Hall of Fame gier (27.09.2026)

- [x] **7.1** Na dole Hall of Fame sekcja „Hall of Fame gier”: medale (złoto/srebro/brąz, ranking 1-1-3) za liczbę różnych graczy, którzy kiedykolwiek zagrali w daną grę.
- [x] **7.2** Medale za rozstęp czasu między pierwszą a ostatnią partią gry (w dniach).

## Decyzje do podjęcia (zapytaj właściciela, nie zgaduj)

1. **ELO nie jest zero-sum.** Każdy gracz ma własny mnożnik (nowicjusz do ×4, nowa gra ×0.2), więc suma punktów dryfuje. W symulacji 5 graczy i 180 losowych partii suma spadła z 5000 do 4887. Opcje: zostawić bez zmian, albo stosować mnożniki symetrycznie do pary. Zmieni to ranking, więc bez zgody niczego tu nie ruszaj.
2. `liczba_graczy` z arkusza a faktyczna liczba wyników w wierszu: jeśli się różnią, co jest źródłem prawdy? Proponowane: liczyć z danych, a przy niezgodności wyświetlić ostrzeżenie z numerem wiersza. **Decyzja (27.09.2026): źródłem prawdy jest `liczba_graczy` z arkusza** (np. brass 27.12.2022: dwie osoby grały jako jeden gracz). Bez ostrzeżeń w aplikacji; błędne wiersze właściciel poprawił w arkuszu.
3. Struktura UI: zagnieżdżone `st.radio` czy natywne strony Streamlit (`pages/`)? **Decyzja: strony przez `st.navigation` (nawigacja u góry), pliki w `pages/`.**

## Poza zakresem (na razie)

- „Program do proponowania gier” (linie 336–345): zostaje jak jest, nie ruszać.
- ELO liczone per gra: odrzucone, zostaje WSJG.
- **Liczniki partii w ELO zostają liczone po dacie (`date <= l['date']`, `elo.py` linie 45 i 49). To świadoma decyzja właściciela, nie poprawiaj tego.** Uwaga przy refaktorze (1.3): `compute_elo` musi odtwarzać to zachowanie 1:1. Nie przechodź na liczenie po `match_id`, nawet jeśli wydaje się „poprawniejsze”. Test regresyjny: wartości ELO (aktualne i cała historia) na prawdziwych danych identyczne przed i po refaktorze.
- Zmiany formatu arkusza.

## Znalezione po drodze

- [x] **Z.1 `int()` przy porównaniu miejsc** ucina ułamki (w danych 6 niecałkowitych wyników, np. 135.1, 115.5), więc 23.5 i 23 liczą się jako remis. *Zgoda właściciela: porównywać dokładne wartości.*
- **Z.2 Daty cofające się w arkuszu** (4 miejsca, m.in. wiersz 100 „trivial pursuit 06.10.2024” między styczniowymi partiami, pewnie 06.01.2024). ELO liczy liczniki po dacie, więc to wpływa na mnożniki. Do poprawy w arkuszu przez właściciela, kodu nie ruszamy.
- **Z.3 Zduplikowany indeks 183 w arkuszu** (dwie partie „planeta x” 01.01.2025, brak 184). W 1.1 `match_id` brać z pozycji wiersza, nie z indeksu arkusza.
- **Z.4 `liczba_graczy` ≠ liczba wyników** w 3 wierszach (indeksy 5, 79, 207). Dotyczy decyzji nr 2. Rozstrzygnięte: wiersz 5 to gra drużynowa (poprawny), 79 i 207 poprawione w arkuszu.
- **Z.5 Hall of Fame 0.6 pod pandas 3** nie rzuca `ValueError`, tylko rozciąga wynik ostatniego roku na wszystkie lata (cicho złe dane).
- **Z.6 WSJG „wszystkie gry”** pokazuje pustą tabelę po powrocie do tej opcji z innej gry. To skutek 0.5.
- [x] **Z.7 Objaśnienie WSJG odwraca iloraz.** Tekst w zakładce gracza mówi „stosunek tej pierwszej wartości (średnie miejsce gracza) przez tą drugą (środek stawki)”, a kod liczy środek stawki / miejsce gracza. Liczby są dobre, zły jest opis. *Decyzja: wzór zostaje (wyżej = lepiej), poprawiony opis.*
- [x] **Z.8 Zakładka gracza: `ZeroDivisionError` przy pustym filtrze.** Zaznaczenie checkboxa „wybrana gra” lub „sezon” przed wybraniem wartości (albo filtr bez żadnej partii, np. Mati + ankh + 2026) daje `your_place /= 0`. Komunikaty „Czekam aż wybierzesz…” nigdy się nie pokazują. Przy pustym wyniku filtra pokazujemy komunikat i nie liczymy statystyk. *Zgoda właściciela.*
- **Z.9 Literówka w nazwie gry w arkuszu:** „zamki burgundi” (1 partia) i „zamki burgundii” (2 partie) liczą się jako dwie różne gry (widać to m.in. w rekordach Hall of Fame i w Statystykach gry). Do poprawy w arkuszu przez właściciela, kodu nie ruszamy.
- [x] **Z.10 Sprzeczne zależności w `requirements.txt`** (błąd z 0.1): `streamlit==1.52.2` wymaga `pandas<3`, a przypięte było `pandas==3.0.3`, więc Streamlit Cloud nie mógł zainstalować zależności. Poprawka: `streamlit==1.64.0` (pierwsze wersje z `pandas<4` to 1.60+, 1.64.0 = wersja na Streamlit Cloud) i `pyarrow==22.0.0` (25.0.1 ma znany segfault). Sprawdzone: `pip install --dry-run --ignore-installed -r requirements.txt` rozwiązuje się od zera, 122 testy przechodzą na 1.64.

Ustalenia właściciela (27.09.2026): 2022 nie jest sezonem (pomijany w wyborze roku i w Hall of Fame; Open liczy wszystko). WSJG wszędzie zaokrąglany do liczby całkowitej (`round`). Baseline WSJG aktualizowany osobno po 0.3, Z.1 i 0.4.
