import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

PASTA_PROC = Path("dados_processados")

def carregar_dados():
    """Carrega o dataset final e ajusta tipos."""
    caminho = PASTA_PROC / "dataset_final.csv"
    if not caminho.exists():
        print("dataset_final.csv não encontrado → executando preparação...")
        import subprocess, sys
        subprocess.run([sys.executable, "prepara_dados.py"], check=True)

    df = pd.read_csv(caminho, low_memory=False)

    for col in ["ANO", "MES", "TRIMESTRE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["ATRASO_MIN"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["ATRASADO", "CANCELADO"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin(["true", "1", "yes"])

    return df

df = carregar_dados()

COR_PRIMARIA   = "#0A2342"
COR_DESTAQUE   = "#E8563A"
COR_ACENTO     = "#2196F3"
COR_VERDE      = "#26A69A"
COR_BG         = "#F0F4F8"
COR_CARD       = "#FFFFFF"
COR_TEXTO      = "#1A2332"

CORES_EMPRESA = {
    "GLO": "#FF6900",
    "TAM": "#C8102E",
    "AZU": "#0057A8",
    "VBL": "#8DC63F",
    "PAM": "#5B2D8E",
}

def pct_atrasado(df):
    """Calcula percentual de voos atrasados."""
    if "ATRASADO" not in df.columns: return 0
    v = df["ATRASADO"].mean()
    return round(v * 100, 1) if not np.isnan(v) else 0

def pct_cancelado(df):
    """Calcula percentual de voos cancelados."""
    if "CANCELADO" not in df.columns: return 0
    v = df["CANCELADO"].mean()
    return round(v * 100, 1) if not np.isnan(v) else 0

def media_atraso(df):
    """Calcula atraso medio em minutos apenas para voos atrasados."""
    if "ATRASO_MIN" not in df.columns:
        return 0
    if "ATRASADO" in df.columns:
        serie = df.loc[df["ATRASADO"] == True, "ATRASO_MIN"]
    else:
        serie = df["ATRASO_MIN"]
    v = serie.mean()
    return round(v, 1) if pd.notna(v) else 0


def kpi_card(titulo, valor, subtitulo="", cor_destaque=COR_ACENTO, icone="✈"):
    """Cria um card de KPI."""
    return dbc.Card([
        dbc.CardBody([
            html.Div(icone, className="kpi-icon"),
            html.Div(valor, className="kpi-valor", style={"color": cor_destaque}),
            html.Div(titulo, className="kpi-titulo"),
            html.Div(subtitulo, className="kpi-sub"),
        ])
    ], className="kpi-card shadow-sm")


def fig_voos_por_mes(df):
    """Gera grafico de volume de voos por mes."""
    if "ANO" not in df.columns or "MES" not in df.columns:
        return go.Figure()

    grp = (
        df.groupby(["ANO", "MES"])
          .size()
          .reset_index(name="VOOS")
    )
    grp["PERIODO"] = grp["ANO"].astype(str) + "-" + grp["MES"].astype(str).str.zfill(2)
    grp = grp.sort_values("PERIODO")

    fig = px.line(
        grp, x="PERIODO", y="VOOS", color="ANO",
        title="Volume de Voos por Mês",
        labels={"PERIODO": "Mês", "VOOS": "Nº de Voos", "ANO": "Ano"},
        color_discrete_sequence=[COR_ACENTO, COR_DESTAQUE, COR_VERDE],
        markers=True,
    )
    fig.update_layout(**layout_base())
    fig.update_traces(line=dict(width=3), marker=dict(size=7, line=dict(width=1, color="#FFFFFF")))
    fig.update_xaxes(tickangle=45)
    return fig


def fig_top_rotas(df, n=15):
    """Gera grafico com as rotas mais frequentes."""
    if "ROTA" not in df.columns:
        return go.Figure()

    top = (
        df.groupby("ROTA")
          .size()
          .nlargest(n)
          .reset_index(name="VOOS")
          .sort_values("VOOS")
    )
    fig = px.bar(
        top, x="VOOS", y="ROTA", orientation="h",
        title=f"Top {n} Rotas por Volume de Voos",
        labels={"VOOS": "Nº de Voos", "ROTA": "Rota"},
        color="VOOS",
        color_continuous_scale=[[0, "#BDD7EE"], [1, COR_PRIMARIA]],
        text="VOOS",
    )
    fig.update_layout(**layout_base())
    fig.update_traces(marker_line_width=0, opacity=0.92)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_yaxes(automargin=True)
    fig.update_coloraxes(showscale=False)
    return fig


def fig_market_share(df):
    """Gera grafico de market share por empresa."""
    if "EMPRESA" not in df.columns:
        return go.Figure()

    share = (
        df.groupby("EMPRESA")
          .size()
          .nlargest(8)
          .reset_index(name="VOOS")
    )
    share["PCT"] = (share["VOOS"] / share["VOOS"].sum() * 100).round(1)

    cores = [CORES_EMPRESA.get(e, COR_ACENTO) for e in share["EMPRESA"]]

    fig = go.Figure(go.Pie(
        labels=share["EMPRESA"],
        values=share["VOOS"],
        hole=0.62,
        marker_colors=cores,
        textinfo="percent",
        textfont=dict(size=12),
        sort=False,
        hovertemplate="<b>%{label}</b><br>%{value:,} voos<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title="Market Share por Companhia Aérea",
        **layout_base(),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5, yanchor="middle"),
        annotations=[
            dict(
                text=f"{share['VOOS'].sum():,}<br>voos",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=13, color=COR_PRIMARIA),
            )
        ],
    )
    return fig


