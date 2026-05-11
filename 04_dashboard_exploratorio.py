import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc

PASTA_PROC = Path("dados_processados")

def carregar_dados():
    """Carrega o dataset final e ajusta tipos."""
    caminho = PASTA_PROC / "dataset_final.csv"
    if not caminho.exists():
        import subprocess, sys
        subprocess.run([sys.executable, "02_preparar_dados.py"], check=True)

    df = pd.read_csv(caminho, low_memory=False)
    for col in ["ANO","MES","TRIMESTRE","ATRASO_MIN","TARIFA_MEDIA"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["ATRASADO","CANCELADO"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin(["true","1","yes"])
    return df

df = carregar_dados()

COR_PRIMARIA  = "#0A2342"
COR_DESTAQUE  = "#E8563A"
COR_ACENTO    = "#2196F3"
COR_VERDE     = "#26A69A"
COR_BG        = "#F0F4F8"
COR_TEXTO     = "#1A2332"

CORES_EMPRESA = {
    "GLO":"#FF6900","TAM":"#C8102E","AZU":"#0057A8","VBL":"#8DC63F","PAM":"#5B2D8E",
}

SEQ_CORES = [COR_PRIMARIA, COR_ACENTO, COR_DESTAQUE, COR_VERDE,
             "#9C27B0","#FF9800","#795548","#607D8B"]

MESES_NOME = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
              7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

anos_disp = sorted(df["ANO"].dropna().unique().astype(int)) if "ANO" in df.columns else []
emps_disp = sorted(df["EMPRESA"].dropna().unique())         if "EMPRESA" in df.columns else []
regs_disp = sorted(df["ORIG_REGIAO"].dropna().unique())     if "ORIG_REGIAO" in df.columns else []
tip_linha  = sorted(df["TIPO_LINHA"].dropna().unique())     if "TIPO_LINHA" in df.columns else []


def opt(lst):
    """Converte lista em opcoes para componentes Dash."""
    return [{"label": v, "value": v} for v in lst]


def layout_base(h=350):
    """Define o layout padrao dos graficos."""
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'Segoe UI',Arial,sans-serif", color=COR_TEXTO, size=12),
        title_font=dict(size=14, color=COR_PRIMARIA),
        margin=dict(l=20,r=20,t=50,b=20),
        hoverlabel=dict(bgcolor="white", bordercolor="#DDD", font_size=12),
        height=h,
    )

def card_grafico(id_grafico, titulo="", altura=350):
    """Cria um card com grafico."""
    return dbc.Card([
        dbc.CardHeader(titulo, className="card-header-custom") if titulo else None,
        dbc.CardBody(
            dcc.Graph(id=id_grafico, style={"height": f"{altura}px"}, config={"displayModeBar": False})
        ),
    ], className="shadow-card mb-4")


app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap",
    ],
    title="Voos no Brasil — Exploração",
)

sidebar = html.Div([
    html.Div([
        html.Span("✈", style={"fontSize":"1.8rem"}),
        html.Span("  Exploração Interativa", style={"fontWeight":"800","fontSize":"1rem"}),
    ], className="sidebar-title"),

    html.Hr(className="sidebar-hr"),

    html.Label("📅 Período (Anos)", className="filter-label"),
    dcc.Checklist(
        id="filtro-anos",
        options=opt(anos_disp),
        value=anos_disp,
        labelStyle={"display":"block","marginBottom":"4px"},
        className="custom-check",
    ),

    html.Hr(className="sidebar-hr"),

    html.Label("✈ Companhias Aéreas", className="filter-label"),
    dcc.Checklist(
        id="filtro-empresas",
        options=opt(emps_disp),
        value=emps_disp,
        labelStyle={"display":"block","marginBottom":"4px"},
        className="custom-check",
    ),

    html.Hr(className="sidebar-hr"),

    html.Label("🗺 Região de Origem", className="filter-label"),
    dcc.Checklist(
        id="filtro-regioes",
        options=opt(regs_disp),
        value=regs_disp,
        labelStyle={"display":"block","marginBottom":"4px"},
        className="custom-check",
    ),

    html.Hr(className="sidebar-hr"),

    html.Label("🌐 Tipo de Voo", className="filter-label"),
    dcc.RadioItems(
        id="filtro-tipo",
        options=[{"label":"Todos","value":"todos"}] + opt(tip_linha),
        value="todos",
        labelStyle={"display":"block","marginBottom":"4px"},
        className="custom-check",
    ),

    html.Hr(className="sidebar-hr"),

    html.Label("⏱ Apenas Voos Atrasados", className="filter-label"),
    dcc.RadioItems(
        id="filtro-atrasado",
        options=[{"label":"Todos","value":"todos"},
                 {"label":"Atrasados","value":"sim"},
                 {"label":"No Horário","value":"nao"}],
        value="todos",
        labelStyle={"display":"block","marginBottom":"4px"},
        className="custom-check",
    ),

    html.Hr(className="sidebar-hr"),

    html.Div(id="contador-registros", className="contador-box"),

], className="sidebar")

