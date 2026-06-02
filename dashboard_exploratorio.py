"""
Dashboard 2 — Exploração Interativa da Aviação Civil Brasileira
================================================================
Sete abas temáticas sobre ~3 milhões de voos (ANAC/VRA, 2022–2025), com
filtros encadeados na barra lateral:

    Visão · Pontualidade · Frota & Capacidade · Malha & Geografia ·
    Tarifas · Comparativo configurável · Tabela (com download)

    python dashboard_exploratorio.py    →    http://localhost:8051
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update
import dash_bootstrap_components as dbc

import lib_dados as L
from lib_dados import (T, fmt, fmt_compacto, fmt_reais, layout_base, fig_vazia,
                       CORES_GRUPO, CORES_FABRICANTE, MESES_PT, ORDEM_MESES, ORDEM_DIAS,
                       taxa_pct)

# ───────────────────────────────── DADOS ──────────────────────────────────────
df = L.carregar()
tarifas = L.carregar_tarifas()

ANOS    = sorted(df["ANO"].dropna().unique().astype(int))
GRUPOS  = [g for g in ["Azul", "LATAM", "Gol", "Regionais", "Internacionais", "Cargueiras"]
           if g in df["GRUPO"].unique()]
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

app = dash.Dash(
    __name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Aviação Brasil · Exploração", suppress_callback_exceptions=True,
)
server = app.server


def opt(lst):
    return [{"label": f"  {v}", "value": v} for v in lst]


# ─────────────────────────────── FILTRAGEM ────────────────────────────────────

def filtrar(anos, grupos, regioes, seg, pont):
    """Aplica os filtros da barra lateral ao dataset principal."""
    mask = pd.Series(True, index=df.index)
    if anos:
        mask &= df["ANO"].isin([int(a) for a in anos])
    if grupos:
        mask &= df["GRUPO"].isin(grupos)
    # região só restringe quando o usuário desmarca alguma (preserva voos do exterior)
    if regioes and set(regioes) != set(REGIOES):
        mask &= df["ORIG_REGIAO"].isin(regioes)
    if seg == "dom":
        mask &= df["DOMESTICO"]
    elif seg == "int":
        mask &= df["SEGMENTO"] == "Internacional"
    if pont == "atr":
        mask &= df["ATRASADO"]
    elif pont == "ok":
        mask &= ~df["ATRASADO"]
    return df.loc[mask]


def filtrar_tarifas(anos, grupos, regioes):
    """Filtra a base de tarifas pelos filtros compatíveis."""
    if tarifas.empty:
        return tarifas
    m = pd.Series(True, index=tarifas.index)
    if anos:
        m &= tarifas["ANO"].isin([int(a) for a in anos])
    if grupos:
        m &= tarifas["GRUPO"].isin(grupos) | tarifas["EMPRESA"].isin(grupos)
    if regioes and set(regioes) != set(REGIOES):
        m &= tarifas["ORIG_REGIAO"].isin(regioes)
    return tarifas.loc[m]


# ─────────────────────────────── COMPONENTES ──────────────────────────────────

def painel(graf_id, titulo, altura=340, sub=None):
    """Card com cabeçalho e gráfico."""
    cab = [html.Span(titulo, className="pn-tit")]
    if sub:
        cab.append(html.Span(sub, className="pn-sub"))
    return dbc.Card([
        dbc.CardHeader(cab, className="pn-head"),
        dbc.CardBody(dcc.Graph(id=graf_id, style={"height": f"{altura}px"},
                               config={"displayModeBar": False})),
    ], className="painel mb-3")


def check(id_, opcoes, valor):
    return dcc.Checklist(id=id_, options=opt(opcoes), value=valor,
                         labelStyle={"display": "block", "marginBottom": "3px"},
                         className="chk")


sidebar = html.Div([
    html.Div([html.Span("✈", className="sb-logo"),
              html.Div([html.Div("Exploração", className="sb-t1"),
                        html.Div("Aviação Civil BR", className="sb-t2")])],
             className="sb-brand"),

    html.Div("Filtros", className="sb-section"),
    html.Label("📅 Período", className="flbl"),
    check("f-anos", ANOS, ANOS),
    html.Label("🏢 Grupo econômico", className="flbl"),
    check("f-grupos", GRUPOS, GRUPOS),
    html.Label("🗺 Região de origem", className="flbl"),
    check("f-regioes", REGIOES, REGIOES),
    html.Label("🌐 Segmento", className="flbl"),
    dcc.RadioItems(id="f-seg", value="all", className="chk",
                   options=[{"label": "  Todos", "value": "all"},
                            {"label": "  Doméstico", "value": "dom"},
                            {"label": "  Internacional", "value": "int"}],
                   labelStyle={"display": "block", "marginBottom": "3px"}),
    html.Label("⏱ Pontualidade", className="flbl"),
    dcc.RadioItems(id="f-pont", value="all", className="chk",
                   options=[{"label": "  Todos", "value": "all"},
                            {"label": "  Só atrasados", "value": "atr"},
                            {"label": "  Só no horário", "value": "ok"}],
                   labelStyle={"display": "block", "marginBottom": "3px"}),

    html.Div(id="sb-stats", className="sb-stats"),
], className="sidebar")


def aba(label, tab_id, linhas):
    return dbc.Tab(label=label, tab_id=tab_id, children=html.Div(linhas, className="aba-body"))


conteudo = html.Div([
    dbc.Tabs(id="tabs", active_tab="tab-visao", children=[
        aba("🗺 Visão", "tab-visao", [
            dbc.Row([dbc.Col(painel("g-vol", "Volume de voos no tempo", 320), md=8),
                     dbc.Col(painel("g-share", "Participação por grupo", 320), md=4)]),
            dbc.Row([dbc.Col(painel("g-rotas", "Top 15 rotas", 380), md=6),
                     dbc.Col(painel("g-heat", "Intensidade · mês × dia da semana", 380), md=6)]),
        ]),
        aba("⏱ Pontualidade", "tab-pont", [
            dbc.Row([dbc.Col(painel("g-hist", "Distribuição dos atrasos de partida", 320), md=6),
                     dbc.Col(painel("g-hora", "Atraso por hora · partida vs chegada", 320,
                                    "evidencia a recuperação em voo"), md=6)]),
            dbc.Row([dbc.Col(painel("g-dia", "Taxa de atraso por dia da semana", 320), md=6),
                     dbc.Col(painel("g-canc", "Taxa de cancelamento por mês", 320), md=6)]),
        ]),
        aba("🛩 Frota & Capacidade", "tab-frota", [
            dbc.Row([dbc.Col(painel("g-fab", "Participação por fabricante", 320), md=4),
                     dbc.Col(painel("g-fam", "Famílias de aeronave mais usadas", 320), md=8)]),
            dbc.Row([dbc.Col(painel("g-assentos", "Porte médio da aeronave por grupo", 320), md=5),
                     dbc.Col(painel("g-cap", "Capacidade ofertada no tempo (assentos-km)", 320), md=7)]),
        ]),
        aba("🌐 Malha & Geografia", "tab-malha", [
            dbc.Row([dbc.Col(painel("g-mapa", "Malha aérea nacional", 560), md=7),
                     dbc.Col([painel("g-fluxo", "Fluxo entre regiões", 270),
                              painel("g-distatr", "Distância × recuperação em voo", 270)], md=5)]),
        ]),
        aba("💲 Tarifas", "tab-tarifas", [
            dbc.Row([dbc.Col(painel("g-tar-emp", "Tarifa média por companhia", 320), md=5),
                     dbc.Col(painel("g-tar-tempo", "Evolução da tarifa média", 320), md=7)]),
            dbc.Row([dbc.Col(painel("g-tar-dist", "Tarifa × distância (tamanho = volume)", 330), md=7),
                     dbc.Col(painel("g-tar-rotas", "Rotas mais caras e mais baratas", 330), md=5)]),
        ]),
        aba("🔭 Curiosidades", "tab-cur", [
            html.Div("🔎 Fatos e relações curiosas, calculados ao vivo a partir dos dados — "
                     "tudo muda conforme os filtros da barra lateral. Passe o mouse nos gráficos "
                     "para ver os números.", className="cur-intro"),
            html.Div(id="cur-cards", className="cur-grid"),
            dbc.Row([
                dbc.Col(painel("cur-heat", "O que tem a ver com o quê?", 360,
                               "quais coisas andam juntas"), md=7),
                dbc.Col(painel("cur-fab", "Qual fabricante atrasa mais?", 360,
                               "% de voos atrasados por fabricante"), md=5),
            ]),
            dbc.Row([
                dbc.Col(painel("cur-rkm", "Preço por km despenca com a distância", 330,
                               "a tarifa quase não muda; o R$/km, sim"), md=6),
                dbc.Col(painel("cur-cresc", "Rotas que mais cresceram e encolheram", 330,
                               "1º vs último ano do recorte"), md=6),
            ]),
        ]),
        aba("📊 Comparativo", "tab-comp", [
            dbc.Card(dbc.CardBody(dbc.Row([
                dbc.Col([html.Label("Dimensão (eixo X)", className="flbl-c"),
                         dcc.Dropdown(id="c-x", clearable=False, value="GRUPO", options=[
                             {"label": "Grupo econômico", "value": "GRUPO"},
                             {"label": "Companhia", "value": "EMPRESA_NOME"},
                             {"label": "Mês", "value": "MES_PT"},
                             {"label": "Ano", "value": "ANO"},
                             {"label": "Trimestre", "value": "TRIMESTRE"},
                             {"label": "Região de origem", "value": "ORIG_REGIAO"},
                             {"label": "Fabricante", "value": "FABRICANTE"},
                             {"label": "Faixa horária", "value": "FAIXA_HORARIA"},
                             {"label": "Dia da semana", "value": "DIA_SEM_PT"},
                             {"label": "Segmento", "value": "SEGMENTO"}])], md=4),
                dbc.Col([html.Label("Métrica", className="flbl-c"),
                         dcc.Dropdown(id="c-m", clearable=False, value="n_voos", options=[
                             {"label": "Nº de voos", "value": "n_voos"},
                             {"label": "Taxa de atraso (%)", "value": "pct_atraso"},
                             {"label": "Taxa de cancelamento (%)", "value": "pct_canc"},
                             {"label": "Atraso médio (min)", "value": "med_atraso"},
                             {"label": "Porte médio (assentos)", "value": "assentos"},
                             {"label": "Distância média (km)", "value": "dist"}])], md=4),
                dbc.Col([html.Label("Separar por cor", className="flbl-c"),
                         dcc.Dropdown(id="c-c", clearable=False, value="none", options=[
                             {"label": "Nenhum", "value": "none"},
                             {"label": "Grupo", "value": "GRUPO"},
                             {"label": "Ano", "value": "ANO"},
                             {"label": "Segmento", "value": "SEGMENTO"},
                             {"label": "Fabricante", "value": "FABRICANTE"}])], md=4),
            ]), className="painel mb-3 ctrl-card")),
            painel("g-comp", "Comparativo configurável", 440),
        ]),
        aba("📋 Tabela", "tab-tabela", [
            dbc.Card(dbc.CardBody([
                dbc.Row([
                    dbc.Col([html.Label("Colunas exibidas", className="flbl-c"),
                             dcc.Dropdown(id="tb-cols", multi=True,
                                          options=[{"label": c, "value": c} for c in df.columns],
                                          value=[c for c in ["EMPRESA_NOME", "ROTA_IATA",
                                                 "ORIG_CIDADE", "DEST_CIDADE", "ANO", "MES",
                                                 "MODELO_EQUIPAMENTO", "SITUACAO", "ATRASO_MIN",
                                                 "DIST_KM"] if c in df.columns])], md=9),
                    dbc.Col([html.Label(" ", className="flbl-c"),
                             html.Button("⬇ Baixar CSV", id="tb-btn", className="btn-dl")], md=3),
                ]),
                html.Div("Mostrando até 500 linhas. O download traz até 50.000 linhas do recorte.",
                         className="tb-nota"),
            ]), className="painel mb-3 ctrl-card"),
            dcc.Loading(html.Div(id="tb-cont"), type="dot", color=T.ACENTO),
            dcc.Download(id="tb-download"),
        ]),
    ]),
], className="conteudo")

app.layout = html.Div([sidebar, conteudo], className="wrap")


# ───────────────────────────── STATS DA SIDEBAR ───────────────────────────────

@app.callback(
    Output("sb-stats", "children"),
    [Input("f-anos", "value"), Input("f-grupos", "value"), Input("f-regioes", "value"),
     Input("f-seg", "value"), Input("f-pont", "value")])
def stats(anos, grupos, regioes, seg, pont):
    dff = filtrar(anos, grupos, regioes, seg, pont)
    def item(v, lab):
        return html.Div([html.Div(v, className="stt-v"), html.Div(lab, className="stt-l")],
                        className="stt")
    return [
        html.Div("Recorte atual", className="sb-section"),
        item(fmt_compacto(len(dff)), "voos"),
        item(f"{taxa_pct(dff['ATRASADO'])}%".replace(".", ","), "atrasados"),
        item(f"{taxa_pct(dff['CANCELADO'])}%".replace(".", ","), "cancelados"),
        item(fmt(dff["ROTA"].nunique()), "rotas"),
    ]


# ─────────────────────────────── ABA: VISÃO ───────────────────────────────────

@app.callback(
    [Output("g-vol", "figure"), Output("g-share", "figure"),
     Output("g-rotas", "figure"), Output("g-heat", "figure")],
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value")])
def ab_visao(tab, anos, grupos, regioes, seg, pont):
    if tab != "tab-visao":
        return [no_update] * 4
    dff = filtrar(anos, grupos, regioes, seg, pont)
    if dff.empty:
        return [fig_vazia()] * 4

    # Volume no tempo por grupo
    g = dff.groupby(["PERIODO", "GRUPO"], observed=True).size().reset_index(name="V")
    fig_vol = px.area(g.sort_values("PERIODO"), x="PERIODO", y="V", color="GRUPO",
                      color_discrete_map=CORES_GRUPO,
                      labels={"V": "Voos", "PERIODO": "Mês", "GRUPO": "Grupo"})
    fig_vol.update_layout(layout_base(), legend=dict(orientation="h", y=1.12, x=0),
                          hovermode="x unified")
    fig_vol.update_xaxes(tickangle=45)

    # Share por grupo
    s = dff.groupby("GRUPO", observed=True).size().sort_values(ascending=False)
    fig_share = go.Figure(go.Pie(
        labels=s.index.tolist(), values=s.values, hole=0.62, sort=False,
        marker=dict(colors=[CORES_GRUPO.get(k, T.ACENTO) for k in s.index],
                    line=dict(color="white", width=2)),
        textinfo="percent", textfont=dict(color="white", size=11)))
    fig_share.update_layout(layout_base(), showlegend=True,
                            legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"),
                            annotations=[dict(text=f"{fmt_compacto(s.sum())}<br>voos", x=0.5, y=0.5,
                                              showarrow=False, font=dict(size=13, color=T.PRIMARIA))])

    # Top rotas (IATA)
    top = dff.groupby("ROTA_IATA", observed=True).size().nlargest(15).reset_index(name="V").sort_values("V")
    fig_rotas = go.Figure(go.Bar(
        x=top["V"], y=top["ROTA_IATA"], orientation="h",
        marker=dict(color=top["V"], colorscale=L.ESCALA_AZUL),
        text=[fmt_compacto(v) for v in top["V"]], textposition="outside",
        cliponaxis=False, hovertemplate="<b>%{y}</b><br>%{x:,} voos<extra></extra>"))
    fig_rotas.update_layout(layout_base(), margin=dict(l=10, r=60, t=20, b=36))
    fig_rotas.update_yaxes(automargin=True)
    L.folga_eixo(fig_rotas, top["V"].max())

    # Heatmap mês × dia
    h = dff.groupby(["MES_PT", "DIA_SEM_PT"], observed=True).size().reset_index(name="V")
    piv = h.pivot(index="DIA_SEM_PT", columns="MES_PT", values="V")
    piv = piv.reindex(index=[d for d in ORDEM_DIAS if d in piv.index],
                      columns=[m for m in ORDEM_MESES if m in piv.columns])
    fig_heat = go.Figure(go.Heatmap(
        z=piv.values, x=list(piv.columns), y=list(piv.index), colorscale=L.ESCALA_AZUL,
        hovertemplate="%{x} · %{y}<br>%{z:,} voos<extra></extra>"))
    fig_heat.update_layout(layout_base(), margin=dict(l=10, r=10, t=20, b=36))
    return fig_vol, fig_share, fig_rotas, fig_heat


# ──────────────────────────── ABA: PONTUALIDADE ───────────────────────────────

@app.callback(
    [Output("g-hist", "figure"), Output("g-hora", "figure"),
     Output("g-dia", "figure"), Output("g-canc", "figure")],
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value")])
def ab_pont(tab, anos, grupos, regioes, seg, pont):
    if tab != "tab-pont":
        return [no_update] * 4
    dff = filtrar(anos, grupos, regioes, seg, pont)
    if dff.empty:
        return [fig_vazia()] * 4

    # Histograma de atrasos de partida (1-120 min, bins de 3 min)
    atr = dff.loc[(dff["ATRASO_MIN"] > 0) & (dff["ATRASO_MIN"] <= 120), "ATRASO_MIN"]
    if len(atr):
        media = float(atr.mean())
        fig_hist = go.Figure(go.Histogram(
            x=atr, xbins=dict(start=0, end=120, size=3), marker_color=T.ACENTO,
            hovertemplate="%{x} min<br>%{y:,} voos<extra></extra>"))
        fig_hist.update_layout(layout_base(), showlegend=False, bargap=0.04,
                               xaxis_title="Minutos de atraso na partida", yaxis_title="Voos")
        fig_hist.add_vline(x=media, line_dash="dash", line_color=T.DESTAQUE,
                           annotation_text=f"média {media:.0f} min",
                           annotation_position="top")
    else:
        fig_hist = fig_vazia()

    # Atraso por hora: partida vs chegada (recuperação)
    h = (dff.dropna(subset=["HORA_PARTIDA"])
         .groupby("HORA_PARTIDA", observed=True)
         .agg(P=("ATRASO_MIN", "mean"), C=("ATRASO_CHEGADA_MIN", "mean")).reset_index())
    fig_hora = go.Figure()
    fig_hora.add_trace(go.Scatter(x=h["HORA_PARTIDA"], y=h["P"], name="Partida", mode="lines+markers",
                                  line=dict(color=T.DESTAQUE, width=3)))
    fig_hora.add_trace(go.Scatter(x=h["HORA_PARTIDA"], y=h["C"], name="Chegada", mode="lines+markers",
                                  line=dict(color=T.VERDE, width=3),
                                  fill="tonexty", fillcolor="rgba(31,163,124,0.10)"))
    fig_hora.update_layout(layout_base(), hovermode="x unified",
                           legend=dict(orientation="h", y=1.12, x=0),
                           xaxis_title="Hora da partida prevista", yaxis_title="Atraso médio (min)")

    # Taxa de atraso por dia da semana
    d = dff.groupby("DIA_SEM_PT", observed=True)["ATRASADO"].mean().reindex(ORDEM_DIAS) * 100
    fig_dia = go.Figure(go.Bar(
        x=ORDEM_DIAS, y=d.values, marker=dict(color=d.values, colorscale=L.ESCALA_CALOR),
        text=[f"{v:.1f}%".replace(".", ",") if pd.notna(v) else "" for v in d.values],
        textposition="outside"))
    fig_dia.update_layout(layout_base(), yaxis_title="% atrasados", showlegend=False)

    # Cancelamento por mês
    c = dff.groupby("MES_PT", observed=True)["CANCELADO"].mean().reindex(ORDEM_MESES) * 100
    fig_canc = go.Figure(go.Bar(
        x=ORDEM_MESES, y=c.values, marker=dict(color=c.values, colorscale=L.ESCALA_CALOR),
        text=[f"{v:.1f}%".replace(".", ",") if pd.notna(v) else "" for v in c.values],
        textposition="outside"))
    fig_canc.update_layout(layout_base(), yaxis_title="% cancelados", showlegend=False)
    return fig_hist, fig_hora, fig_dia, fig_canc


# ───────────────────────── ABA: FROTA & CAPACIDADE ────────────────────────────

@app.callback(
    [Output("g-fab", "figure"), Output("g-fam", "figure"),
     Output("g-assentos", "figure"), Output("g-cap", "figure")],
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value")])
def ab_frota(tab, anos, grupos, regioes, seg, pont):
    if tab != "tab-frota":
        return [no_update] * 4
    dff = filtrar(anos, grupos, regioes, seg, pont)
    if dff.empty:
        return [fig_vazia()] * 4

    # Fabricante (donut)
    fb = dff.groupby("FABRICANTE", observed=True).size().sort_values(ascending=False)
    fig_fab = go.Figure(go.Pie(
        labels=fb.index.tolist(), values=fb.values, hole=0.6, sort=False,
        marker=dict(colors=[CORES_FABRICANTE.get(k, "#9AA8B8") for k in fb.index],
                    line=dict(color="white", width=2)),
        textinfo="percent", textfont=dict(color="white", size=11)))
    fig_fab.update_layout(layout_base(), showlegend=True,
                          legend=dict(orientation="h", y=-0.08, x=0.5, xanchor="center"))

    # Famílias (barra)
    fm = (dff[dff["FAMILIA_AERONAVE"] != "Outros"]
          .groupby(["FAMILIA_AERONAVE", "FABRICANTE"], observed=True).size()
          .reset_index(name="V").nlargest(10, "V").sort_values("V"))
    fig_fam = go.Figure(go.Bar(
        x=fm["V"], y=fm["FAMILIA_AERONAVE"], orientation="h",
        marker_color=[CORES_FABRICANTE.get(f, "#9AA8B8") for f in fm["FABRICANTE"]],
        text=[fmt_compacto(v) for v in fm["V"]], textposition="outside", customdata=fm["FABRICANTE"],
        cliponaxis=False, hovertemplate="<b>%{y}</b> (%{customdata})<br>%{x:,} voos<extra></extra>"))
    fig_fam.update_layout(layout_base(), margin=dict(l=10, r=60, t=20, b=36))
    fig_fam.update_yaxes(automargin=True)
    L.folga_eixo(fig_fam, fm["V"].max())

    # Porte médio por grupo
    sg = (dff[dff["NUMERO_DE_ASSENTOS"] > 0].groupby("GRUPO", observed=True)["NUMERO_DE_ASSENTOS"]
          .mean().sort_values())
    fig_ass = go.Figure(go.Bar(
        x=sg.values, y=sg.index.tolist(), orientation="h",
        marker_color=[CORES_GRUPO.get(k, T.ACENTO) for k in sg.index],
        text=[f"{v:.0f}" for v in sg.values], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:.0f} assentos (média)<extra></extra>"))
    fig_ass.update_layout(layout_base(), xaxis_title="Assentos por voo (média)",
                          margin=dict(l=10, r=50, t=20, b=36))
    fig_ass.update_yaxes(automargin=True)
    L.folga_eixo(fig_ass, sg.max())

    # Capacidade ofertada (ASK) no tempo
    cap = dff.groupby("PERIODO", observed=True).agg(ASK=("ASK", "sum"),
                                                    ASSENTOS=("NUMERO_DE_ASSENTOS", "sum")).reset_index()
    fig_cap = go.Figure(go.Scatter(
        x=cap["PERIODO"], y=cap["ASK"], mode="lines", fill="tozeroy",
        line=dict(color=T.PRIMARIA_2, width=2.5), fillcolor="rgba(33,150,243,0.15)",
        hovertemplate="%{x}<br>%{y:,.0f} assentos-km<extra></extra>"))
    fig_cap.update_layout(layout_base(), yaxis_title="Assentos-km ofertados")
    fig_cap.update_xaxes(tickangle=45)
    return fig_fab, fig_fam, fig_ass, fig_cap


# ─────────────────────────── ABA: MALHA & GEOGRAFIA ───────────────────────────

@app.callback(
    [Output("g-mapa", "figure"), Output("g-fluxo", "figure"), Output("g-distatr", "figure")],
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value")])
def ab_malha(tab, anos, grupos, regioes, seg, pont):
    if tab != "tab-malha":
        return [no_update] * 3
    dff = filtrar(anos, grupos, regioes, seg, pont)
    if dff.empty:
        return [fig_vazia()] * 3

    fig_mapa = L.mapa_malha(dff, top_rotas=60, titulo="")

    # Fluxo regional
    sub = dff[dff["ORIG_REGIAO"].notna() & dff["DEST_REGIAO"].notna()]
    if sub.empty:
        fig_fluxo = fig_vazia("Sem voos domésticos no recorte")
    else:
        piv = (sub.groupby(["ORIG_REGIAO", "DEST_REGIAO"], observed=True).size()
               .reset_index(name="N").pivot(index="ORIG_REGIAO", columns="DEST_REGIAO", values="N"))
        ordem = [r for r in REGIOES if r in piv.index]
        cols = [r for r in REGIOES if r in piv.columns]
        piv = piv.reindex(index=ordem, columns=cols)
        fig_fluxo = go.Figure(go.Heatmap(
            z=piv.values, x=cols, y=ordem, colorscale=L.ESCALA_AZUL, showscale=False,
            text=[[fmt_compacto(v) if pd.notna(v) else "" for v in row] for row in piv.values],
            texttemplate="%{text}", textfont=dict(size=9),
            hovertemplate="%{y} → %{x}<br>%{z:,} voos<extra></extra>"))
        fig_fluxo.update_layout(layout_base(), margin=dict(l=10, r=10, t=18, b=30),
                                xaxis_title="Destino", yaxis_title="Origem")

    # Distância × recuperação em voo (por rota)
    base = dff.dropna(subset=["DIST_KM", "RECUPERACAO_MIN"])
    if base.empty:
        fig_da = fig_vazia()
    else:
        r = (base.groupby("ROTA_IATA", observed=True)
             .agg(DIST=("DIST_KM", "first"), REC=("RECUPERACAO_MIN", "mean"),
                  N=("ROTA_IATA", "size")).reset_index())
        r = r[r["N"] >= 30].nlargest(250, "N")
        fig_da = go.Figure(go.Scatter(
            x=r["DIST"], y=r["REC"], mode="markers",
            marker=dict(size=np.clip(r["N"] / r["N"].max() * 22, 5, 22),
                        color=r["REC"], colorscale="RdYlGn", cmid=0,
                        line=dict(width=0.5, color="white"), showscale=False),
            text=r["ROTA_IATA"],
            hovertemplate="<b>%{text}</b><br>%{x:,.0f} km<br>recupera %{y:.0f} min<extra></extra>"))
        fig_da.add_hline(y=0, line_dash="dot", line_color=T.TEXTO_SUAVE)
        fig_da.update_layout(layout_base(), margin=dict(l=10, r=10, t=18, b=30),
                             xaxis_title="Distância (km)", yaxis_title="Recuperação média (min)")
    return fig_mapa, fig_fluxo, fig_da


# ─────────────────────────────── ABA: TARIFAS ─────────────────────────────────

@app.callback(
    [Output("g-tar-emp", "figure"), Output("g-tar-tempo", "figure"),
     Output("g-tar-dist", "figure"), Output("g-tar-rotas", "figure")],
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value")])
def ab_tarifas(tab, anos, grupos, regioes):
    if tab != "tab-tarifas":
        return [no_update] * 4
    if tarifas.empty:
        return [fig_vazia("Arquivo de tarifas não disponível")] * 4
    tf = filtrar_tarifas(anos, grupos, regioes)
    if tf.empty:
        return [fig_vazia()] * 4

    # Tarifa média por companhia
    e = tf.groupby("EMPRESA_NOME", observed=True)["TARIFA_MEDIA"].mean().sort_values()
    fig_emp = go.Figure(go.Bar(
        x=e.values, y=e.index.tolist(), orientation="h",
        marker=dict(color=e.values, colorscale=L.ESCALA_AZUL),
        text=[fmt_reais(v) for v in e.values], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>R$ %{x:.2f}<extra></extra>"))
    fig_emp.update_layout(layout_base(), xaxis_title="Tarifa média (R$)",
                          margin=dict(l=10, r=75, t=20, b=36))
    fig_emp.update_yaxes(automargin=True)
    L.folga_eixo(fig_emp, e.max())

    # Evolução temporal da tarifa média
    tf2 = tf.copy()
    tf2["PERIODO"] = (tf2["ANO"].astype(int).astype(str) + "-" +
                      tf2["MES"].astype(int).astype(str).str.zfill(2))
    tt = tf2.groupby("PERIODO")["TARIFA_MEDIA"].mean().reset_index().sort_values("PERIODO")
    fig_tempo = go.Figure(go.Scatter(
        x=tt["PERIODO"], y=tt["TARIFA_MEDIA"], mode="lines+markers",
        line=dict(color=T.DESTAQUE, width=3), fill="tozeroy", fillcolor="rgba(232,86,58,0.10)",
        hovertemplate="%{x}<br>R$ %{y:.2f}<extra></extra>"))
    fig_tempo.update_layout(layout_base(), yaxis_title="Tarifa média (R$)")
    fig_tempo.update_xaxes(tickangle=45)

    # Tarifa × distância (bolha = volume)
    rt = (tf.dropna(subset=["DIST_KM"]).groupby("ROTA_IATA", observed=True)
          .agg(TAR=("TARIFA_MEDIA", "mean"), DIST=("DIST_KM", "first"),
               PAX=("PASS_PAGOS", "sum")).reset_index())
    rt = rt[rt["DIST"] > 0]
    if rt.empty:
        fig_dist = fig_vazia()
    else:
        fig_dist = go.Figure(go.Scatter(
            x=rt["DIST"], y=rt["TAR"], mode="markers", text=rt["ROTA_IATA"], showlegend=False,
            marker=dict(size=np.clip(np.sqrt(rt["PAX"].fillna(1)) / 4, 5, 26),
                        color=rt["TAR"], colorscale=L.ESCALA_AZUL, opacity=0.7,
                        line=dict(width=0.5, color="white")),
            hovertemplate="<b>%{text}</b><br>%{x:,.0f} km · R$ %{y:.0f}<extra></extra>"))
        # linha de tendência
        m, b = np.polyfit(rt["DIST"], rt["TAR"], 1)
        xs = np.array([rt["DIST"].min(), rt["DIST"].max()])
        fig_dist.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines",
                                      line=dict(color=T.DESTAQUE, dash="dash", width=2),
                                      name="tendência", showlegend=False))
        fig_dist.update_layout(layout_base(), showlegend=False, xaxis_title="Distância (km)",
                               yaxis_title="Tarifa média (R$)")

    # Rotas mais caras e mais baratas (cores determinísticas por tipo)
    cont = tf.groupby("ROTA_IATA", observed=True).size()
    rr = tf.groupby("ROTA_IATA", observed=True)["TARIFA_MEDIA"].mean()[cont >= 3]
    if len(rr) >= 12:
        baratas = rr.nsmallest(6).rename("TAR").reset_index().assign(tipo="barata")
        caras = rr.nlargest(6).rename("TAR").reset_index().assign(tipo="cara")
        dfp = (pd.concat([baratas, caras]).drop_duplicates("ROTA_IATA")
               .sort_values("TAR"))
        cores = [T.VERDE if t == "barata" else T.DESTAQUE for t in dfp["tipo"]]
        fig_rotas = go.Figure(go.Bar(
            x=dfp["TAR"], y=dfp["ROTA_IATA"], orientation="h", marker_color=cores,
            text=[fmt_reais(v) for v in dfp["TAR"]], textposition="outside", cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>R$ %{x:.0f}<extra></extra>"))
        fig_rotas.update_layout(layout_base(), xaxis_title="Tarifa média (R$)",
                                margin=dict(l=10, r=75, t=20, b=36))
        fig_rotas.update_yaxes(automargin=True)
        L.folga_eixo(fig_rotas, dfp["TAR"].max())
    else:
        fig_rotas = fig_vazia()
    return fig_emp, fig_tempo, fig_dist, fig_rotas


# ──────────────────────── ABA: CURIOSIDADES & CORRELAÇÕES ─────────────────────

def _cur_card(icone, valor, titulo, desc, cor):
    return html.Div(dbc.Card(dbc.CardBody([
        html.Div([html.Span(icone, className="cur-ic"),
                  html.Span(valor, className="cur-val", style={"color": cor})], className="cur-top"),
        html.Div(titulo, className="cur-tit"),
        html.Div(desc, className="cur-desc"),
    ]), className="cur-card"), className="cur-wrap")


def curiosidades_cards(dff, tf):
    """Gera cartões 'você sabia?' calculados a partir do recorte."""
    cards = []

    # 1) Efeito cascata: noite vs manhã
    h = (dff.dropna(subset=["HORA_PARTIDA"]).assign(H=dff["HORA_PARTIDA"].astype("Int64"))
         .groupby("H")["ATRASADO"].agg(["mean", "size"]))
    h = h[h["size"] >= 200]
    if len(h) >= 4:
        manha = h.loc[h.index.isin([6, 7, 8, 9]), "mean"].mean()
        noite = h.loc[h.index.isin([19, 20, 21, 22]), "mean"].mean()
        if manha and manha > 0:
            cards.append(_cur_card("🌅", f"{noite/manha:.1f}×".replace(".", ","), "Efeito cascata",
                                   f"voos da noite atrasam {noite/manha:.1f}× mais que os da manhã "
                                   f"({manha*100:.0f}% → {noite*100:.0f}%)".replace(".", ","), T.DESTAQUE))

    # 2) Recuperação no ar
    if "ATRASO_CHEGADA_MIN" in dff.columns:
        late = dff["ATRASO_MIN"] > 15
        if late.sum() > 0:
            salvos = (late & (dff["ATRASO_CHEGADA_MIN"] <= 15)).sum() / late.sum() * 100
            cards.append(_cur_card("🛬", f"{salvos:.0f}%", "Salvos no ar",
                                   "dos que partem atrasados ainda chegam no horário — "
                                   "tempo recuperado em voo", T.VERDE))

    # 3) Aeroporto mais pontual (só aeroportos conhecidos, p/ rótulo limpo)
    mov = pd.concat([dff["ORIGEM_IATA"], dff["DESTINO_IATA"]]).value_counts()
    grandes = [a for a in mov[mov >= 8000].index if a in L.IATA_CIDADE]
    if grandes:
        ap = (dff[dff["ORIGEM_IATA"].isin(grandes)].groupby("ORIGEM_IATA", observed=True)["ATRASADO"]
              .mean() * 100).dropna()
        ap = ap[ap.index.isin(grandes)]
        if len(ap):
            best = ap.idxmin()
            cards.append(_cur_card("🏅", f"{ap.min():.0f}%".replace(".", ","),
                                   f"{L.IATA_CIDADE.get(best, best)} ({best})",
                                   "o aeroporto movimentado mais pontual do recorte", T.VERDE))

    # 4) Boeing × Embraer
    fab = (dff.groupby("FABRICANTE", observed=True)["ATRASADO"].mean() * 100)
    if {"Boeing", "Embraer"}.issubset(fab.dropna().index):
        b, e = fab["Boeing"], fab["Embraer"]
        if e > 0:
            cards.append(_cur_card("✈", f"+{(b/e-1)*100:.0f}%", "Boeing × Embraer",
                                   f"jatos Boeing atrasam {(b/e-1)*100:.0f}% mais que os Embraer "
                                   f"({e:.0f}% vs {b:.0f}%)".replace(".", ","), T.AMBAR))

    # 5) Voos curtos
    d = dff["DIST_KM"].dropna()
    d = d[d > 0]
    if len(d):
        curtos = (d < 500).mean() * 100
        cards.append(_cur_card("📏", f"{curtos:.0f}%", "Saltos curtos",
                               f"dos voos cobrem menos de 500 km (mediana {d.median():.0f} km)",
                               T.ACENTO))

    # 6) Pior dia da semana
    dsem = (dff.groupby("DIA_SEM_PT", observed=True)["ATRASADO"].mean()).dropna()
    if len(dsem):
        pior = dsem.idxmax()
        cards.append(_cur_card("📆", str(pior), "Pior dia p/ voar",
                               f"{pior} tem a maior taxa de atrasos ({dsem.max()*100:.0f}%) — "
                               f"contra {dsem.idxmin()} ({dsem.min()*100:.0f}%)".replace(".", ","),
                               T.DESTAQUE))

    # 7) Quando atrasa, atrasa muito (grupo com maior atraso médio)
    am = (dff[dff["ATRASADO"]].groupby("GRUPO", observed=True)["ATRASO_MIN"].mean()).dropna()
    if len(am):
        g = am.idxmax()
        cards.append(_cur_card("⏳", f"{am.max():.0f} min", "Quando atrasa, atrasa",
                               f"grupo {g} acumula o maior atraso médio quando se atrasa", T.ROXO))

    # 8) R$/km despenca (tarifas)
    if tf is not None and not tf.empty and "TARIFA_POR_KM" in tf.columns:
        t2 = tf.dropna(subset=["DIST_KM", "TARIFA_POR_KM"])
        t2 = t2[t2["DIST_KM"] > 0]
        if len(t2) > 50:
            curto = t2[t2["DIST_KM"] < 500]["TARIFA_POR_KM"].mean()
            longo = t2[t2["DIST_KM"] >= 1500]["TARIFA_POR_KM"].mean()
            if longo and longo > 0:
                cards.append(_cur_card("💸", f"{curto/longo:.0f}×", "Curto sai caro",
                                       f"o km custa {curto/longo:.0f}× mais num voo curto que num longo "
                                       "— a tarifa quase não muda com a distância", T.PRIMARIA_2))

    # 9) Super-hub
    if len(mov):
        topa = mov.index[0]
        cards.append(_cur_card("🛫", f"{mov.iloc[0]/mov.sum()*100:.0f}%",
                               f"{L.IATA_CIDADE.get(topa, topa)} ({topa})",
                               "concentra essa fatia de todos os movimentos do recorte", T.CIANO))

    return cards


def _fig_relacoes(dff):
    """'O que tem a ver com o quê?' — relações em linguagem clara (sem jargão)."""
    base = dff.assign(ATRASOU=dff["ATRASADO"].astype(int))

    def c(x, y):
        try:
            return float(base[[x, y]].corr().iloc[0, 1])
        except Exception:
            return np.nan

    rels = [
        ("Saiu atrasado  ↔  Chegou atrasado", c("ATRASO_MIN", "ATRASO_CHEGADA_MIN")),
        ("Avião maior  ↔  Rota mais longa", c("NUMERO_DE_ASSENTOS", "DIST_KM")),
        ("Avião maior  ↔  Recupera no ar", c("NUMERO_DE_ASSENTOS", "RECUPERACAO_MIN")),
        ("Rota mais longa  ↔  Recupera no ar", c("DIST_KM", "RECUPERACAO_MIN")),
        ("Distância da rota  ↔  Atrasar", c("DIST_KM", "ATRASOU")),
    ]
    rels = [(n, v) for n, v in rels if pd.notna(v)]
    if not rels:
        return fig_vazia()
    rels.sort(key=lambda t: abs(t[1]))  # mais forte no topo da barra horizontal

    def classificar(v):
        a = abs(v)
        if a >= 0.8:  return "quase perfeita", "#0A2342"
        if a >= 0.5:  return "forte", "#1565C0"
        if a >= 0.3:  return "moderada", "#2196F3"
        if a >= 0.15: return "fraca", "#00ACC1"
        if a >= 0.05: return "muito fraca", "#F2A900"
        return "quase nenhuma", "#AEB6C2"

    nomes = [n for n, _ in rels]
    vals = [abs(v) for _, v in rels]
    palavras = [classificar(v)[0] for _, v in rels]
    cores = [classificar(v)[1] for _, v in rels]
    fig = go.Figure(go.Bar(
        x=vals, y=nomes, orientation="h", marker_color=cores,
        text=[f"<b>{p}</b>  ({v:+.2f})".replace(".", ",") for (_, v), p in zip(rels, palavras)],
        textposition="outside", cliponaxis=False, customdata=[v for _, v in rels],
        hovertemplate="<b>%{y}</b><br>correlação: %{customdata:+.2f}<extra></extra>"))
    fig.add_vline(x=0.3, line_dash="dot", line_color="#CBD5E1")
    fig.add_vline(x=0.6, line_dash="dot", line_color="#CBD5E1")
    fig.update_layout(
        layout_base(), margin=dict(l=10, r=130, t=40, b=0),
        xaxis_title="força da relação   →   0 = sem relação    ·    1 = andam sempre juntas")
    fig.update_xaxes(range=[0, 1.2], showticklabels=False)
    fig.update_yaxes(automargin=True)
    return fig


def _fig_fab(dff):
    """Pontualidade por fabricante (curiosidade Boeing × Embraer)."""
    g = (dff.groupby("FABRICANTE", observed=True)["ATRASADO"].agg(["mean", "size"]).reset_index())
    g = g[(g["size"] >= 2000) & (g["FABRICANTE"] != "Outros")]
    if g.empty:
        return fig_vazia()
    g["PCT"] = (g["mean"] * 100).round(1)
    g = g.sort_values("PCT")
    fig = go.Figure(go.Bar(
        x=g["PCT"], y=g["FABRICANTE"], orientation="h",
        marker_color=[CORES_FABRICANTE.get(f, "#9AA8B8") for f in g["FABRICANTE"]],
        text=[f"{v:.1f}%".replace(".", ",") for v in g["PCT"]], textposition="outside",
        cliponaxis=False, customdata=g["size"],
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% atrasos · %{customdata:,} voos<extra></extra>"))
    fig.update_layout(layout_base(), xaxis_title="% de voos atrasados",
                      margin=dict(l=10, r=55, t=18, b=34))
    fig.update_yaxes(automargin=True)
    L.folga_eixo(fig, g["PCT"].max())
    return fig


def _fig_rkm(tf):
    """Preço por km por faixa de distância (economia de escala)."""
    if tf is None or tf.empty or "TARIFA_POR_KM" not in tf.columns:
        return fig_vazia("Tarifas indisponíveis")
    t2 = tf.dropna(subset=["DIST_KM", "TARIFA_POR_KM", "TARIFA_MEDIA"])
    t2 = t2[t2["DIST_KM"] > 0]
    if len(t2) < 30:
        return fig_vazia()
    t2 = t2.assign(FX=pd.cut(t2["DIST_KM"], [0, 500, 1000, 1500, 2500, 6000],
                             labels=["<500", "500–1000", "1000–1500", "1500–2500", "2500+"]))
    g = t2.groupby("FX", observed=True).agg(RKM=("TARIFA_POR_KM", "mean"),
                                            TAR=("TARIFA_MEDIA", "mean")).reset_index()
    fig = go.Figure(go.Bar(
        x=g["FX"].astype(str), y=g["RKM"], marker=dict(color=g["RKM"], colorscale=L.ESCALA_CALOR),
        text=[fmt_reais(v, 2) for v in g["RKM"]], textposition="outside", cliponaxis=False,
        customdata=g["TAR"],
        hovertemplate="%{x} km<br>R$ %{y:.2f}/km · tarifa média R$ %{customdata:.0f}<extra></extra>"))
    fig.update_layout(layout_base(), yaxis_title="R$ por km", xaxis_title="Distância da rota (km)",
                      margin=dict(l=10, r=10, t=30, b=34))
    L.folga_eixo(fig, g["RKM"].max(), eixo="y")
    return fig


def _fig_cresc(dff):
    """Rotas que mais cresceram/encolheram entre o 1º e o último ano do recorte."""
    anos = sorted(int(a) for a in dff["ANO"].dropna().unique())
    if len(anos) < 2:
        return fig_vazia("Selecione ≥ 2 anos para comparar")
    # evita usar o ano parcial como referência final (distorce o crescimento)
    completos = [a for a in anos if a != L.ANO_PARCIAL]
    a1 = completos[-1] if completos else anos[-1]
    a0 = anos[0]
    if a0 >= a1:
        a0, a1 = anos[0], anos[-1]
    r0 = dff[dff["ANO"] == a0].groupby("ROTA_IATA", observed=True).size()
    r1 = dff[dff["ANO"] == a1].groupby("ROTA_IATA", observed=True).size()
    g = pd.DataFrame({"v0": r0, "v1": r1}).fillna(0)
    g = g[g["v0"] >= 400]
    if g.empty:
        return fig_vazia()
    g["var"] = (g["v1"] / g["v0"] - 1) * 100
    top = pd.concat([g.nlargest(6, "var"), g.nsmallest(6, "var")]).drop_duplicates().sort_values("var")
    cores = [T.DESTAQUE if v < 0 else T.VERDE for v in top["var"]]
    fig = go.Figure(go.Bar(
        x=top["var"], y=top.index.tolist(), orientation="h", marker_color=cores,
        text=[f"{v:+.0f}%" for v in top["var"]],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="white", size=11),
        hovertemplate="<b>%{y}</b><br>%{x:+.0f}% de voos<extra></extra>"))
    fig.add_vline(x=0, line_color="#CBD5E1", line_width=1)
    fig.update_layout(layout_base(), xaxis_title=f"variação de voos {a0} → {a1} (%)",
                      margin=dict(l=10, r=18, t=18, b=34),
                      uniformtext=dict(mode="show", minsize=9))
    fig.update_yaxes(automargin=True)
    vmin, vmax = top["var"].min(), top["var"].max()
    pad = max(25, (vmax - vmin) * 0.05)
    fig.update_xaxes(range=[vmin - pad, vmax + pad])
    return fig


@app.callback(
    [Output("cur-cards", "children"), Output("cur-heat", "figure"), Output("cur-fab", "figure"),
     Output("cur-rkm", "figure"), Output("cur-cresc", "figure")],
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value")])
def ab_curiosidades(tab, anos, grupos, regioes, seg, pont):
    if tab != "tab-cur":
        return [no_update] * 5
    dff = filtrar(anos, grupos, regioes, seg, pont)
    if dff.empty:
        return [html.Div("Sem dados para o recorte.", className="cur-vazio")], \
            fig_vazia(), fig_vazia(), fig_vazia(), fig_vazia()
    tf = filtrar_tarifas(anos, grupos, regioes)
    return (curiosidades_cards(dff, tf), _fig_relacoes(dff), _fig_fab(dff),
            _fig_rkm(tf), _fig_cresc(dff))


# ───────────────────────────── ABA: COMPARATIVO ───────────────────────────────

@app.callback(
    Output("g-comp", "figure"),
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value"),
     Input("c-x", "value"), Input("c-m", "value"), Input("c-c", "value")])
def ab_comp(tab, anos, grupos, regioes, seg, pont, x, metrica, cor):
    if tab != "tab-comp":
        return no_update
    dff = filtrar(anos, grupos, regioes, seg, pont)
    if dff.empty or x not in dff.columns:
        return fig_vazia()

    cor_col = None if cor == "none" or cor not in dff.columns else cor
    cols = [x] + ([cor_col] if cor_col else [])

    # coluna auxiliar p/ atraso médio (apenas voos atrasados)
    aux = dff
    if metrica == "med_atraso":
        aux = dff.assign(_AP=dff["ATRASO_MIN"].where(dff["ATRASADO"]))

    gb = aux.groupby(cols, observed=True)
    if metrica == "n_voos":
        s = gb.size()
    elif metrica == "pct_atraso":
        s = gb["ATRASADO"].mean() * 100
    elif metrica == "pct_canc":
        s = gb["CANCELADO"].mean() * 100
    elif metrica == "med_atraso":
        s = gb["_AP"].mean()
    elif metrica == "assentos":
        s = gb["NUMERO_DE_ASSENTOS"].mean()
    elif metrica == "dist":
        s = gb["DIST_KM"].mean()
    else:
        s = gb.size()
    g = s.reset_index(name="VAL").dropna(subset=["VAL"])
    if g.empty:
        return fig_vazia()

    labels = {"n_voos": "Nº de voos", "pct_atraso": "Taxa de atraso (%)",
              "pct_canc": "Taxa de cancelamento (%)", "med_atraso": "Atraso médio (min)",
              "assentos": "Porte médio (assentos)", "dist": "Distância média (km)"}
    if str(x) in ("ANO", "TRIMESTRE"):
        g[x] = g[x].astype("Int64").astype(str)

    if cor_col:
        fig = px.bar(g, x=x, y="VAL", color=cor_col, barmode="group",
                     color_discrete_map={**CORES_GRUPO, **CORES_FABRICANTE},
                     color_discrete_sequence=L.SEQ_CORES, labels={"VAL": labels[metrica]})
    else:
        g = g.sort_values("VAL", ascending=False)
        fig = px.bar(g, x=x, y="VAL", color="VAL", color_continuous_scale=L.ESCALA_AZUL,
                     labels={"VAL": labels[metrica]})
        fig.update_coloraxes(showscale=False)
    fig.update_layout(layout_base(440), xaxis_title="", yaxis_title=labels[metrica])
    return fig


# ─────────────────────────────── ABA: TABELA ──────────────────────────────────

@app.callback(
    Output("tb-cont", "children"),
    [Input("tabs", "active_tab"), Input("f-anos", "value"), Input("f-grupos", "value"),
     Input("f-regioes", "value"), Input("f-seg", "value"), Input("f-pont", "value"),
     Input("tb-cols", "value")])
def ab_tabela(tab, anos, grupos, regioes, seg, pont, cols):
    if tab != "tab-tabela":
        return no_update
    dff = filtrar(anos, grupos, regioes, seg, pont)
    cols = [c for c in (cols or []) if c in dff.columns] or list(df.columns[:8])
    amostra = dff[cols].head(500)
    return dash_table.DataTable(
        data=amostra.to_dict("records"),
        columns=[{"name": c, "id": c} for c in cols],
        page_size=15, sort_action="native", filter_action="native",
        style_table={"overflowX": "auto", "borderRadius": "10px", "overflow": "hidden"},
        style_header={"backgroundColor": T.PRIMARIA, "color": "white", "fontWeight": "700",
                      "fontSize": "12px", "border": "none", "textTransform": "uppercase"},
        style_cell={"fontSize": "12.5px", "padding": "9px 12px", "border": "1px solid #EEF2F7",
                    "textAlign": "left", "maxWidth": "230px", "overflow": "hidden",
                    "textOverflow": "ellipsis", "fontFamily": "Inter, sans-serif"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#F6F9FC"}],
    )


@app.callback(
    Output("tb-download", "data"),
    Input("tb-btn", "n_clicks"),
    [State("f-anos", "value"), State("f-grupos", "value"), State("f-regioes", "value"),
     State("f-seg", "value"), State("f-pont", "value"), State("tb-cols", "value")],
    prevent_initial_call=True)
def baixar(n, anos, grupos, regioes, seg, pont, cols):
    dff = filtrar(anos, grupos, regioes, seg, pont)
    cols = [c for c in (cols or []) if c in dff.columns] or list(df.columns[:10])
    return dcc.send_data_frame(dff[cols].head(50_000).to_csv,
                               "voos_filtrado.csv", index=False, encoding="utf-8-sig")


# ───────────────────────────────── ESTILO ─────────────────────────────────────

app.index_string = """
<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box;}
  body{font-family:'Inter','Segoe UI',sans-serif;margin:0;background:#EEF2F7;color:#1A2332;}
  .wrap{display:flex;min-height:100vh;}

  /* SIDEBAR */
  .sidebar{width:248px;min-width:248px;background:linear-gradient(180deg,#0A2342 0%,#0E2C53 100%);
    color:#fff;padding:18px 16px;position:sticky;top:0;height:100vh;overflow-y:auto;
    box-shadow:5px 0 22px rgba(10,35,66,.22);}
  .sb-brand{display:flex;align-items:center;gap:11px;margin-bottom:14px;}
  .sb-logo{font-size:1.7rem;background:rgba(255,255,255,.12);width:42px;height:42px;border-radius:11px;
    display:flex;align-items:center;justify-content:center;}
  .sb-t1{font-weight:800;font-size:1rem;line-height:1.1;}
  .sb-t2{font-size:.7rem;opacity:.7;}
  .sb-section{font-size:.64rem;text-transform:uppercase;letter-spacing:.1em;color:#7FB0E6;
    font-weight:700;margin:14px 0 8px;border-top:1px solid rgba(255,255,255,.1);padding-top:12px;}
  .flbl{font-size:.72rem;font-weight:700;color:#BFD6F0;display:block;margin:12px 0 5px;}
  .chk label{font-size:.8rem;color:rgba(255,255,255,.88);cursor:pointer;}
  .chk input{accent-color:#2196F3;margin-right:3px;}
  .sb-stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px;}
  .stt{background:rgba(255,255,255,.07);border-radius:10px;padding:9px;text-align:center;}
  .stt-v{font-size:1.05rem;font-weight:800;color:#fff;}
  .stt-l{font-size:.62rem;color:#9FC0E6;text-transform:uppercase;letter-spacing:.04em;}

  /* CONTEÚDO */
  .conteudo{flex:1;padding:18px 22px;overflow-y:auto;max-width:calc(100vw - 248px);}
  .aba-body{padding-top:16px;}
  [class*="col"]{padding-left:8px;padding-right:8px;}

  .painel{border:none!important;border-radius:14px!important;background:#fff!important;
    box-shadow:0 2px 11px rgba(10,35,66,.07)!important;overflow:hidden;}
  .pn-head{background:linear-gradient(90deg,#0A2342 0%,#1565C0 100%)!important;color:#fff;
    border:none!important;padding:9px 15px!important;display:flex;align-items:baseline;gap:9px;}
  .pn-tit{font-weight:700;font-size:.86rem;}
  .pn-sub{font-size:.68rem;opacity:.72;font-weight:400;}
  .painel .card-body{padding:8px 10px;}
  .ctrl-card .card-body{padding:14px 16px;}
  .flbl-c{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
    color:#5B6B7F;display:block;margin-bottom:5px;}

  .btn-dl{width:100%;background:#1FA37C;color:#fff;border:none;border-radius:9px;padding:8px 12px;
    font-weight:700;font-size:.84rem;cursor:pointer;transition:filter .15s;}
  .btn-dl:hover{filter:brightness(1.08);}
  .tb-nota{font-size:.72rem;color:#9AA8B8;margin-top:9px;}

  /* CURIOSIDADES */
  .cur-intro{background:#E8F1FB;border-left:4px solid #2196F3;border-radius:10px;
    padding:11px 16px;font-size:.86rem;color:#334; margin:2px 0 14px;line-height:1.45;}
  .cur-grid{display:flex;flex-wrap:wrap;gap:12px;margin:4px 0 16px;}
  .cur-wrap{flex:1 1 230px;min-width:215px;}
  .cur-card{border:none!important;border-radius:14px!important;background:#fff!important;height:100%;
    box-shadow:0 2px 10px rgba(10,35,66,.07)!important;transition:transform .18s,box-shadow .18s;
    border-left:4px solid #2196F3!important;}
  .cur-card:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(10,35,66,.13)!important;}
  .cur-card .card-body{padding:13px 15px;}
  .cur-top{display:flex;align-items:center;gap:9px;}
  .cur-ic{font-size:1.4rem;}
  .cur-val{font-size:1.5rem;font-weight:800;line-height:1;}
  .cur-tit{font-size:.78rem;font-weight:700;color:#0A2342;margin-top:7px;text-transform:uppercase;
    letter-spacing:.02em;}
  .cur-desc{font-size:.76rem;color:#5B6B7F;margin-top:3px;line-height:1.42;}
  .cur-vazio{padding:30px;color:#9AA8B8;}

  /* TABS */
  .nav-tabs{border-bottom:2px solid #DCE6F0;gap:2px;}
  .nav-tabs .nav-link{font-size:.85rem;font-weight:600;color:#5B6B7F;border:none;
    border-radius:9px 9px 0 0;padding:9px 15px;}
  .nav-tabs .nav-link:hover{background:#E3ECF6;color:#0A2342;}
  .nav-tabs .nav-link.active{color:#0A2342;background:#fff;border-bottom:3px solid #2196F3;
    box-shadow:0 -2px 8px rgba(10,35,66,.05);}

  ::-webkit-scrollbar{width:8px;height:8px;}
  ::-webkit-scrollbar-track{background:transparent;}
  ::-webkit-scrollbar-thumb{background:#C2D0E0;border-radius:4px;}
  .sidebar::-webkit-scrollbar-thumb{background:rgba(255,255,255,.2);}
</style></head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
"""

if __name__ == "__main__":
    print("\n  ✈  Exploração Interativa  →  http://localhost:8051\n")
    app.run(debug=False, port=8051)