def fig_mapa_rotas(df):
    """Gera mapa de aeroportos com volume de voos."""
    if "ORIG_LAT" not in df.columns:
        return go.Figure()

    orig = (
        df.dropna(subset=["ORIG_LAT", "ORIG_LON"])
          .groupby(["ORIGEM", "ORIG_LAT", "ORIG_LON", "ORIG_CIDADE"])
          .size()
          .reset_index(name="VOOS")
    )

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lat=orig["ORIG_LAT"],
        lon=orig["ORIG_LON"],
        text=orig.apply(
            lambda r: f"<b>{r['ORIG_CIDADE']}</b> ({r['ORIGEM']})<br>{r['VOOS']:,} voos", axis=1
        ),
        mode="markers+text",
        textposition="top center",
        marker=dict(
            size=np.sqrt(orig["VOOS"]) * 0.5 + 4,
            color=orig["VOOS"],
            colorscale=[[0, "#BDD7EE"], [1, COR_PRIMARIA]],
            line=dict(width=1, color="white"),
            showscale=True,
            colorbar=dict(title="Voos"),
        ),
        hoverinfo="text",
        name="Aeroportos",
    ))

    fig.update_layout(
        title="Mapa de Aeroportos — Volume de Voos",
        geo=dict(
            scope="south america",
            showland=True, landcolor="#EEF2F7",
            showocean=True, oceancolor="#D6E8F7",
            showcountries=True, countrycolor="#AABBCC",
            showlakes=True, lakecolor="#D6E8F7",
            center=dict(lat=-15, lon=-52),
            projection_scale=3.2,
        ),
        **{**layout_base(), "margin": dict(l=0, r=0, t=50, b=0)},
    )
    return fig


def fig_atrasos_empresa(df):
    """Gera grafico de atrasos por empresa."""
    if "EMPRESA" not in df.columns or "ATRASADO" not in df.columns:
        return go.Figure()

    grp = (
        df.groupby("EMPRESA")
          .agg(
              TOTAL=("EMPRESA", "count"),
              ATRASADOS=("ATRASADO", "sum"),
          )
          .reset_index()
    )
    grp["PCT_ATRASO"] = (grp["ATRASADOS"] / grp["TOTAL"] * 100).round(1)
    grp = grp[grp["TOTAL"] > 100].sort_values("PCT_ATRASO")

    cores = [CORES_EMPRESA.get(e, COR_ACENTO) for e in grp["EMPRESA"]]

    fig = go.Figure(go.Bar(
        x=grp["EMPRESA"], y=grp["PCT_ATRASO"],
        marker_color=cores,
        text=grp["PCT_ATRASO"].apply(lambda v: f"{v}%"),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Atraso: %{y}%<extra></extra>",
    ))
    fig.update_layout(
        title="Taxa de Atraso por Companhia Aérea",
        xaxis_title="Companhia",
        yaxis_title="% de Voos Atrasados",
        **layout_base(),
    )
    fig.update_traces(marker_line_width=0, opacity=0.95)
    return fig


def fig_sazonalidade(df):
    """Gera grafico de sazonalidade mensal."""
    if "MES" not in df.columns:
        return go.Figure()

    MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

    grp = df.groupby("MES").size().reset_index(name="VOOS")
    grp["MES_NOME"] = grp["MES"].apply(
        lambda m: MESES[int(m) - 1]
        if pd.notna(m) and 1 <= int(m) <= 12
        else "?"
    )

    fig = go.Figure(go.Bar(
        x=grp["MES_NOME"], y=grp["VOOS"],
        marker=dict(
            color=grp["VOOS"],
            colorscale=[[0, "#BDD7EE"], [1, COR_PRIMARIA]],
        ),
        hovertemplate="<b>%{x}</b><br>%{y:,} voos<extra></extra>",
    ))
    fig.update_layout(
        title="Sazonalidade — Voos por Mês (todos os anos)",
        xaxis_title="Mês", yaxis_title="Nº de Voos",
        **layout_base(),
    )
    fig.update_traces(marker_line_width=0)
    return fig