conteudo = html.Div([
    dbc.Tabs([
        dbc.Tab(label="🗺  Rotas & Volume", tab_id="tab-rotas", children=[
            dbc.Row([
                dbc.Col(card_grafico("graf-vol-tempo",  altura=320), md=8),
                dbc.Col(card_grafico("graf-pizza-emp",  altura=320), md=4),
            ]),
            dbc.Row([
                dbc.Col(card_grafico("graf-top-rotas",  altura=380), md=6),
                dbc.Col(card_grafico("graf-heatmap-mes",altura=380), md=6),
            ]),
        ]),
        dbc.Tab(label="⏱  Pontualidade", tab_id="tab-pont", children=[
            dbc.Row([
                dbc.Col(card_grafico("graf-atraso-hist",  altura=320), md=6),
                dbc.Col(card_grafico("graf-atraso-emp",   altura=320), md=6),
            ]),
            dbc.Row([
                dbc.Col(card_grafico("graf-atraso-hora",  altura=320), md=6),
                dbc.Col(card_grafico("graf-canc-mes",     altura=320), md=6),
            ]),
        ]),
        dbc.Tab(label="💰  Tarifas", tab_id="tab-tarifas", children=[
            dbc.Row([
                dbc.Col(card_grafico("graf-tarifa-emp",  altura=320), md=6),
                dbc.Col(card_grafico("graf-tarifa-mes",  altura=320), md=6),
            ]),
            dbc.Row([
                dbc.Col(card_grafico("graf-tarifa-rota", altura=360), md=12),
            ]),
        ]),
        dbc.Tab(label="📊  Comparativo", tab_id="tab-comp", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Variável X:", className="filter-label"),
                    dcc.Dropdown(
                        id="comp-eixo-x",
                        options=[
                            {"label":"Companhia","value":"EMPRESA"},
                            {"label":"Mês","value":"MES"},
                            {"label":"Ano","value":"ANO"},
                            {"label":"Região Origem","value":"ORIG_REGIAO"},
                            {"label":"Trimestre","value":"TRIMESTRE"},
                        ],
                        value="EMPRESA", clearable=False,
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Métrica:", className="filter-label"),
                    dcc.Dropdown(
                        id="comp-metrica",
                        options=[
                            {"label":"Nº de Voos","value":"n_voos"},
                            {"label":"Taxa de Atraso (%)","value":"pct_atraso"},
                            {"label":"Taxa de Cancelamento (%)","value":"pct_canc"},
                            {"label":"Atraso Médio (min)","value":"med_atraso"},
                            {"label":"Tarifa Média (R$)","value":"tarifa_media"},
                        ],
                        value="n_voos", clearable=False,
                    ),
                ], md=4),
                dbc.Col([
                    html.Label("Separar por:", className="filter-label"),
                    dcc.Dropdown(
                        id="comp-cor",
                        options=[{"label":"Nenhum","value":"none"},
                                 {"label":"Companhia","value":"EMPRESA"},
                                 {"label":"Ano","value":"ANO"},
                                 {"label":"Tipo de Voo","value":"TIPO_LINHA"}],
                        value="none", clearable=False,
                    ),
                ], md=4),
            ], className="mb-3"),
            card_grafico("graf-comparativo", altura=420),
        ]),
        dbc.Tab(label="📋  Tabela", tab_id="tab-dados", children=[
            dbc.Row([
                dbc.Col([
                    html.Label("Selecionar colunas:", className="filter-label"),
                    dcc.Dropdown(
                        id="tabela-cols",
                        options=[{"label":c,"value":c} for c in df.columns],
                        value=[c for c in ["EMPRESA","ORIGEM","DESTINO","ROTA","ANO","MES",
                                           "SITUACAO","ATRASO_MIN","TARIFA_MEDIA"]
                               if c in df.columns],
                        multi=True,
                    ),
                ], md=12),
            ], className="mb-3"),
            html.Div(id="tabela-dados"),
            html.Div(id="tabela-download-btn", className="mt-2"),
        ]),

    ], id="tabs-principais", active_tab="tab-rotas"),

], className="conteudo")

