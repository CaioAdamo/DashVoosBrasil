"""
Dashboard 1 — Painel Executivo da Aviação Civil Brasileira
===========================================================
Visão estratégica de alto nível sobre ~3 milhões de voos (ANAC, 2022–2025):
malha aérea geográfica, concentração de mercado, frota, sazonalidade,
pontualidade e fluxo regional — com KPIs comparativos (variação ano a ano)
e insights calculados dinamicamente a partir do recorte selecionado.

    python dashboard_visao_geral.py     →     http://localhost:8050
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

import lib_dados as L
from lib_dados import (T, fmt, fmt_compacto, layout_base, fig_vazia,
                       CORES_GRUPO, CORES_FABRICANTE, CORES_REGIAO,
                       ORDEM_MESES, MESES_PT, taxa_pct, hhi)

# ───────────────────────────────── DADOS ──────────────────────────────────────
df = L.carregar()
ANOS = sorted(df["ANO"].dropna().unique().astype(int))
REGIOES_ORD = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Aviação Brasil · Painel Executivo",
    suppress_callback_exceptions=True,
)
server = app.server


# ───────────────────────────────── KPIs ───────────────────────────────────────

def _metricas(dff: pd.DataFrame) -> dict:
    """Calcula o bloco de indicadores-chave para um recorte."""
    n = len(dff)
    dias = dff["PARTIDA_PREV"].dt.normalize().nunique() if n else 0
    return {
        "voos": n,
        "voos_dia": (n / dias) if dias else 0,
        "empresas": dff["EMPRESA"].nunique(),
        "aeroportos": pd.unique(dff[["ORIGEM", "DESTINO"]].values.ravel()).size if n else 0,
        "rotas": dff["ROTA"].nunique(),
        "pontualidade": 100 - taxa_pct(dff["ATRASADO"]),
        "cancel": taxa_pct(dff["CANCELADO"]),
        "assentos": dff["NUMERO_DE_ASSENTOS"].sum(),
        "atraso_med": dff.loc[dff["ATRASADO"], "ATRASO_MIN"].mean(),
    }


def _delta(atual, anterior):
    """Retorna (texto, cor) da variação percentual entre dois valores."""
    if anterior in (None, 0) or pd.isna(anterior) or pd.isna(atual):
        return None, None
    var = (atual - anterior) / anterior * 100
    seta = "▲" if var >= 0 else "▼"
    return f"{seta} {abs(var):.1f}%".replace(".", ","), (T.VERDE if var >= 0 else T.DESTAQUE)


def kpi_card(titulo, valor, sub, cor, icone, delta=None, delta_cor=None, delta_label=""):
    corpo = [
        html.Div([html.Span(icone, className="kpi-ic"),
                  html.Span(delta, className="kpi-delta", style={"color": delta_cor})
                  if delta else None], className="kpi-top"),
        html.Div(valor, className="kpi-val", style={"color": cor}),
        html.Div(titulo, className="kpi-tit"),
        html.Div(sub if not delta else f"{delta_label}", className="kpi-sub"),
    ]
    return html.Div(dbc.Card(dbc.CardBody(corpo), className="kpi-card"), className="kpi-wrap")


def montar_kpis(dff, dff_prev=None, label_prev=""):
    m = _metricas(dff)
    p = _metricas(dff_prev) if dff_prev is not None and len(dff_prev) else None

    def d(chave):
        return _delta(m[chave], p[chave]) if p else (None, None)

    dv, cv = d("voos"); dd, cd = d("voos_dia"); ds, cs = d("assentos")
    # pontualidade: variação em pontos percentuais (mais clara que %)
    if p:
        dp_val = m["pontualidade"] - p["pontualidade"]
        dpont = f"{'▲' if dp_val>=0 else '▼'} {abs(dp_val):.1f} p.p.".replace(".", ",")
        cpont = T.VERDE if dp_val >= 0 else T.DESTAQUE
    else:
        dpont, cpont = None, None

    cards = [
        kpi_card("Voos operados", fmt_compacto(m["voos"]), "no período", T.ACENTO, "✈",
                 dv, cv, label_prev),
        kpi_card("Voos por dia", fmt(m["voos_dia"]), "média diária", T.PRIMARIA_2, "📅",
                 dd, cd, label_prev),
        kpi_card("Companhias", fmt(m["empresas"]), "em operação", T.ROXO, "🏢"),
        kpi_card("Aeroportos", fmt(m["aeroportos"]), "atendidos", T.CIANO, "🛫"),
        kpi_card("Pontualidade", f"{fmt(m['pontualidade'],1)}%", "saídas ≤15 min", T.VERDE, "🎯",
                 dpont, cpont, label_prev),
        kpi_card("Cancelamentos", f"{fmt(m['cancel'],1)}%", "do total", T.DESTAQUE, "✖"),
        kpi_card("Assentos ofertados", fmt_compacto(m["assentos"]), "capacidade", T.AMBAR, "💺",
                 ds, cs, label_prev),
        kpi_card("Atraso médio", f"{fmt(m['atraso_med'])} min", "quando atrasa", "#C2410C", "⏱"),
    ]
    return html.Div(cards, className="kpi-row")


# ─────────────────────────────── GRÁFICOS ─────────────────────────────────────

def fig_share_grupo(dff):
    """Donut de participação por grupo econômico + concentração no centro."""
    if dff.empty:
        return fig_vazia()
    g = dff.groupby("GRUPO", observed=True).size().sort_values(ascending=False)
    cores = [CORES_GRUPO.get(k, T.ACENTO) for k in g.index]
    indice = hhi(g)
    top3 = g.head(3).sum() / g.sum() * 100 if g.sum() else 0
    nivel = "alta" if indice > 2500 else ("moderada" if indice > 1500 else "baixa")
    fig = go.Figure(go.Pie(
        labels=g.index.tolist(), values=g.values, hole=0.66, sort=False,
        marker=dict(colors=cores, line=dict(color="white", width=2)),
        textinfo="percent", textfont=dict(size=12, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value:,} voos · %{percent}<extra></extra>"))
    fig.update_layout(
        layout_base(), title="Participação por grupo econômico",
        showlegend=True,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", font=dict(size=10.5)),
        annotations=[
            dict(text=f"<b>Top-3</b><br>{top3:.0f}%", x=0.5, y=0.54,
                 showarrow=False, font=dict(size=16, color=T.PRIMARIA)),
            dict(text=f"HHI {indice:,.0f}<br>conc. {nivel}", x=0.5, y=0.40,
                 showarrow=False, font=dict(size=10, color=T.TEXTO_SUAVE)),
        ])
    return fig


def fig_evolucao(dff):
    """Volume mensal sobreposto por ano (compara sazonalidade entre anos)."""
    if dff.empty:
        return fig_vazia()
    g = dff.groupby(["ANO", "MES"], observed=True).size().reset_index(name="VOOS")
    g["MES_PT"] = pd.Categorical(g["MES"].map(MESES_PT), categories=ORDEM_MESES, ordered=True)
    g = g.sort_values(["ANO", "MES"])
    fig = go.Figure()
    paleta = {2022: "#9AB8D8", 2023: T.ACENTO, 2024: T.PRIMARIA, 2025: T.DESTAQUE}
    for ano, sub in g.groupby("ANO"):
        parcial = ano == L.ANO_PARCIAL
        fig.add_trace(go.Scatter(
            x=sub["MES_PT"], y=sub["VOOS"], mode="lines+markers",
            name=f"{int(ano)}{' (parcial)' if parcial else ''}",
            line=dict(width=3, color=paleta.get(int(ano), T.VERDE),
                      dash="dot" if parcial else "solid"),
            marker=dict(size=6),
            hovertemplate=f"<b>{int(ano)}</b> · %{{x}}<br>%{{y:,}} voos<extra></extra>"))
    fig.update_layout(layout_base(), title="Evolução mensal do volume de voos (por ano)",
                      hovermode="x unified", legend=dict(orientation="h", y=1.12, x=0))
    fig.update_yaxes(title_text="Voos")
    return fig


def fig_sazonalidade(dff):
    """Média de voos por mês com destaque para picos."""
    if dff.empty:
        return fig_vazia()
    por_ano_mes = dff.groupby(["ANO", "MES"], observed=True).size().reset_index(name="V")
    med = por_ano_mes.groupby("MES")["V"].mean()
    med = med.reindex(range(1, 13))
    cores = [T.DESTAQUE if (pd.notna(v) and v >= med.max() * 0.92) else "#BBD3EA" for v in med]
    fig = go.Figure(go.Bar(
        x=[MESES_PT[m] for m in med.index], y=med.values, marker_color=cores,
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} voos/mês (média)<extra></extra>"))
    fig.update_layout(layout_base(), title="Sazonalidade — média mensal",
                      yaxis_title="Voos/mês")
    return fig


def fig_hubs(dff, n=12):
    """Ranking dos aeroportos com mais movimentos (origem + destino)."""
    if dff.empty:
        return fig_vazia()
    mov = pd.concat([dff["ORIGEM_IATA"], dff["DESTINO_IATA"]]).value_counts().head(n)
    cid = {**L.IATA_CIDADE}
    rotulos = [f"{cid.get(i, i)} · {i}" for i in mov.index]
    g = pd.DataFrame({"label": rotulos, "N": mov.values}).sort_values("N")
    fig = go.Figure(go.Bar(
        x=g["N"], y=g["label"], orientation="h",
        marker=dict(color=g["N"], colorscale=L.ESCALA_AZUL),
        text=[fmt_compacto(v) for v in g["N"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,} movimentos<extra></extra>"))
    fig.update_layout(layout_base(), title=f"Top {n} aeroportos por movimento",
                      margin=dict(l=30, r=70, t=56, b=38))
    fig.update_yaxes(automargin=True)
    fig.update_traces(cliponaxis=False)
    L.folga_eixo(fig, g["N"].max())
    return fig


def fig_frota(dff, n=8):
    """Mix de frota: famílias mais operadas, coloridas por fabricante."""
    if dff.empty or "FAMILIA_AERONAVE" not in dff.columns:
        return fig_vazia()
    g = (dff[dff["FAMILIA_AERONAVE"] != "Outros"]
         .groupby(["FABRICANTE", "FAMILIA_AERONAVE"], observed=True).size()
         .reset_index(name="N").sort_values("N", ascending=False).head(n).sort_values("N"))
    if g.empty:
        return fig_vazia()
    cores = [CORES_FABRICANTE.get(f, "#9AA8B8") for f in g["FABRICANTE"]]
    total = dff.shape[0]
    fig = go.Figure(go.Bar(
        x=g["N"], y=g["FAMILIA_AERONAVE"], orientation="h", marker_color=cores,
        text=[f"{v/total*100:.1f}%".replace(".", ",") for v in g["N"]], textposition="outside",
        customdata=g["FABRICANTE"],
        hovertemplate="<b>%{y}</b> (%{customdata})<br>%{x:,} voos<extra></extra>"))
    fig.update_layout(layout_base(), title="Frota mais operada (família · fabricante)",
                      margin=dict(l=30, r=60, t=56, b=38))
    fig.update_yaxes(automargin=True)
    fig.update_traces(cliponaxis=False)
    L.folga_eixo(fig, g["N"].max())
    return fig


def fig_pontualidade_cia(dff, n=8):
    """Taxa de atraso das maiores companhias (barras coloridas por grupo)."""
    if dff.empty:
        return fig_vazia()
    g = (dff.groupby("EMPRESA_NOME", observed=True)
         .agg(N=("EMPRESA_NOME", "size"), ATR=("ATRASADO", "mean"),
              GRUPO=("GRUPO", "first")).reset_index())
    g = g[g["N"] >= max(500, g["N"].max() * 0.01)].nlargest(n, "N").sort_values("ATR")
    if g.empty:
        return fig_vazia()
    g["PCT"] = (g["ATR"] * 100).round(1)
    cores = [CORES_GRUPO.get(gr, T.ACENTO) for gr in g["GRUPO"]]
    fig = go.Figure(go.Bar(
        x=g["PCT"], y=g["EMPRESA_NOME"], orientation="h", marker_color=cores,
        text=[f"{v:.1f}%".replace(".", ",") for v in g["PCT"]], textposition="outside",
        customdata=g["N"],
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% atrasos · %{customdata:,} voos<extra></extra>"))
    media = dff["ATRASADO"].mean() * 100
    fig.add_vline(x=media, line_dash="dash", line_color=T.TEXTO_SUAVE,
                  annotation_text=f"média {media:.1f}%".replace(".", ","),
                  annotation_position="top")
    fig.update_layout(layout_base(), title=f"Pontualidade — taxa de atraso das {n} maiores",
                      margin=dict(l=30, r=60, t=56, b=38), xaxis_title="% de voos atrasados")
    fig.update_yaxes(automargin=True)
    fig.update_traces(cliponaxis=False)
    L.folga_eixo(fig, g["PCT"].max())
    return fig


def fig_fluxo_regional(dff):
    """Heatmap de fluxo entre regiões (origem × destino)."""
    sub = dff[dff["ORIG_REGIAO"].notna() & dff["DEST_REGIAO"].notna()]
    if sub.empty:
        return fig_vazia("Sem voos domésticos com região no recorte")
    piv = (sub.groupby(["ORIG_REGIAO", "DEST_REGIAO"], observed=True).size()
           .reset_index(name="N")
           .pivot(index="ORIG_REGIAO", columns="DEST_REGIAO", values="N"))
    ordem = [r for r in REGIOES_ORD if r in piv.index]
    cols = [r for r in REGIOES_ORD if r in piv.columns]
    piv = piv.reindex(index=ordem, columns=cols)
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=cols, y=ordem, colorscale=L.ESCALA_AZUL,
        text=[[fmt_compacto(v) if pd.notna(v) else "" for v in row] for row in piv.values],
        texttemplate="%{text}", textfont=dict(size=10),
        hovertemplate="%{y} → %{x}<br>%{z:,} voos<extra></extra>",
        colorbar=dict(title="Voos", thickness=12, len=0.8)))
    fig.update_layout(layout_base(), title="Fluxo entre regiões (origem → destino)",
                      xaxis_title="Destino", yaxis_title="Origem")
    return fig


# ──────────────────────────── INSIGHTS DINÂMICOS ──────────────────────────────

def gerar_insights(dff):
    """Gera bullets de insight calculados a partir do recorte atual."""
    its = []
    if dff.empty:
        return [html.Li("Sem dados para o recorte selecionado.")]

    # Hub dominante
    mov = pd.concat([dff["ORIGEM_IATA"], dff["DESTINO_IATA"]]).value_counts()
    if len(mov):
        top = mov.index[0]
        cid = L.IATA_CIDADE.get(top, top)
        its.append(f"**{cid} ({top})** é o maior hub do recorte, com "
                   f"{fmt_compacto(mov.iloc[0])} movimentos "
                   f"({mov.iloc[0]/mov.sum()*100:.1f}% do total).".replace(".", ","))

    # Concentração de mercado
    g = dff.groupby("GRUPO", observed=True).size().sort_values(ascending=False)
    if len(g):
        top3 = g.head(3).sum() / g.sum() * 100
        its.append(f"Os três maiores grupos concentram **{top3:.0f}%** dos voos — "
                   f"mercado {'altamente ' if hhi(g) > 2500 else ''}concentrado "
                   f"(HHI {hhi(g):,.0f}).")

    # Recuperação em voo
    atr = dff[dff["ATRASADO"]]
    if len(atr) and "RECUPERACAO_MIN" in atr.columns:
        rec = atr["RECUPERACAO_MIN"].mean()
        if pd.notna(rec):
            its.append(f"Voos que partem atrasados recuperam em média **{rec:.0f} min** no ar — "
                       f"saem ~{atr['ATRASO_MIN'].mean():.0f} min atrasados e chegam "
                       f"~{atr['ATRASO_CHEGADA_MIN'].mean():.0f} min atrasados.")

    # Pico sazonal
    saz = dff.groupby("MES", observed=True).size()
    if len(saz):
        mtop = int(saz.idxmax())
        its.append(f"**{MESES_PT[mtop]}** é o mês de maior demanda; os meses de pico "
                   f"superam os de baixa em {(saz.max()/saz.min()-1)*100:.0f}%.")

    # Frota
    fab = dff.groupby("FABRICANTE", observed=True).size().sort_values(ascending=False)
    fab = fab[fab.index != "Outros"]
    if len(fab) >= 2:
        its.append(f"A frota é liderada por **{fab.index[0]}** "
                   f"({fab.iloc[0]/fab.sum()*100:.0f}%), seguido de **{fab.index[1]}** "
                   f"({fab.iloc[1]/fab.sum()*100:.0f}%).")

    # Efeito cascata por hora
    hh = (dff.dropna(subset=["HORA_PARTIDA"]).assign(H=dff["HORA_PARTIDA"].astype("Int64"))
          .groupby("H")["ATRASADO"].mean())
    if len(hh) > 8:
        manha = hh.reindex([6, 7, 8, 9]).mean()
        noite = hh.reindex([19, 20, 21, 22]).mean()
        if manha and manha > 0 and pd.notna(noite):
            its.append(f"**Efeito cascata**: voos da noite atrasam ~{noite/manha:.1f}× mais que os "
                       f"da manhã ({manha*100:.0f}% → {noite*100:.0f}%), efeito acumulado do dia."
                       .replace(".", ","))

    # Boeing × Embraer
    fb = dff.groupby("FABRICANTE", observed=True)["ATRASADO"].mean() * 100
    if {"Boeing", "Embraer"}.issubset(fb.dropna().index) and fb["Embraer"] > 0:
        its.append(f"Curiosamente, jatos **Boeing** atrasam {(fb['Boeing']/fb['Embraer']-1)*100:.0f}% "
                   f"mais que os **Embraer** ({fb['Embraer']:.0f}% vs {fb['Boeing']:.0f}%).")

    # Recuperação no ar (%)
    late = dff["ATRASO_MIN"] > 15
    if late.sum() > 0 and "ATRASO_CHEGADA_MIN" in dff.columns:
        salvos = (late & (dff["ATRASO_CHEGADA_MIN"] <= 15)).sum() / late.sum() * 100
        its.append(f"**{salvos:.0f}%** dos voos que partem atrasados ainda chegam no horário — "
                   f"o tempo é recuperado em voo.")

    # Distância média / ASK
    dist = dff["DIST_KM"].mean()
    if pd.notna(dist):
        its.append(f"A distância média das rotas mapeadas é de **{fmt(dist)} km**, "
                   f"com {fmt_compacto(dff['ASK'].sum())} assentos-km ofertados.")

    return [dcc.Markdown(i, className="insight-li") for i in its]


# ───────────────────────────────── LAYOUT ─────────────────────────────────────

def card(grafico_id, altura, md):
    return dbc.Col(dbc.Card(dbc.CardBody(
        dcc.Graph(id=grafico_id, style={"height": f"{altura}px"},
                  config={"displayModeBar": False})), className="painel"), md=md)


app.layout = html.Div([
    # Cabeçalho
    html.Div([
        html.Div([
            html.Span("✈", className="hd-logo"),
            html.Div([
                html.H1("Aviação Civil Brasileira", className="hd-title"),
                html.P("Painel Executivo · Dados públicos ANAC/VRA · 2022–2025",
                       className="hd-sub"),
            ]),
        ], className="hd-left"),
        html.Div([
            html.Div([
                html.Label("Ano", className="ctrl-lbl"),
                dcc.Dropdown(id="f-ano", clearable=False, className="ctrl-dd",
                             options=[{"label": "Todos os anos", "value": "all"}] +
                                     [{"label": str(a) + (" (parcial)" if a == L.ANO_PARCIAL else ""),
                                       "value": a} for a in ANOS],
                             value="all"),
            ], className="ctrl"),
            html.Div([
                html.Label("Segmento", className="ctrl-lbl"),
                dcc.Dropdown(id="f-seg", clearable=False, className="ctrl-dd",
                             options=[{"label": "Todos", "value": "all"},
                                      {"label": "Doméstico", "value": "Doméstico"},
                                      {"label": "Internacional", "value": "Internacional"}],
                             value="all"),
            ], className="ctrl"),
        ], className="hd-right"),
    ], className="header"),

    dbc.Container([
        html.Div(id="kpis"),

        dbc.Row([card("g-mapa", 470, 8), card("g-share", 470, 4)], className="g-row"),
        dbc.Row([card("g-evol", 330, 8), card("g-saz", 330, 4)], className="g-row"),
        dbc.Row([card("g-hubs", 400, 6), card("g-frota", 400, 6)], className="g-row"),
        dbc.Row([card("g-pont", 400, 6), card("g-fluxo", 400, 6)], className="g-row"),

        dbc.Row(dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([html.Span("💡", style={"fontSize": "1.2rem"}),
                      html.Span("  Insights do recorte selecionado", className="ins-title")],
                     className="ins-head"),
            html.Ul(id="insights", className="ins-list"),
            html.Div("Indicadores recalculados automaticamente conforme os filtros de "
                     "ano e segmento. ANAC/VRA — atraso = partida >15 min após o previsto.",
                     className="ins-foot"),
        ]), className="painel insight-card")), className="g-row mb-4"),
    ], fluid=True, className="container-main"),
], className="page")


# ──────────────────────────────── CALLBACK ────────────────────────────────────

@app.callback(
    [Output("kpis", "children"), Output("g-mapa", "figure"), Output("g-share", "figure"),
     Output("g-evol", "figure"), Output("g-saz", "figure"), Output("g-hubs", "figure"),
     Output("g-frota", "figure"), Output("g-pont", "figure"), Output("g-fluxo", "figure"),
     Output("insights", "children")],
    [Input("f-ano", "value"), Input("f-seg", "value")],
)
def atualizar(ano, seg):
    dff = df
    if seg == "Doméstico":
        dff = dff[dff["DOMESTICO"]]
    elif seg == "Internacional":
        dff = dff[dff["SEGMENTO"] == "Internacional"]

    dff_prev, label_prev = None, ""
    if ano != "all":
        ano = int(ano)
        base = dff
        dff = base[base["ANO"] == ano]
        if (ano - 1) in ANOS:
            dff_prev = base[base["ANO"] == ano - 1]
            label_prev = f"vs {ano-1}"

    return (
        montar_kpis(dff, dff_prev, label_prev),
        L.mapa_malha(dff), fig_share_grupo(dff), fig_evolucao(dff), fig_sazonalidade(dff),
        fig_hubs(dff), fig_frota(dff), fig_pontualidade_cia(dff), fig_fluxo_regional(dff),
        gerar_insights(dff),
    )


# ───────────────────────────────── ESTILO ─────────────────────────────────────

app.index_string = """
<!DOCTYPE html><html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box;}
  body{font-family:'Inter','Segoe UI',sans-serif;background:#EEF2F7;margin:0;color:#1A2332;}
  .page{min-height:100vh;}
  .container-main{padding:20px 26px 8px;max-width:1640px;}

  .header{background:linear-gradient(120deg,#0A2342 0%,#1565C0 100%);padding:18px 30px;
    display:flex;align-items:center;justify-content:space-between;color:#fff;
    box-shadow:0 6px 22px rgba(10,35,66,.28);position:sticky;top:0;z-index:50;}
  .hd-left{display:flex;align-items:center;gap:14px;}
  .hd-logo{font-size:2rem;background:rgba(255,255,255,.12);width:52px;height:52px;border-radius:14px;
    display:flex;align-items:center;justify-content:center;}
  .hd-title{margin:0;font-size:1.45rem;font-weight:800;letter-spacing:-.5px;}
  .hd-sub{margin:2px 0 0;font-size:.78rem;opacity:.8;font-weight:500;}
  .hd-right{display:flex;gap:14px;}
  .ctrl-lbl{font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;opacity:.8;
    display:block;margin-bottom:3px;font-weight:600;}
  .ctrl-dd{width:185px;font-size:13px;color:#1A2332;}

  /* KPIs */
  .kpi-row{display:flex;gap:14px;margin:20px 0 6px;flex-wrap:wrap;}
  .kpi-wrap{flex:1 1 0;min-width:150px;}
  .kpi-card{border:none!important;border-radius:14px!important;background:#fff;
    box-shadow:0 2px 10px rgba(10,35,66,.07)!important;transition:transform .18s,box-shadow .18s;
    height:100%;}
  .kpi-card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(10,35,66,.14)!important;}
  .kpi-card .card-body{padding:14px 16px;}
  .kpi-top{display:flex;justify-content:space-between;align-items:center;}
  .kpi-ic{font-size:1.25rem;opacity:.9;}
  .kpi-delta{font-size:.72rem;font-weight:700;}
  .kpi-val{font-size:1.62rem;font-weight:800;line-height:1.1;margin-top:6px;}
  .kpi-tit{font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;
    color:#5B6B7F;margin-top:3px;}
  .kpi-sub{font-size:.66rem;color:#9AA8B8;margin-top:1px;font-weight:500;}

  /* Painéis */
  .g-row{margin-bottom:18px;}
  .g-row > [class*="col"]{padding-left:9px;padding-right:9px;}
  .painel{border:none!important;border-radius:16px!important;background:#fff!important;
    box-shadow:0 2px 12px rgba(10,35,66,.07)!important;height:100%;}
  .painel .card-body{padding:8px 10px;}

  .insight-card{background:linear-gradient(135deg,#F0F7FF 0%,#EEF6F3 100%)!important;}
  .insight-card .card-body{padding:18px 22px;}
  .ins-head{display:flex;align-items:center;margin-bottom:8px;}
  .ins-title{font-weight:800;color:#0A2342;font-size:1.02rem;}
  .ins-list{margin:0;padding-left:6px;list-style:none;columns:2;column-gap:34px;}
  .ins-list li{margin-bottom:9px;break-inside:avoid;}
  .insight-li p{margin:0 0 4px;padding-left:20px;position:relative;line-height:1.5;font-size:.9rem;}
  .insight-li p::before{content:"▹";position:absolute;left:0;color:#2196F3;font-weight:700;}
  .ins-foot{font-size:.72rem;color:#9AA8B8;margin-top:10px;border-top:1px solid #DCE6F0;padding-top:8px;}

  .Select-control,.is-focused .Select-control{border-radius:9px!important;}
  ::-webkit-scrollbar{width:8px;height:8px;}
  ::-webkit-scrollbar-thumb{background:#C2D0E0;border-radius:4px;}
</style></head>
<body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>
"""

if __name__ == "__main__":
    print("\n  ✈  Painel Executivo  →  http://localhost:8050\n")
    app.run(debug=False, port=8050)
