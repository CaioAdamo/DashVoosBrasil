"""
lib_dados.py  —  Camada de Engenharia de Dados dos Dashboards
================================================================

Centraliza TODO o trabalho pesado de dados para que os dashboards fiquem
rápidos, consistentes e fáceis de manter:

  1.  Carregamento veloz via cache **Parquet** (10x mais rápido que reparsear
      o CSV de ~1 GB a cada inicialização).
  2.  **Enriquecimento analítico**: nomes de companhias, grupos econômicos,
      fabricante/família da aeronave, código IATA, distância (haversine),
      atraso na chegada, recuperação em voo, faixa horária, ASK (oferta de
      assentos-km), fluxo regional, etc.
  3.  **Integração das tarifas** (ANAC) resolvendo o descasamento ICAO×IATA.
  4.  **Tema visual** e utilitários de formatação pt-BR compartilhados.

Pode ser executado isolado para (re)construir o cache:
    python lib_dados.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

# Mapeamentos geográficos são a fonte única da verdade — reaproveitados da
# etapa de preparação para não duplicar conhecimento de domínio.
from prepara_dados import COORDENADAS, ICAO_POR_IATA, REGIAO_UF

PASTA_PROC   = Path("dados_processados")
ARQ_CSV      = PASTA_PROC / "dataset_final.csv"
ARQ_PARQUET  = PASTA_PROC / "dataset_analitico.parquet"
ARQ_TARIFAS  = PASTA_PROC / "tarifas_limpo.csv"

# Versão do schema analítico. Mudou a lógica de enriquecimento? Incremente
# para invalidar o cache automaticamente.
VERSAO_BASE = 5

# ───────────────────────────── DICIONÁRIOS DE DOMÍNIO ──────────────────────────

# Código ICAO da empresa → nome comercial
EMPRESAS = {
    "AZU": "Azul",
    "TAM": "LATAM",
    "GLO": "Gol",
    "ACN": "Azul Conecta",
    "PTB": "Voepass",
    "PAM": "MAP",
    "ARG": "Aerolíneas Argentinas",
    "TAP": "TAP Portugal",
    "CMP": "Copa Airlines",
    "AVA": "Avianca",
    "LAN": "LATAM (LA)",
    "QTR": "Qatar Airways",
    "AAL": "American Airlines",
    "SID": "Sideral (cargo)",
    "SKU": "Sky Airline",
    "ETH": "Ethiopian",
    "UAL": "United",
    "DAL": "Delta",
    "AFR": "Air France",
    "KLM": "KLM",
    "DLH": "Lufthansa",
    "BAW": "British Airways",
    "IBE": "Iberia",
    "ABJ": "Abaeté",
    "TTL": "Total (cargo)",
    "AZN": "Azul (AZN)",
    "ONE": "Boliviana",
    "GLG": "Gol (cargo)",
}

# Grupos econômicos / blocos competitivos
GRUPO_EMPRESA = {
    "AZU": "Azul",       "ACN": "Azul",       "AZN": "Azul",
    "TAM": "LATAM",      "LAN": "LATAM",
    "GLO": "Gol",        "GLG": "Gol",
    "PTB": "Regionais",  "PAM": "Regionais",  "ABJ": "Regionais",  "SID": "Cargueiras",
    "TTL": "Cargueiras",
}
def _grupo(emp):
    if emp in GRUPO_EMPRESA:
        return GRUPO_EMPRESA[emp]
    return "Internacionais"

# Modelo (ICAO da aeronave) → (fabricante, família comercial)
AERONAVES = {
    "A320": ("Airbus", "A320ceo"), "A319": ("Airbus", "A320ceo"), "A321": ("Airbus", "A320ceo"),
    "A318": ("Airbus", "A320ceo"),
    "A20N": ("Airbus", "A320neo"), "A21N": ("Airbus", "A320neo"), "A19N": ("Airbus", "A320neo"),
    "A332": ("Airbus", "A330"),    "A333": ("Airbus", "A330"),    "A339": ("Airbus", "A330neo"),
    "A338": ("Airbus", "A330neo"),
    "B737": ("Boeing", "737 NG"),  "B738": ("Boeing", "737 NG"),  "B739": ("Boeing", "737 NG"),
    "B38M": ("Boeing", "737 MAX"), "B39M": ("Boeing", "737 MAX"),
    "B763": ("Boeing", "767"),     "B762": ("Boeing", "767"),
    "B788": ("Boeing", "787"),     "B789": ("Boeing", "787"),     "B78X": ("Boeing", "787"),
    "B77W": ("Boeing", "777"),     "B772": ("Boeing", "777"),     "B77L": ("Boeing", "777"),
    "B744": ("Boeing", "747"),
    "E195": ("Embraer", "E-Jet"),  "E190": ("Embraer", "E-Jet"),  "E175": ("Embraer", "E-Jet"),
    "E170": ("Embraer", "E-Jet"),
    "E295": ("Embraer", "E2"),     "E290": ("Embraer", "E2"),
    "AT76": ("ATR", "ATR 72"),     "AT75": ("ATR", "ATR 72"),     "AT72": ("ATR", "ATR 72"),
    "AT45": ("ATR", "ATR 42"),     "AT46": ("ATR", "ATR 42"),     "AT44": ("ATR", "ATR 42"),
    "C208": ("Cessna", "Caravan"), "C208B": ("Cessna", "Caravan"),
    "C68A": ("Cessna", "Executivo"),
    "DH8D": ("De Havilland", "Dash 8"), "DH8C": ("De Havilland", "Dash 8"),
}
AERON_FABRICANTE = {m: v[0] for m, v in AERONAVES.items()}
AERON_FAMILIA    = {m: v[1] for m, v in AERONAVES.items()}

# Tipo de linha ANAC → segmento legível
TIPO_LINHA_NOME = {
    "N": "Doméstico", "I": "Internacional", "G": "Intl. cargueiro",
    "C": "Cargueiro doméstico", "X": "Outros", "R": "Regional", "H": "Subsidiada",
    "E": "Especial", "L": "Internacional",
}

# Dia da semana inglês → pt-BR (mantém ordem semanal)
DIA_SEM_PT = {
    "Monday": "Seg", "Tuesday": "Ter", "Wednesday": "Qua", "Thursday": "Qui",
    "Friday": "Sex", "Saturday": "Sáb", "Sunday": "Dom",
}
ORDEM_DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

MESES_PT = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
            7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
ORDEM_MESES = list(MESES_PT.values())

FAIXAS_HORARIAS = ["Madrugada", "Manhã", "Tarde", "Noite"]

# IATA → metadados (cidade/UF) e códigos derivados
ICAO2IATA = {icao: iata for iata, icao in ICAO_POR_IATA.items()}
IATA_CIDADE = {iata: COORDENADAS[iata][2] for iata in COORDENADAS}
ICAO_CIDADE = {icao: COORDENADAS[iata][2] for iata, icao in ICAO_POR_IATA.items()}

# Ano com cobertura parcial (apenas alguns meses coletados)
ANO_PARCIAL = 2025

# ───────────────────────────────── TEMA VISUAL ────────────────────────────────

class T:
    """Paleta e tokens de design compartilhados pelos dois dashboards."""
    PRIMARIA   = "#0A2342"   # navy
    PRIMARIA_2 = "#1565C0"   # azul institucional (gradiente)
    ACENTO     = "#2196F3"   # azul claro
    DESTAQUE   = "#E8563A"   # coral (atenção)
    VERDE      = "#1FA37C"   # positivo
    AMBAR      = "#F2A900"   # alerta suave
    ROXO       = "#7E57C2"
    CIANO      = "#00ACC1"
    BG         = "#EEF2F7"
    CARD       = "#FFFFFF"
    TEXTO      = "#1A2332"
    TEXTO_SUAVE= "#5B6B7F"
    GRID       = "#E7EDF4"
    BORDA      = "#D9E2EC"

# Cores por grupo econômico (consistência entre gráficos)
CORES_GRUPO = {
    "Azul": "#0057A8", "LATAM": "#C8102E", "Gol": "#FF6900",
    "Regionais": "#1FA37C", "Cargueiras": "#5B6B7F", "Internacionais": "#7E57C2",
}
CORES_FABRICANTE = {
    "Airbus": "#0057A8", "Boeing": "#1FA37C", "Embraer": "#E8563A",
    "ATR": "#F2A900", "Cessna": "#7E57C2", "De Havilland": "#00ACC1", "Outros": "#9AA8B8",
}
CORES_REGIAO = {
    "Sudeste": "#1565C0", "Nordeste": "#E8563A", "Sul": "#1FA37C",
    "Centro-Oeste": "#F2A900", "Norte": "#7E57C2", "Exterior": "#5B6B7F",
}
SEQ_CORES = [T.PRIMARIA, T.ACENTO, T.DESTAQUE, T.VERDE, T.ROXO, T.AMBAR, T.CIANO, "#607D8B"]
ESCALA_AZUL = [[0.0, "#EAF2FB"], [0.5, T.ACENTO], [1.0, T.PRIMARIA]]
ESCALA_CALOR = [[0.0, "#FFF3E0"], [0.45, T.AMBAR], [1.0, T.DESTAQUE]]


def layout_base(altura=None, **kw):
    """Layout Plotly padrão (claro, limpo, tipografia consistente)."""
    base = dict(
        template="plotly_white",
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        colorway=SEQ_CORES,
        font=dict(family="Inter, 'Segoe UI', Arial, sans-serif", color=T.TEXTO, size=12),
        title_font=dict(size=15, color=T.PRIMARIA, family="Inter, 'Segoe UI', sans-serif"),
        title_x=0.01, title_xanchor="left",
        margin=dict(l=30, r=22, t=56, b=38),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=T.BORDA, font_size=12, font_color=T.TEXTO),
        legend=dict(font=dict(size=11)),
        xaxis=dict(showgrid=False, zeroline=False, linecolor=T.BORDA, tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor=T.GRID, zeroline=False, tickfont=dict(size=11)),
    )
    if altura:
        base["height"] = altura
    base.update(kw)
    return base


def fig_vazia(msg="Sem dados para os filtros selecionados"):
    """Figura placeholder amigável quando o recorte fica vazio."""
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_annotation(text=f"🔍 {msg}", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=14, color=T.TEXTO_SUAVE))
    fig.update_layout(layout_base(), xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig


# ───────────────────────────── FORMATAÇÃO pt-BR ──────────────────────────────

def fmt(n, casas=0):
    """Formata número no padrão brasileiro (1.234.567,8)."""
    try:
        if pd.isna(n):
            return "—"
    except (TypeError, ValueError):
        pass
    s = f"{n:,.{casas}f}"
    return s.replace(",", "·").replace(".", ",").replace("·", ".")


def fmt_compacto(n):
    """Abrevia grandes números: 1.2 mi, 845 mil."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "—"
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f} bi".replace(".", ",")
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f} mi".replace(".", ",")
    if abs(n) >= 1_000:
        return f"{n/1_000:.0f} mil"
    return fmt(n)