app.layout = html.Div([
    sidebar,
    conteudo,
], style={"display":"flex","minHeight":"100vh","backgroundColor":COR_BG})


def filtrar(anos, empresas, regioes, tipo, atrasado):
    """Aplica os filtros principais ao dataset."""
    dff = df.copy()
    if anos and "ANO" in dff.columns:
        dff = dff[dff["ANO"].isin([int(a) for a in anos])]
    if empresas and "EMPRESA" in dff.columns:
        dff = dff[dff["EMPRESA"].isin(empresas)]
    if regioes and "ORIG_REGIAO" in dff.columns:
        dff = dff[dff["ORIG_REGIAO"].isin(regioes)]
    if tipo and tipo != "todos" and "TIPO_LINHA" in dff.columns:
        dff = dff[dff["TIPO_LINHA"] == tipo]
    if atrasado == "sim" and "ATRASADO" in dff.columns:
        dff = dff[dff["ATRASADO"] == True]
    elif atrasado == "nao" and "ATRASADO" in dff.columns:
        dff = dff[dff["ATRASADO"] == False]
    return dff


@app.callback(
    [Output("graf-vol-tempo","figure"),
     Output("graf-pizza-emp","figure"),
     Output("graf-top-rotas","figure"),
     Output("graf-heatmap-mes","figure"),
     Output("contador-registros","children")],
    [Input("filtro-anos","value"),
     Input("filtro-empresas","value"),
     Input("filtro-regioes","value"),
     Input("filtro-tipo","value"),
     Input("filtro-atrasado","value")],
)
def atualizar_rotas(anos, empresas, regioes, tipo, atrasado):
    """Atualiza graficos e contador da aba Rotas."""
    dff = filtrar(anos, empresas, regioes, tipo, atrasado)

    if "ANO" in dff.columns and "MES" in dff.columns:
        grp = dff.groupby(["ANO","MES"]).size().reset_index(name="VOOS")
        grp["PERIODO"] = grp["ANO"].astype(str)+"-"+grp["MES"].astype(str).str.zfill(2)
        grp = grp.sort_values("PERIODO")
        fig_vol = px.line(grp, x="PERIODO", y="VOOS", color="ANO",
                          title="Volume de Voos ao Longo do Tempo",
                          markers=True, color_discrete_sequence=SEQ_CORES)
        fig_vol.update_layout(**layout_base())
        fig_vol.update_xaxes(tickangle=45)
    else:
        fig_vol = go.Figure()

    if "EMPRESA" in dff.columns:
        share = dff.groupby("EMPRESA").size().nlargest(8).reset_index(name="VOOS")
        cores = [CORES_EMPRESA.get(e, COR_ACENTO) for e in share["EMPRESA"]]
        fig_pizza = go.Figure(go.Pie(
            labels=share["EMPRESA"], values=share["VOOS"], hole=0.5,
            marker_colors=cores, textinfo="label+percent",
        ))
        fig_pizza.update_layout(title="Participação por Companhia", **layout_base())
    else:
        fig_pizza = go.Figure()

    if "ROTA" in dff.columns:
        top = dff.groupby("ROTA").size().nlargest(15).reset_index(name="VOOS").sort_values("VOOS")
        fig_rotas = px.bar(top, x="VOOS", y="ROTA", orientation="h",
                           title="Top 15 Rotas", color="VOOS",
                           color_continuous_scale=[[0,"#BDD7EE"],[1,COR_PRIMARIA]])
        fig_rotas.update_layout(**layout_base(380))
        fig_rotas.update_coloraxes(showscale=False)
    else:
        fig_rotas = go.Figure()

    if "MES" in dff.columns and "DIA_SEM" in dff.columns:
        ordem_dia = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        nomes_dia  = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
        grp2 = dff.groupby(["MES","DIA_SEM"]).size().reset_index(name="VOOS")
        grp2["MES_NOME"] = grp2["MES"].map(MESES_NOME)
        pivot = grp2.pivot_table(index="DIA_SEM", columns="MES_NOME", values="VOOS", aggfunc="sum")
        meses_ord = [MESES_NOME[m] for m in sorted(MESES_NOME) if MESES_NOME[m] in pivot.columns]
        pivot = pivot[[c for c in meses_ord if c in pivot.columns]]
        dias_pres = [d for d in ordem_dia if d in pivot.index]
        pivot = pivot.loc[dias_pres]
        pivot.index = [nomes_dia[ordem_dia.index(d)] for d in dias_pres]
        fig_heat = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0,"#EEF5FF"],[0.5,COR_ACENTO],[1,COR_PRIMARIA]],
            hoverongaps=False,
            hovertemplate="Mês: %{x}<br>Dia: %{y}<br>Voos: %{z:,}<extra></extra>",
        ))
        fig_heat.update_layout(title="Intensidade: Mês × Dia da Semana", **layout_base(380))
    else:
        fig_heat = go.Figure()

    contador = html.Div([
        html.Div(f"{len(dff):,}", style={"fontSize":"1.4rem","fontWeight":"800","color":COR_ACENTO}),
        html.Div("registros filtrados", style={"fontSize":"0.7rem","color":"#888"}),
    ], style={"textAlign":"center","padding":"8px","background":"#EEF5FF","borderRadius":"8px"})

    return fig_vol, fig_pizza, fig_rotas, fig_heat, contador


