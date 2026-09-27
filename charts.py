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