def fmt_reais(v, casas=0):
    """Formata valor monetário em reais."""
    if pd.isna(v):
        return "—"
    return "R$ " + fmt(v, casas)


# ────────────────────────────── HAVERSINE / DISTÂNCIA ─────────────────────────

def _haversine(lat1, lon1, lat2, lon2):
    """Distância em km entre pares de coordenadas (vetorizado, NaN-safe)."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(lambda x: np.radians(x.astype(float)), (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# ───────────────────────────────── ENRIQUECIMENTO ─────────────────────────────

# Colunas pesadas e de baixo valor analítico, descartadas no cache.
_DROP_COLS = [
    "DESCRICAO_AEROPORTO_ORIGEM", "DESCRICAO_AEROPORTO_DESTINO",  # mojibake + volumosas
    "JUSTIFICATIVA",                                              # 100% nula
    "REFERENCIA", "MES_NOME",                                     # redundantes
]


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona as variáveis analíticas derivadas ao DataFrame VRA limpo."""
    df = df.drop(columns=[c for c in _DROP_COLS if c in df.columns])

    # Tipagem temporal
    for c in ["PARTIDA_PREV", "PARTIDA_REAL", "CHEGADA_PREV", "CHEGADA_REAL"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    for c in ["ANO", "MES", "TRIMESTRE", "ATRASO_MIN", "NUMERO_DE_ASSENTOS"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["ATRASADO", "CANCELADO"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.lower().isin(["true", "1", "yes"])

    # Companhia e grupo
    df["EMPRESA_NOME"] = df["EMPRESA"].map(EMPRESAS).fillna(df["EMPRESA"])
    df["GRUPO"] = df["EMPRESA"].map(_grupo)

    # Aeronave
    df["FABRICANTE"] = df["MODELO_EQUIPAMENTO"].map(AERON_FABRICANTE).fillna("Outros")
    df["FAMILIA_AERONAVE"] = df["MODELO_EQUIPAMENTO"].map(AERON_FAMILIA).fillna("Outros")

    # Códigos IATA legíveis + rota
    df["ORIGEM_IATA"]  = df["ORIGEM"].map(ICAO2IATA).fillna(df["ORIGEM"])
    df["DESTINO_IATA"] = df["DESTINO"].map(ICAO2IATA).fillna(df["DESTINO"])
    df["ROTA_IATA"]    = df["ORIGEM_IATA"].astype(str) + " → " + df["DESTINO_IATA"].astype(str)
    df["ORIG_CIDADE"]  = df.get("ORIG_CIDADE", df["ORIGEM"].map(ICAO_CIDADE))
    df["DEST_CIDADE"]  = df.get("DEST_CIDADE", df["DESTINO"].map(ICAO_CIDADE))

    # Distância e oferta de assentos-km (ASK)
    if {"ORIG_LAT", "ORIG_LON", "DEST_LAT", "DEST_LON"}.issubset(df.columns):
        df["DIST_KM"] = _haversine(df["ORIG_LAT"], df["ORIG_LON"],
                                   df["DEST_LAT"], df["DEST_LON"]).round(0)
    else:
        df["DIST_KM"] = np.nan
    assentos = df["NUMERO_DE_ASSENTOS"].where(df["NUMERO_DE_ASSENTOS"] > 0)
    df["ASK"] = (assentos * df["DIST_KM"])

    # Atraso na chegada e recuperação em voo (partiu atrasado e chegou no horário?)
    if {"CHEGADA_REAL", "CHEGADA_PREV"}.issubset(df.columns):
        df["ATRASO_CHEGADA_MIN"] = (
            (df["CHEGADA_REAL"] - df["CHEGADA_PREV"]).dt.total_seconds() / 60
        ).round(1)
        df["RECUPERACAO_MIN"] = (df["ATRASO_MIN"] - df["ATRASO_CHEGADA_MIN"]).round(1)

    # Hora e faixa horária da partida prevista
    df["HORA_PARTIDA"] = df["PARTIDA_PREV"].dt.hour
    df["FAIXA_HORARIA"] = pd.cut(
        df["HORA_PARTIDA"], bins=[-1, 5, 11, 17, 23], labels=FAIXAS_HORARIAS
    )

    # Dia da semana em pt-BR (ordenado)
    if "DIA_SEM" in df.columns:
        df["DIA_SEM_PT"] = pd.Categorical(
            df["DIA_SEM"].map(DIA_SEM_PT), categories=ORDEM_DIAS, ordered=True
        )

    # Período (chave temporal mensal) e mês legível
    ano_i = df["ANO"].astype("Int64")
    mes_i = df["MES"].astype("Int64")
    df["PERIODO"] = ano_i.astype(str) + "-" + mes_i.astype(str).str.zfill(2)
    df["MES_PT"] = pd.Categorical(
        df["MES"].map(MESES_PT), categories=ORDEM_MESES, ordered=True
    )

    # Segmento e fluxo regional
    df["SEGMENTO"] = df["TIPO_LINHA"].map(TIPO_LINHA_NOME).fillna("Outros")
    df["DOMESTICO"] = df["TIPO_LINHA"].eq("N")
    orig_r = df.get("ORIG_REGIAO").fillna("Exterior") if "ORIG_REGIAO" in df.columns else "Exterior"
    dest_r = df.get("DEST_REGIAO").fillna("Exterior") if "DEST_REGIAO" in df.columns else "Exterior"
    df["FLUXO_REGIAO"] = orig_r.astype(str) + " → " + dest_r.astype(str)

    # Descarta colunas brutas que já cumpriram seu papel (reduz memória/carga).
    # PARTIDA_PREV é mantida (data de referência usada em métricas e hora).
    lixo = ["NUM_VOO", "COD_DI", "PARTIDA_REAL", "CHEGADA_PREV", "CHEGADA_REAL",
            "SITUACAO_PARTIDA", "SITUACAO_CHEGADA", "DIA_SEM", "ORIG_UF", "DEST_UF"]
    df = df.drop(columns=[c for c in lixo if c in df.columns])

    # Downcast numérico (sem perda relevante de precisão)
    inteiros = {"ANO": "int16", "MES": "int8", "TRIMESTRE": "int8", "NUMERO_DE_ASSENTOS": "int16"}
    for c, tipo in inteiros.items():
        if c in df.columns and df[c].notna().all():
            df[c] = df[c].astype(tipo)
    for c in ["ATRASO_MIN", "ATRASO_CHEGADA_MIN", "RECUPERACAO_MIN", "DIST_KM", "ASK",
              "ORIG_LAT", "ORIG_LON", "DEST_LAT", "DEST_LON", "HORA_PARTIDA"]:
        if c in df.columns:
            df[c] = df[c].astype("float32")

    # PERIODO como categoria ORDENADA (preserva ordem cronológica no eixo X)
    periodos = sorted(df["PERIODO"].dropna().unique())
    df["PERIODO"] = pd.Categorical(df["PERIODO"], categories=periodos, ordered=True)

    # Demais categorias para economizar memória
    for c in ["EMPRESA", "EMPRESA_NOME", "GRUPO", "FABRICANTE", "FAMILIA_AERONAVE",
              "MODELO_EQUIPAMENTO", "ORIGEM", "DESTINO", "ORIGEM_IATA", "DESTINO_IATA",
              "ORIG_CIDADE", "DEST_CIDADE", "ORIG_REGIAO", "DEST_REGIAO", "SEGMENTO",
              "TIPO_LINHA", "SITUACAO", "FAIXA_HORARIA", "FLUXO_REGIAO"]:
        if c in df.columns:
            df[c] = df[c].astype("category")

    return df


# ─────────────────────────────────── CARGA ────────────────────────────────────

def _cache_valido() -> bool:
    if not ARQ_PARQUET.exists():
        return False
    if ARQ_CSV.exists() and ARQ_PARQUET.stat().st_mtime < ARQ_CSV.stat().st_mtime:
        return False
    # valida versão do schema gravada nos metadados
    try:
        import pyarrow.parquet as pq
        meta = pq.read_metadata(ARQ_PARQUET).metadata or {}
        return meta.get(b"versao_base") == str(VERSAO_BASE).encode()
    except Exception:
        return False


def construir_base(verbose=True) -> pd.DataFrame:
    """Lê o CSV bruto, enriquece e grava o cache Parquet otimizado."""
    if not ARQ_CSV.exists():
        # delega à preparação se o dataset ainda não existe
        import subprocess, sys
        if verbose:
            print("dataset_final.csv ausente → executando prepara_dados.py...")
        subprocess.run([sys.executable, "prepara_dados.py"], check=True)

    if verbose:
        print(f"  Lendo {ARQ_CSV.name} (pode levar ~30-60s)...")
    df = pd.read_csv(ARQ_CSV, low_memory=False)
    if verbose:
        print(f"  {len(df):,} linhas. Enriquecendo...")
    df = enriquecer(df)

    if verbose:
        print(f"  Gravando cache → {ARQ_PARQUET.name}")
    import pyarrow as pa
    import pyarrow.parquet as pq
    tabela = pa.Table.from_pandas(df, preserve_index=False)
    tabela = tabela.replace_schema_metadata(
        {**(tabela.schema.metadata or {}), b"versao_base": str(VERSAO_BASE).encode()}
    )
    pq.write_table(tabela, ARQ_PARQUET, compression="zstd")
    if verbose:
        mb = ARQ_PARQUET.stat().st_size / 1e6
        print(f"  Cache pronto ({mb:.0f} MB, {len(df.columns)} colunas).")
    return df


def carregar(force=False, verbose=False) -> pd.DataFrame:
    """Retorna a base analítica. Usa o cache Parquet quando disponível."""
    if force or not _cache_valido():
        return construir_base(verbose=verbose)
    df = pd.read_parquet(ARQ_PARQUET)
    # garante ordenação categórica (parquet pode perder a ordem)
    if "DIA_SEM_PT" in df.columns:
        df["DIA_SEM_PT"] = pd.Categorical(df["DIA_SEM_PT"], categories=ORDEM_DIAS, ordered=True)
    if "MES_PT" in df.columns:
        df["MES_PT"] = pd.Categorical(df["MES_PT"], categories=ORDEM_MESES, ordered=True)
    if "PERIODO" in df.columns and str(df["PERIODO"].dtype) == "category":
        df["PERIODO"] = df["PERIODO"].cat.reorder_categories(
            sorted(df["PERIODO"].cat.categories), ordered=True)
    return df


def carregar_tarifas() -> pd.DataFrame:
    """Carrega e enriquece as tarifas, convertendo IATA→ICAO p/ casar com o VRA."""
    if not ARQ_TARIFAS.exists():
        return pd.DataFrame()
    t = pd.read_csv(ARQ_TARIFAS, low_memory=False)
    t.columns = [c.strip().upper().lstrip("﻿") for c in t.columns]
    for c in ["TARIFA_MEDIA", "ASSENTOS", "PASS_PAGOS", "ANO", "MES"]:
        if c in t.columns:
            t[c] = pd.to_numeric(t[c], errors="coerce")
    t = t.dropna(subset=["TARIFA_MEDIA"])
    # tarifas vêm em IATA; mantemos IATA p/ exibição e criamos ICAO p/ join
    t["ORIGEM_IATA"]  = t["ORIGEM"]
    t["DESTINO_IATA"] = t["DESTINO"]
    t["ORIGEM_ICAO"]  = t["ORIGEM"].map(ICAO_POR_IATA)
    t["DESTINO_ICAO"] = t["DESTINO"].map(ICAO_POR_IATA)
    t["ROTA_IATA"]    = t["ORIGEM"].astype(str) + " → " + t["DESTINO"].astype(str)
    t["EMPRESA_NOME"] = t["EMPRESA"].map(EMPRESAS).fillna(t["EMPRESA"])
    t["GRUPO"]        = t["EMPRESA"].map(_grupo)
    if "PASS_PAGOS" in t.columns and "ASSENTOS" in t.columns:
        t["OCUPACAO"] = (t["PASS_PAGOS"] / t["ASSENTOS"]).clip(upper=1.5)

    # Distância da rota (haversine a partir das coordenadas IATA)
    lat = {i: COORDENADAS[i][0] for i in COORDENADAS}
    lon = {i: COORDENADAS[i][1] for i in COORDENADAS}
    t["DIST_KM"] = _haversine(
        t["ORIGEM"].map(lat), t["ORIGEM"].map(lon),
        t["DESTINO"].map(lat), t["DESTINO"].map(lon)).round(0)
    if "TARIFA_MEDIA" in t.columns:
        t["TARIFA_POR_KM"] = (t["TARIFA_MEDIA"] / t["DIST_KM"]).replace([np.inf, -np.inf], np.nan)

    # Região de origem (para cruzar com filtros geográficos)
    uf = {i: COORDENADAS[i][3] for i in COORDENADAS}
    t["ORIG_REGIAO"] = t["ORIGEM"].map(uf).map(REGIAO_UF)
    return t


# ─────────────────────────────── AGREGAÇÕES ÚTEIS ─────────────────────────────

def mapa_malha(dff: pd.DataFrame, top_rotas=45, titulo=None):
    """Mapa do Brasil com aeroportos (bolhas) e principais ligações (linhas).

    Compartilhado pelos dois dashboards. Exige as colunas de coordenadas e os
    códigos IATA gerados no enriquecimento.
    """
    import plotly.graph_objects as go
    geo = dff.dropna(subset=["ORIG_LAT", "ORIG_LON", "DEST_LAT", "DEST_LON"])
    if geo.empty:
        return fig_vazia("Sem coordenadas no recorte")

    o = geo.groupby(["ORIGEM_IATA", "ORIG_LAT", "ORIG_LON", "ORIG_CIDADE"], observed=True).size()
    d = geo.groupby(["DESTINO_IATA", "DEST_LAT", "DEST_LON", "DEST_CIDADE"], observed=True).size()
    o = o.reset_index(); o.columns = ["IATA", "LAT", "LON", "CIDADE", "N"]
    d = d.reset_index(); d.columns = ["IATA", "LAT", "LON", "CIDADE", "N"]
    aero = (pd.concat([o, d]).groupby(["IATA", "LAT", "LON", "CIDADE"], observed=True)["N"]
            .sum().reset_index().sort_values("N", ascending=False))

    rt = geo.groupby(["ORIGEM_IATA", "DESTINO_IATA", "ORIG_LAT", "ORIG_LON",
                      "DEST_LAT", "DEST_LON"], observed=True).size().reset_index(name="N")
    rt["par"] = rt.apply(lambda r: "-".join(sorted([str(r["ORIGEM_IATA"]), str(r["DESTINO_IATA"])])), axis=1)
    rt = (rt.groupby("par", observed=True)
            .agg(N=("N", "sum"), ORIG_LAT=("ORIG_LAT", "first"), ORIG_LON=("ORIG_LON", "first"),
                 DEST_LAT=("DEST_LAT", "first"), DEST_LON=("DEST_LON", "first"))
            .reset_index().sort_values("N", ascending=False).head(top_rotas))

    fig = go.Figure()
    nmax = rt["N"].max() if len(rt) else 1
    for _, r in rt.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r["ORIG_LON"], r["DEST_LON"]], lat=[r["ORIG_LAT"], r["DEST_LAT"]],
            mode="lines", line=dict(width=0.8 + 6 * (r["N"] / nmax), color="rgba(33,150,243,0.35)"),
            hoverinfo="skip", showlegend=False))

    amax = aero["N"].max() if len(aero) else 1
    fig.add_trace(go.Scattergeo(
        lon=aero["LON"], lat=aero["LAT"], mode="markers",
        marker=dict(size=8 + 34 * np.sqrt(aero["N"] / amax), color=aero["N"],
                    colorscale=ESCALA_AZUL, line=dict(width=0.6, color="white"), opacity=0.92,
                    colorbar=dict(title="Movimentos", thickness=12, len=0.6, x=0.99)),
        text=aero["CIDADE"].astype(str) + " (" + aero["IATA"].astype(str) + ")",
        customdata=aero["N"],
        hovertemplate="<b>%{text}</b><br>%{customdata:,} movimentos<extra></extra>",
        showlegend=False))

    tit = titulo if titulo is not None else f"Malha aérea — aeroportos e {len(rt)} principais ligações"
    fig.update_layout(layout_base(), title=tit,
                      margin=dict(l=0, r=0, t=(20 if tit == "" else 46), b=0))
    fig.update_geos(scope="south america", showcountries=True, countrycolor="#CBD5E1",
                    showland=True, landcolor="#F4F7FB", showocean=True, oceancolor="#EAF2FB",
                    lataxis_range=[-34, 7], lonaxis_range=[-75, -33], bgcolor="rgba(0,0,0,0)",
                    resolution=50)
    return fig