@app.callback(
    [Output("graf-atraso-hist","figure"),
     Output("graf-atraso-emp","figure"),
     Output("graf-atraso-hora","figure"),
     Output("graf-canc-mes","figure")],
    [Input("filtro-anos","value"),
     Input("filtro-empresas","value"),
     Input("filtro-regioes","value"),
     Input("filtro-tipo","value"),
     Input("filtro-atrasado","value")],
)
def atualizar_pontualidade(anos, empresas, regioes, tipo, atrasado):
    """Atualiza graficos da aba Pontualidade."""
    dff = filtrar(anos, empresas, regioes, tipo, atrasado)

    if "ATRASO_MIN" in dff.columns:
        atr = dff[(dff["ATRASO_MIN"] > 0) & (dff["ATRASO_MIN"] < 300)]["ATRASO_MIN"].dropna()
        fig_hist = px.histogram(atr, nbins=40, title="Distribuição dos Atrasos (min)",
                                labels={"value":"Minutos de Atraso","count":"Nº de Voos"},
                                color_discrete_sequence=[COR_ACENTO])
        fig_hist.update_layout(**layout_base())
        fig_hist.add_vline(x=atr.mean(), line_dash="dash", line_color=COR_DESTAQUE,
                           annotation_text=f"Média: {atr.mean():.0f} min")
    else:
        fig_hist = go.Figure()

    if "EMPRESA" in dff.columns and "ATRASADO" in dff.columns:
        grp = dff.groupby("EMPRESA").agg(
            TOTAL=("EMPRESA","count"), AT=("ATRASADO","sum")).reset_index()
        grp["PCT"] = (grp["AT"]/grp["TOTAL"]*100).round(1)
        grp = grp[grp["TOTAL"]>50].sort_values("PCT")
        cores = [CORES_EMPRESA.get(e, COR_ACENTO) for e in grp["EMPRESA"]]
        fig_emp = go.Figure(go.Bar(
            x=grp["EMPRESA"], y=grp["PCT"], marker_color=cores,
            text=grp["PCT"].apply(lambda v:f"{v}%"), textposition="outside",
        ))
        fig_emp.update_layout(title="Taxa de Atraso por Companhia (%)", **layout_base(),
                              xaxis_title="Companhia", yaxis_title="% Atrasados")
    else:
        fig_emp = go.Figure()

    if "PARTIDA_PREV" in dff.columns and "ATRASO_MIN" in dff.columns:
        dff2 = dff.dropna(subset=["PARTIDA_PREV"]).copy()
        dff2["HORA"] = pd.to_datetime(dff2["PARTIDA_PREV"], errors="coerce").dt.hour
        grp_h = dff2.groupby("HORA").agg(MED=("ATRASO_MIN","mean")).reset_index().dropna()
        fig_hora = px.line(grp_h, x="HORA", y="MED", markers=True,
                           title="Atraso Médio por Hora de Partida",
                           labels={"HORA":"Hora","MED":"Atraso Médio (min)"},
                           color_discrete_sequence=[COR_DESTAQUE])
        fig_hora.update_layout(**layout_base())
    else:
        fig_hora = go.Figure()

    if "MES" in dff.columns and "CANCELADO" in dff.columns:
        grp_c = dff.groupby("MES").agg(
            TOTAL=("MES","count"), CANC=("CANCELADO","sum")).reset_index()
        grp_c["PCT"] = (grp_c["CANC"]/grp_c["TOTAL"]*100).round(2)
        grp_c["MES_NOME"] = grp_c["MES"].map(MESES_NOME)
        fig_canc = px.bar(grp_c, x="MES_NOME", y="PCT",
                          title="Taxa de Cancelamento por Mês (%)",
                          labels={"MES_NOME":"Mês","PCT":"% Cancelados"},
                          color="PCT",
                          color_continuous_scale=[[0,"#FFEAA7"],[1,COR_DESTAQUE]])
        fig_canc.update_layout(**layout_base())
        fig_canc.update_coloraxes(showscale=False)
    else:
        fig_canc = go.Figure()

    return fig_hist, fig_emp, fig_hora, fig_canc