def layout_base():
    """Define o layout padrao dos graficos."""
    return dict(
        template="plotly_white",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        colorway=[COR_ACENTO, COR_DESTAQUE, COR_VERDE, COR_PRIMARIA, "#7E57C2", "#F59E0B"],
        font=dict(family="'Segoe UI', Arial, sans-serif", color=COR_TEXTO, size=12),
        title_font=dict(size=15, color=COR_PRIMARIA, family="'Segoe UI', Arial, sans-serif"),
        title_x=0.01,
        margin=dict(l=28, r=20, t=56, b=36),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#D9E2EC", font_size=12, font_color=COR_TEXTO),
        hovermode="x unified",
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#D9E2EC", tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="#E9EEF5", zeroline=False, tickfont=dict(size=11)),
    )


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap",
    ],
    title="Voos no Brasil — Visão Geral",
)

total_voos    = len(df)
empresas_ativ = df["EMPRESA"].nunique() if "EMPRESA" in df.columns else 0
rotas_ativas  = df["ROTA"].nunique()    if "ROTA"    in df.columns else 0
pct_atr       = pct_atrasado(df)
pct_canc      = pct_cancelado(df)
med_atr       = media_atraso(df)
anos_disp     = sorted(df["ANO"].dropna().unique().astype(int)) if "ANO" in df.columns else []

app.layout = html.Div([

    html.Div([
        html.Div([
            html.Span("✈", style={"fontSize": "2rem", "marginRight": "12px"}),
            html.Div([
                html.H1("Aviação Civil Brasileira", className="header-title"),
                html.P("Painel Executivo de Indicadores | Dados ANAC", className="header-sub"),
            ])
        ], className="header-left"),
        html.Div([
            dcc.Dropdown(
                id="filtro-ano-geral",
                options=[{"label": "Todos os Anos", "value": "all"}] +
                        [{"label": str(a), "value": a} for a in anos_disp],
                value="all",
                clearable=False,
                style={"width": "180px", "fontSize": "13px"},
            ),
        ], className="header-right"),
    ], className="header-bar"),

    dbc.Container([
        dbc.Row([
            dbc.Col(kpi_card("Total de Voos",      f"{total_voos:,}",    "no período analisado", COR_ACENTO,    "✈"), md=2),
            dbc.Col(kpi_card("Companhias Ativas",  str(empresas_ativ),   "operando no Brasil",   COR_PRIMARIA,  "🏢"), md=2),
            dbc.Col(kpi_card("Rotas Distintas",    f"{rotas_ativas:,}",  "pares origem-destino", COR_VERDE,     "🗺"), md=2),
            dbc.Col(kpi_card("Taxa de Atraso",     f"{pct_atr}%",        "> 15 min de atraso",   COR_DESTAQUE,  "⏱"), md=2),
            dbc.Col(kpi_card("Taxa de Cancelam.",  f"{pct_canc}%",       "voos cancelados",      "#9C27B0",     "❌"), md=2),
            dbc.Col(kpi_card("Atraso Médio",       f"{med_atr} min",     "quando há atraso",     "#FF9800",     "⌛"), md=2),
        ], className="mb-4 mt-3", id="kpi-row"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody(dcc.Graph(id="grafico-mapa", figure=fig_mapa_rotas(df),
                                       style={"height": "420px"}))
            ], className="shadow-sm"), md=8),
            dbc.Col(dbc.Card([
                dbc.CardBody(dcc.Graph(id="grafico-share", figure=fig_market_share(df),
                                       style={"height": "420px"}))
            ], className="shadow-sm"), md=4),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody(dcc.Graph(id="grafico-mensal", figure=fig_voos_por_mes(df),
                                       style={"height": "320px"}))
            ], className="shadow-sm"), md=8),
            dbc.Col(dbc.Card([
                dbc.CardBody(dcc.Graph(id="grafico-sazonal", figure=fig_sazonalidade(df),
                                       style={"height": "320px"}))
            ], className="shadow-sm"), md=4),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody(dcc.Graph(id="grafico-rotas", figure=fig_top_rotas(df),
                                       style={"height": "420px"}))
            ], className="shadow-sm"), md=6),
            dbc.Col(dbc.Card([
                dbc.CardBody(dcc.Graph(id="grafico-atraso-emp", figure=fig_atrasos_empresa(df),
                                       style={"height": "420px"}))
            ], className="shadow-sm"), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H5("💡 Principais Insights", style={"color": COR_PRIMARIA, "fontWeight": "700"}),
                    html.Ul([
                        html.Li("GRU e CGH concentram o maior volume de voos do país, consolidando São Paulo como hub dominante."),
                        html.Li("Os meses de janeiro, julho e dezembro apresentam picos de demanda, refletindo o padrão de férias escolares e festas de fim de ano."),
                        html.Li("A aviação doméstica responde por ~85% dos voos, com rotas curtas como GRU-CGH entre as mais operadas."),
                        html.Li("O período pós-pandemia (2022–2024) mostra recuperação consistente, com crescimento anual de voos."),
                    ], style={"lineHeight": "2", "color": COR_TEXTO}),
                ])
            ], className="shadow-sm insight-card")),
        ], className="mb-5"),

    ], fluid=True),

], style={"backgroundColor": COR_BG, "minHeight": "100vh"})


