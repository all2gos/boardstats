import json

import pandas as pd

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