@app.callback(
    [Output("graf-tarifa-emp","figure"),
     Output("graf-tarifa-mes","figure"),
     Output("graf-tarifa-rota","figure")],
    [Input("filtro-anos","value"),
     Input("filtro-empresas","value"),
     Input("filtro-regioes","value"),
     Input("filtro-tipo","value"),
     Input("filtro-atrasado","value")],
)
def atualizar_tarifas(anos, empresas, regioes, tipo, atrasado):
    """Atualiza graficos da aba Tarifas."""
    dff = filtrar(anos, empresas, regioes, tipo, atrasado)

    if "TARIFA_MEDIA" not in dff.columns or dff["TARIFA_MEDIA"].isna().all():
        fig_vz = go.Figure().update_layout(
            title="Dados de Tarifas não disponíveis no filtro atual",
            **layout_base())
        return fig_vz, fig_vz, fig_vz

    dff_t = dff.dropna(subset=["TARIFA_MEDIA"])

    if "EMPRESA" in dff_t.columns:
        cores = [CORES_EMPRESA.get(e, COR_ACENTO) for e in dff_t["EMPRESA"].unique()]
        fig_box = px.box(dff_t, x="EMPRESA", y="TARIFA_MEDIA",
                         title="Distribuição de Tarifas por Companhia",
                         labels={"EMPRESA":"Companhia","TARIFA_MEDIA":"Tarifa Média (R$)"},
                         color="EMPRESA",
                         color_discrete_map=CORES_EMPRESA)
        fig_box.update_layout(**layout_base())
        fig_box.update_traces(showlegend=False)
    else:
        fig_box = go.Figure()

    if "MES" in dff_t.columns:
        grp = dff_t.groupby("MES")["TARIFA_MEDIA"].mean().reset_index()
        grp["MES_NOME"] = grp["MES"].map(MESES_NOME)
        fig_mes = px.line(grp, x="MES_NOME", y="TARIFA_MEDIA", markers=True,
                          title="Tarifa Média por Mês",
                          labels={"MES_NOME":"Mês","TARIFA_MEDIA":"R$"},
                          color_discrete_sequence=[COR_VERDE])
        fig_mes.update_layout(**layout_base())
        fig_mes.add_hline(y=grp["TARIFA_MEDIA"].mean(), line_dash="dash",
                          line_color="#999", annotation_text="Média geral")
    else:
        fig_mes = go.Figure()

    if "ROTA" in dff_t.columns:
        grp_r = dff_t.groupby("ROTA").agg(
            TARIFA=("TARIFA_MEDIA","mean"),
            VOOS=("ROTA","count"),
        ).reset_index().nlargest(40, "VOOS")
        fig_scatter = px.scatter(
            grp_r, x="VOOS", y="TARIFA", text="ROTA", size="VOOS",
            title="Top 40 Rotas: Tarifa Média vs Volume de Voos",
            labels={"VOOS":"Nº de Voos","TARIFA":"Tarifa Média (R$)"},
            color="TARIFA",
            color_continuous_scale=[[0,COR_VERDE],[0.5,COR_ACENTO],[1,COR_DESTAQUE]],
        )
        fig_scatter.update_traces(textposition="top center", textfont_size=9)
        fig_scatter.update_layout(**layout_base(360))
    else:
        fig_scatter = go.Figure()

    return fig_box, fig_mes, fig_scatter


