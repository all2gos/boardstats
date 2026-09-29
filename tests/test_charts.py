import json

import pandas as pd
import pytest

from charts import DASHES, PALETTE, REFERENCE_ELO, elo_chart, player_styles
from data import player_columns
from ratings import elo_chart_data
from tests.test_ratings import compute
from tests.fixtures import sheet

MANY = [f'Gracz {i}' for i in range(35)]


def test_player_styles_unique_and_stable():
    styles = player_styles(MANY)
    assert len({(c, tuple(d)) for c, d in styles.values()}) == 35  # każdy gracz ma inną parę kolor + wzór
    assert styles['Gracz 0'] == (PALETTE['light'][0], DASHES[0])
    assert styles['Gracz 8'] == (PALETTE['light'][0], DASHES[1])  # ta sama barwa, inny wzór linii
    assert player_styles(MANY, 'dark')['Gracz 3'][0] == PALETTE['dark'][3]


def spec(selected, **kwargs):
    df = sheet()
    history, _ = compute(df)
    return elo_chart(elo_chart_data(history, df), selected, player_columns(df), **kwargs).to_dict()


def line_layer(s):
    return next(layer for layer in s['layer'] if layer['mark']['type'] == 'line')


def test_colors_follow_player_not_selection():
    styles = player_styles(player_columns(sheet()))
    for selected in (['Darek', 'Ania'], ['Celina', 'Darek', 'Bartek']):
        color = line_layer(spec(selected))['encoding']['color']
        assert color['scale']['domain'] == selected
        assert color['scale']['range'] == [styles[p][0] for p in selected]


def test_chart_contents():
    s = spec(['Ania', 'Darek'])
    line = line_layer(s)
    assert line['mark']['interpolate'] == 'step-after'
    assert line['encoding']['color']['legend']['title'] == 'Gracz'
    assert line['encoding']['x']['field'] == 'numer_partii'
    reference = s['layer'][0]
    assert reference['mark']['type'] == 'rule' and reference['mark']['strokeDash'] == [4, 4]
    assert json.dumps(s).count(f'"elo": {REFERENCE_ELO}') == 1
    points = next(layer for layer in s['layer'] if layer['mark']['type'] == 'point')
    assert [t['field'] for t in points['encoding']['tooltip']] == ['gracz', 'elo', 'data', 'gra', 'numer_partii']
    assert line_layer(spec(['Ania'], x='data'))['encoding']['x']['field'] == 'data'


def test_chart_data_only_selected_players():
    s = spec(['Ania'])
    data = pd.DataFrame(s['datasets'][line_layer(s)['data']['name']])
    assert set(data['gracz']) == {'Ania'}


def test_network_html():
    from charts import VIS_NETWORK_JS, network_html
    nodes = [{'id': 'Ania', 'label': 'Ania', 'value': 7, 'lines': ['Ania', '7 partii']},
             {'id': 'Bartek', 'label': 'Bartek', 'value': 6, 'lines': ['Bartek', '6 partii']}]
    edges = [{'from': 'Ania', 'to': 'Bartek', 'value': 2.5, 'lines': ['Ania — Bartek', '5 wspólnych partii']}]
    html = network_html(nodes, edges, theme='dark')
    assert VIS_NETWORK_JS in html and "'#3987e5'" in html  # akcent z ciemnej palety
    assert '"Ania — Bartek"' in html and '"5 wspólnych partii"' in html  # polskie znaki bez escapowania
    assert '"opacity": 0.9' in html  # najmocniejsza krawędź ma pełne krycie
    assert "network.on('click'" in html  # panel na telefon


def test_network_html_js_is_valid(tmp_path):
    """Skrypt w wygenerowanym HTML musi się parsować (node --check), jeśli node jest dostępny."""
    import re
    import shutil
    import subprocess
    from charts import network_html
    node = shutil.which('node')
    if not node:
        pytest.skip('brak node')
    html = network_html([{'id': 'A', 'label': 'A', 'value': 1, 'lines': ['A', '1 partia']}], [], theme='light')
    script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
    (tmp_path / 'g.js').write_text(script, encoding='utf-8')
    assert subprocess.run([node, '--check', str(tmp_path / 'g.js')], capture_output=True).returncode == 0


def test_network_elements_on_snapshot_and_valid_js(tmp_path):
    import re
    import shutil
    import subprocess
    from pathlib import Path
    from charts import network_elements, network_html
    from data import parse_sheet, to_long
    snapshot = Path(__file__).parent / 'baseline' / 'sheet_snapshot.csv'
    long = to_long(parse_sheet(pd.read_csv(snapshot, index_col=0)))
    nodes, edges = network_elements(long, now=pd.Timestamp(2026, 9, 27), half_life_days=182.62)
    assert len(nodes) == 35 and all(len(n['lines']) >= 3 for n in nodes)
    assert all(e['value'] > 0 and e['lines'][0].count(' — ') == 1 for e in edges)
    node = shutil.which('node')
    if node:
        script = re.search(r'<script>(.*?)</script>', network_html(nodes, edges), re.S).group(1)
        (tmp_path / 'g.js').write_text(script, encoding='utf-8')
        assert subprocess.run([node, '--check', str(tmp_path / 'g.js')], capture_output=True).returncode == 0


def test_network_html_escapes_script_end():
    from charts import network_html
    html = network_html([{'id': 'x', 'label': '</script><b>', 'value': 1, 'lines': ['</script>']}], [])
    assert html.count('</script>') == 2  # tylko dwa prawdziwe znaczniki (biblioteka + nasz skrypt)