def folga_eixo(fig, vmax, vmin=0, frac=0.20, eixo="x"):
    """Adiciona folga no eixo p/ rótulos 'outside' das barras não serem cortados."""
    try:
        hi = float(vmax) * (1 + frac) if vmax and vmax > 0 else 1
    except (TypeError, ValueError):
        return fig
    if eixo == "x":
        fig.update_xaxes(range=[vmin, hi])
    else:
        fig.update_yaxes(range=[vmin, hi])
    return fig


def taxa_pct(serie_bool) -> float:
    """% de True em uma série booleana (NaN-safe)."""
    if serie_bool is None or len(serie_bool) == 0:
        return 0.0
    v = pd.Series(serie_bool).mean()
    return round(float(v) * 100, 1) if pd.notna(v) else 0.0


def hhi(contagens) -> float:
    """Índice Herfindahl-Hirschman (0-10000) de concentração de mercado."""
    s = pd.Series(contagens).astype(float)
    total = s.sum()
    if total <= 0:
        return 0.0
    shares = s / total * 100
    return float((shares ** 2).sum())


if __name__ == "__main__":
    import time
    t0 = time.time()
    df = construir_base(verbose=True)
    print(f"\n  Resumo da base analítica ({time.time()-t0:.0f}s):")
    print(f"    Linhas .......... {len(df):,}")
    print(f"    Colunas ......... {len(df.columns)}")
    print(f"    Período ......... {int(df['ANO'].min())}–{int(df['ANO'].max())}")
    print(f"    Companhias ...... {df['EMPRESA'].nunique()}")
    print(f"    Aeroportos ...... {df['ORIGEM'].nunique()}")
    print(f"    Rotas distintas . {df['ROTA'].nunique():,}")
    print(f"    Atraso médio .... {df.loc[df['ATRASADO'],'ATRASO_MIN'].mean():.0f} min")
    tar = carregar_tarifas()
    print(f"    Tarifas (linhas)  {len(tar):,}")