@app.callback(
    Output("graf-comparativo","figure"),
    [Input("filtro-anos","value"),
     Input("filtro-empresas","value"),
     Input("filtro-regioes","value"),
     Input("filtro-tipo","value"),
     Input("filtro-atrasado","value"),
     Input("comp-eixo-x","value"),
     Input("comp-metrica","value"),
     Input("comp-cor","value")],
)
def atualizar_comp(anos, empresas, regioes, tipo, atrasado, eixo_x, metrica, cor):
    """Atualiza grafico comparativo conforme selecao."""
    dff = filtrar(anos, empresas, regioes, tipo, atrasado)

    if eixo_x not in dff.columns:
        return go.Figure()

    cor_col = None if cor == "none" or cor not in dff.columns else cor

    grp_cols = [eixo_x] + ([cor_col] if cor_col else [])

    def calc_metrica(g):
        if metrica == "n_voos":
            return len(g)
        elif metrica == "pct_atraso" and "ATRASADO" in g.columns:
            return g["ATRASADO"].mean() * 100
        elif metrica == "pct_canc" and "CANCELADO" in g.columns:
            return g["CANCELADO"].mean() * 100
        elif metrica == "med_atraso" and "ATRASO_MIN" in g.columns:
            return g["ATRASO_MIN"].mean()
        elif metrica == "tarifa_media" and "TARIFA_MEDIA" in g.columns:
            return g["TARIFA_MEDIA"].mean()
        return np.nan

    grp = dff.groupby(grp_cols, dropna=False).apply(calc_metrica).reset_index(name="VALOR")
    grp = grp.dropna(subset=["VALOR"])

    if eixo_x == "MES":
        grp[eixo_x] = grp[eixo_x].map(MESES_NOME).fillna(grp[eixo_x].astype(str))

    labels = {
        "n_voos":"Nº de Voos", "pct_atraso":"Taxa de Atraso (%)",
        "pct_canc":"Taxa de Cancelam. (%)", "med_atraso":"Atraso Médio (min)",
        "tarifa_media":"Tarifa Média (R$)",
    }
    titulo = f"{labels.get(metrica, metrica)} por {eixo_x}"
    if cor_col:
        titulo += f" (separado por {cor_col})"

    if cor_col:
        fig = px.bar(grp, x=eixo_x, y="VALOR", color=cor_col, barmode="group",
                     title=titulo, color_discrete_sequence=SEQ_CORES,
                     labels={"VALOR": labels.get(metrica, "Valor")})
    else:
        fig = px.bar(grp.sort_values("VALOR", ascending=False),
                     x=eixo_x, y="VALOR", title=titulo,
                     color="VALOR",
                     color_continuous_scale=[[0,"#BDD7EE"],[1,COR_PRIMARIA]],
                     labels={"VALOR": labels.get(metrica, "Valor")})
        fig.update_coloraxes(showscale=False)

    fig.update_layout(**layout_base(420))
    return fig


