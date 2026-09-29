"""Wykresy Altair. Bez Streamlita."""
import altair as alt
import pandas as pd

# Paleta kategoryczna (8 barw, kolejność stała), osobne stopnie dla jasnego i ciemnego tła.
PALETTE = {
    'light': ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948'],
    'dark': ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
}
# Wzory linii dla kolejnych „okrążeń” palety: gracz 1-8 ciągła, 9-16 kreska, 17-24 kropki...
DASHES = [[1, 0], [6, 3], [2, 2], [8, 3, 2, 3], [1, 4]]
REFERENCE_ELO = 1000
MUTED = {'light': '#8a8984', 'dark': '#8a8984'}


def player_styles(all_players, theme='light'):
    """Stały kolor i wzór linii dla każdego gracza, wg kolejności w arkuszu (nie zależy od zaznaczenia)."""
    colors = PALETTE[theme]
    return {p: (colors[i % len(colors)], DASHES[(i // len(colors)) % len(DASHES)]) for i, p in enumerate(all_players)}


def elo_chart(data, selected, all_players, x='numer_partii', interpolate='step-after', theme='light'):
    """Wykres ELO wybranych graczy.

    data: wynik ratings.elo_chart_data; x: 'numer_partii' albo 'data';
    interpolate: 'step-after' (schodki, wybór właściciela: ELO zmienia się tylko po partii) albo 'linear'.
    """
    styles = player_styles(all_players, theme)
    data = data[data['gracz'].isin(selected)]
    x_enc = (alt.X('numer_partii:Q', title='Numer partii', axis=alt.Axis(format='d')) if x == 'numer_partii'
             else alt.X('data:T', title='Data', axis=alt.Axis(format='%m.%Y')))
    legend = alt.Legend(title='Gracz', symbolType='stroke', symbolStrokeWidth=2.5, symbolSize=400)
    color = alt.Color('gracz:N', sort=selected, legend=legend,
                      scale=alt.Scale(domain=selected, range=[styles[p][0] for p in selected]))
    dash = alt.StrokeDash('gracz:N', sort=selected, legend=legend,
                          scale=alt.Scale(domain=selected, range=[styles[p][1] for p in selected]))
    y_enc = alt.Y('elo:Q', title='ELO', scale=alt.Scale(zero=False))
    hover = alt.selection_point(fields=[x], nearest=True, on='pointerover', empty=False, clear='pointerout')
    tooltip = [alt.Tooltip('gracz:N', title='Gracz'), alt.Tooltip('elo:Q', title='ELO', format='.1f'),
               alt.Tooltip('data:T', title='Data', format='%d.%m.%Y'), alt.Tooltip('gra:N', title='Gra'),
               alt.Tooltip('numer_partii:Q', title='Numer partii')]

    base = alt.Chart(data).encode(x=x_enc, y=y_enc)
    lines = base.mark_line(interpolate=interpolate, strokeWidth=2).encode(color=color, strokeDash=dash)
    points = base.mark_point(filled=True, size=70).encode(
        color=color,
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=tooltip,
    ).add_params(hover)
    crosshair = alt.Chart(data).mark_rule(color=MUTED[theme], strokeWidth=1).encode(
        x=x_enc, opacity=alt.condition(hover, alt.value(0.6), alt.value(0)))
    reference = alt.Chart(pd.DataFrame({'elo': [REFERENCE_ELO]})).mark_rule(
        color=MUTED[theme], strokeDash=[4, 4], strokeWidth=1).encode(y='elo:Q')
    return alt.layer(reference, lines, crosshair, points).properties(height=420)


VIS_NETWORK_JS = 'https://cdn.jsdelivr.net/npm/vis-network@10.1.2/standalone/umd/vis-network.min.js'
TEXT = {'light': '#0b0b0b', 'dark': '#ffffff'}
SURFACE = {'light': '#fcfcfb', 'dark': '#1a1a19'}


def network_html(nodes, edges, theme='light', height=600):
    """Interaktywny graf (vis-network) jako samodzielny HTML do st.components.v1.html.

    nodes: lista dict {id, label, value, lines}; edges: lista dict {from, to, value, lines};
    value steruje wielkością wierzchołka / grubością krawędzi, lines to wiersze podpisu
    (tooltip po najechaniu, a na telefonie panel pod grafem po dotknięciu).
    """
    import json
    top = max((e['value'] for e in edges), default=1) or 1
    vis_edges = [{'from': e['from'], 'to': e['to'], 'value': e['value'], 'lines': e['lines'],
                  'color': {'color': MUTED[theme], 'opacity': round(0.2 + 0.7 * e['value'] / top, 3)}}
                 for e in edges]
    # '</' -> '<\/' : żaden tekst z danych nie może zamknąć znacznika <script>
    data = json.dumps({'nodes': nodes, 'edges': vis_edges}, ensure_ascii=False).replace('</', '<\\/')
    accent, text, surface, muted = PALETTE[theme][0], TEXT[theme], SURFACE[theme], MUTED[theme]
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<script src="{VIS_NETWORK_JS}"></script>
<style>
  body {{ margin: 0; font-family: sans-serif; color: {text}; background: transparent; }}
  #wrap {{ position: relative; }}
  #graph {{ width: 100%; height: {height}px; }}
  #info {{ position: absolute; top: 6px; left: 6px; max-width: 60%; padding: 6px 10px; border-radius: 6px;
           font-size: 13px; white-space: pre-line; background: {surface}e6; border: 1px solid {muted};
           pointer-events: none; }}
  .tip {{ white-space: pre-line; font-size: 13px; }}
</style></head>
<body>
<div id="wrap">
  <div id="graph"></div>
  <div id="info">Najedź albo dotknij gracza lub połączenie, żeby zobaczyć liczby.</div>
</div>
<script>
  const data = {data};
  const tip = lines => {{ const d = document.createElement('div'); d.className = 'tip'; d.innerText = lines.join('\\n'); return d; }};
  data.nodes.forEach(n => n.title = tip(n.lines));
  data.edges.forEach(e => e.title = tip(e.lines));
  const nodes = new vis.DataSet(data.nodes), edges = new vis.DataSet(data.edges);
  const network = new vis.Network(document.getElementById('graph'), {{nodes, edges}}, {{
    nodes: {{ shape: 'dot', color: {{ background: '{accent}', border: '{accent}',
              highlight: {{ background: '{accent}', border: '{text}' }} }},
              font: {{ color: '{text}', size: 14, strokeWidth: 3, strokeColor: '{surface}' }},
              scaling: {{ min: 8, max: 34 }} }},
    edges: {{ smooth: false, scaling: {{ min: 1, max: 10 }}, selectionWidth: 2 }},
    physics: {{ solver: 'forceAtlas2Based', forceAtlas2Based: {{ gravitationalConstant: -60, springLength: 120 }},
                stabilization: {{ iterations: 300 }} }},
    interaction: {{ hover: true, tooltipDelay: 80, navigationButtons: false }}
  }});
  const info = document.getElementById('info');
  network.on('click', p => {{
    if (p.nodes.length) info.innerText = nodes.get(p.nodes[0]).lines.join('\\n');
    else if (p.edges.length) info.innerText = edges.get(p.edges[0]).lines.join('\\n');
  }});
</script>
</body></html>"""


def network_elements(long_df, now, half_life_days):
    """Wierzchołki i krawędzie grafu współgraczy dla network_html (z polskimi podpisami)."""
    from data import DATE_FORMAT, fmt_num, plural
    from stats import edge_weights, pair_matches
    edges = edge_weights(pair_matches(long_df), now=now, half_life_days=half_life_days)
    both = pd.concat([edges.rename(columns={'gracz_a': 'g', 'gracz_b': 'z'}),
                      edges.rename(columns={'gracz_b': 'g', 'gracz_a': 'z'})])
    mates = both.groupby('g').size()
    strongest = both.sort_values('waga', ascending=False).drop_duplicates('g').set_index('g')['z']
    nodes = []
    for player, n in long_df.groupby('player')['match_id'].size().items():
        k = int(mates.get(player, 0))
        lines = [player, f"{n} {plural(n, 'partia', 'partie', 'partii')}",
                 f"{k} {plural(k, 'współgracz', 'współgraczy', 'współgraczy')}"]
        if player in strongest.index:
            lines.append(f"najmocniej związany(a) z: {strongest[player]}")
        nodes.append({'id': player, 'label': player, 'value': int(n), 'lines': lines})
    edge_list = []
    for e in edges.itertuples(index=False):
        lines = [f"{e.gracz_a} — {e.gracz_b}",
                 f"{e.partie} {plural(e.partie, 'wspólna partia', 'wspólne partie', 'wspólnych partii')}"]
        if half_life_days is not None:
            lines.append(f"waga z zanikiem: {fmt_num(e.waga)}")
        lines.append(f"ostatnio: {e.ostatnia.strftime(DATE_FORMAT)}")
        edge_list.append({'from': e.gracz_a, 'to': e.gracz_b, 'value': round(float(e.waga), 3), 'lines': lines})
    return nodes, edge_list
