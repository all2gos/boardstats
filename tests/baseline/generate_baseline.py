"""Regresyjny zrzut tabel ELO i WSJG z aplikacji.

Uruchamia main.py przez streamlit AppTest (ten sam kod, który widzi użytkownik),
podmieniając pobieranie arkusza na zamrożony snapshot `sheet_snapshot.csv`,
i zapisuje wyświetlane tabele do CSV.

Użycie (z katalogu repo):
    python tests/baseline/generate_baseline.py OUT_DIR
    python tests/baseline/generate_baseline.py OUT_DIR --elo-only
    python tests/baseline/generate_baseline.py --compare OUT_DIR   # porównaj OUT_DIR z tests/baseline

Baseline w tym katalogu wygenerowano z niezmienionego kodu (commit a1bb7db) pod pandas 2.2.3,
bo pod pandas 3.x stara zakładka WSJG rzuca KeyError (TODO 0.2). ELO sprawdzono też pod
pandas 3.0.3: wynik identyczny.

Aktualizacje baseline'u WSJG (zamierzone zmiany wzoru/miejsc, ELO bez zmian):
- po 0.3 (place_in_match nie gubi graczy)
- po Z.1 (dokładne porównanie wyników zamiast int())
- po 0.4 (środek stawki (n+1)/2, round zamiast int)
"""
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SNAPSHOT = HERE / "sheet_snapshot.csv"
YEARS = ["2023", "2024", "2025", "2026"]  # lata dostępne w UI w chwili robienia baseline'u

_read_csv = pd.read_csv


def _patched_read_csv(path, *args, **kwargs):
    if isinstance(path, str) and "docs.google.com" in path:
        path = SNAPSHOT
    return _read_csv(path, *args, **kwargs)


def _app(page="main.py"):
    """Uruchamia stronę aplikacji. AppTest (Streamlit 1.52) nie przełącza stron st.navigation,
    więc strony z pages/ uruchamiamy bezpośrednio."""
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(REPO / page), default_timeout=600)
    at.run()
    return at


def _radio(at, label):
    return next(r for r in at.radio if r.label == label)


def _check(at):
    if at.exception:
        raise RuntimeError(at.exception[0].message)


def dump_elo(out: Path):
    for league in ["Open"] + YEARS:
        at = _app("pages/ranking_elo.py")
        _radio(at, "Wybierz, jeżeli chcesz zobaczyć ELO dla konkretnego roku").set_value(league).run()
        _check(at)
        frames = [d.value for d in at.dataframe]
        # aktualne ELO: kolumna "elo" (przed 2.3 "max elo"); historia: ostatnia tabela na stronie
        current = next(f for f in frames if list(f.columns) in (["elo"], ["max elo"]))
        history = frames[-1]
        current = current.rename(columns={"max elo": "elo"}).rename_axis("gracz")
        history = history.rename_axis("krok")
        tag = league.lower()
        current.to_csv(out / f"elo_current_{tag}.csv", encoding="utf-8")
        history.to_csv(out / f"elo_history_{tag}.csv", encoding="utf-8")
        print(f"ELO {league}: {len(current)} graczy, {len(history)} kroków historii")


def dump_wsjg(out: Path):
    at = _app("pages/wsjg.py")
    _check(at)
    # "wszystkie gry" bierzemy z domyślnego widoku: po powrocie do tej opcji z innej gry
    # stary kod (`is not` na stringu, TODO 0.5) pokazuje pustą tabelę.
    at.dataframe[-1].value.reset_index(drop=True).to_csv(out / "wsjg_all.csv", index=False, encoding="utf-8")
    sb = next(s for s in at.selectbox if s.label == "Zawęź do jednej gry")
    options = [o for o in sb.options if o != "wszystkie gry"]
    frames = []
    for opt in options:
        sb = next(s for s in at.selectbox if s.label == "Zawęź do jednej gry")
        sb.set_value(opt).run()
        _check(at)
        t = at.dataframe[-1].value.reset_index(drop=True)
        frames.append(t.assign(gra=opt)[["gra", "gracz", "pkt_skutecznosci"]])
    pd.concat(frames).to_csv(out / "wsjg_by_game.csv", index=False, encoding="utf-8")
    print(f"WSJG: wszystkie gry + {len(frames)} gier osobno")


def compare(other: Path, only=None):
    ok = True
    for f in sorted(HERE.glob("*.csv")):
        if f.name == SNAPSHOT.name or (only and not f.name.startswith(only)):
            continue
        g = other / f.name
        if not g.exists():
            print(f"[BRAK] {f.name}")
            ok = False
            continue
        a, b = (pd.read_csv(x, float_precision='round_trip') for x in (f, g))
        try:
            pd.testing.assert_frame_equal(a, b, check_exact=True, check_dtype=False)
            print(f"[OK]   {f.name}")
        except AssertionError as e:
            ok = False
            print(f"[RÓŻNE] {f.name}\n{e}")
    return ok


if __name__ == "__main__":
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    if sys.argv[1] == "--compare":
        sys.exit(0 if compare(Path(sys.argv[2])) else 1)
    pd.read_csv = _patched_read_csv
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    dump_elo(out)
    if "--elo-only" not in sys.argv:
        dump_wsjg(out)