@app.callback(
    Output("tabela-dados","children"),
    [Input("filtro-anos","value"),
     Input("filtro-empresas","value"),
     Input("filtro-regioes","value"),
     Input("filtro-tipo","value"),
     Input("filtro-atrasado","value"),
     Input("tabela-cols","value")],
)
def atualizar_tabela(anos, empresas, regioes, tipo, atrasado, cols):
    """Atualiza a tabela com as colunas selecionadas."""
    dff = filtrar(anos, empresas, regioes, tipo, atrasado)
    cols_val = [c for c in (cols or []) if c in dff.columns]
    if not cols_val:
        cols_val = dff.columns[:8].tolist()

    amostra = dff[cols_val].head(500)

    return dash_table.DataTable(
        data=amostra.to_dict("records"),
        columns=[{"name":c,"id":c} for c in cols_val],
        page_size=20,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX":"auto","borderRadius":"8px","overflow":"hidden"},
        style_header={
            "backgroundColor":COR_PRIMARIA,"color":"white",
            "fontWeight":"700","fontSize":"12px","border":"none",
        },
        style_cell={
            "fontSize":"12px","padding":"8px 12px","border":"1px solid #EEE",
            "textAlign":"left","maxWidth":"200px","overflow":"hidden","textOverflow":"ellipsis",
        },
        style_data_conditional=[
            {"if":{"row_index":"odd"},"backgroundColor":"#F8FAFD"},
        ],
        tooltip_data=[{c:{"value":str(row.get(c,"")),"type":"markdown"} for c in cols_val} for row in amostra.to_dict("records")],
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
        body { font-family: 'Montserrat','Segoe UI',sans-serif; margin:0; background:#F0F4F8; }

        /* SIDEBAR */
        .sidebar {
            width: 240px; min-width: 240px; background: #0A2342;
            color: white; padding: 20px 16px; overflow-y: auto;
            box-shadow: 4px 0 16px rgba(0,0,0,0.2);
            position: sticky; top: 0; height: 100vh;
        }
        .sidebar-title { font-size:.95rem; font-weight:800; display:flex; align-items:center; gap:8px; margin-bottom:12px; }
        .sidebar-hr  { border-color: rgba(255,255,255,0.15); margin: 12px 0; }
        .filter-label { font-size:.7rem; font-weight:700; text-transform:uppercase;
                        letter-spacing:.06em; color:#90CAF9; display:block; margin-bottom:6px; }
        .custom-check label { font-size:.8rem; color:rgba(255,255,255,.85); }
        .custom-check input { accent-color:#2196F3; }
        .contador-box { margin-top:8px; }

        /* CONTEÚDO */
        .conteudo { flex:1; padding: 20px; overflow-y:auto; }

        /* CARDS */
        .shadow-card {
            border:none !important; border-radius:12px !important;
            box-shadow:0 2px 8px rgba(0,0,0,.07) !important;
            background:white !important;
        }
        .card-header-custom {
            background: linear-gradient(90deg, #0A2342 0%, #1565C0 100%);
            color:white; font-weight:700; font-size:.85rem;
            border-radius:12px 12px 0 0 !important; padding:10px 16px;
        }

        /* TABS */
        .nav-tabs .nav-link { font-size:.85rem; font-weight:600; color:#555; border:none; }
        .nav-tabs .nav-link.active { color:#0A2342; border-bottom:3px solid #2196F3; background:none; }
        .nav-tabs { border-bottom:2px solid #E0E0E0; margin-bottom:16px; }

        /* SCROLLBAR */
        ::-webkit-scrollbar { width:6px; }
        ::-webkit-scrollbar-track { background:#F0F4F8; }
        ::-webkit-scrollbar-thumb { background:#AABBCC; border-radius:3px; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
"""

if __name__ == "__main__":
    print("\n  ✈  Dashboard 2 — Exploração Interativa")
    print("  Acesse: http://localhost:8051\n")
    app.run(debug=False, port=8051)