@app.callback(
    [Output("kpi-row",           "children"),
     Output("grafico-mapa",      "figure"),
     Output("grafico-share",     "figure"),
     Output("grafico-mensal",    "figure"),
     Output("grafico-sazonal",   "figure"),
     Output("grafico-rotas",     "figure"),
     Output("grafico-atraso-emp","figure")],
    Input("filtro-ano-geral", "value"),
)
def atualizar_visao(ano):
    """Atualiza KPIs e graficos conforme o filtro de ano."""
    dff = df if ano == "all" else df[df["ANO"] == int(ano)]

    total      = len(dff)
    n_emp      = dff["EMPRESA"].nunique() if "EMPRESA" in dff.columns else 0
    n_rota     = dff["ROTA"].nunique()    if "ROTA"    in dff.columns else 0
    p_atr      = pct_atrasado(dff)
    p_canc     = pct_cancelado(dff)
    m_atr      = media_atraso(dff)

    kpis = dbc.Row([
        dbc.Col(kpi_card("Total de Voos",     f"{total:,}",    "no período analisado", COR_ACENTO,   "✈"), md=2),
        dbc.Col(kpi_card("Companhias Ativas", str(n_emp),      "operando no Brasil",   COR_PRIMARIA, "🏢"), md=2),
        dbc.Col(kpi_card("Rotas Distintas",   f"{n_rota:,}",   "pares origem-destino", COR_VERDE,    "🗺"), md=2),
        dbc.Col(kpi_card("Taxa de Atraso",    f"{p_atr}%",     "> 15 min de atraso",   COR_DESTAQUE, "⏱"), md=2),
        dbc.Col(kpi_card("Taxa de Cancelam.", f"{p_canc}%",    "voos cancelados",      "#9C27B0",    "❌"), md=2),
        dbc.Col(kpi_card("Atraso Médio",      f"{m_atr} min",  "quando há atraso",     "#FF9800",    "⌛"), md=2),
    ], className="mb-4 mt-3")

    return (
        kpis.children,
        fig_mapa_rotas(dff),
        fig_market_share(dff),
        fig_voos_por_mes(dff),
        fig_sazonalidade(dff),
        fig_top_rotas(dff),
        fig_atrasos_empresa(dff),
    )


app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Montserrat', 'Segoe UI', sans-serif; background: #F0F4F8; margin: 0; }

        .header-bar {
            background: linear-gradient(135deg, #0A2342 0%, #1565C0 100%);
            padding: 18px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        .header-left { display: flex; align-items: center; }
        .header-title { margin: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px; }
        .header-sub   { margin: 2px 0 0; font-size: 0.8rem; opacity: 0.75; }
        .header-right { display: flex; align-items: center; gap: 12px; }

        .kpi-card {
            border: none !important;
            border-radius: 12px !important;
            text-align: center;
            padding: 4px;
            transition: transform .2s, box-shadow .2s;
        }
        .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.12) !important; }
        .kpi-icon   { font-size: 1.6rem; margin-bottom: 4px; }
        .kpi-valor  { font-size: 1.8rem; font-weight: 800; line-height: 1.1; }
        .kpi-titulo { font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
                      letter-spacing: 0.05em; color: #555; margin-top: 2px; }
        .kpi-sub    { font-size: 0.65rem; color: #888; }

        .shadow-sm { box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important; border-radius: 12px !important; border: none !important; }
        .insight-card { background: linear-gradient(135deg, #EBF5FF 0%, #F0F9F8 100%) !important; }

        .Select-control { border-radius: 8px !important; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n  ✈  Dashboard 1 — Visão Geral")
    print("  Acesse: http://localhost:8050\n")
    app.run(debug=False, port=8050)
