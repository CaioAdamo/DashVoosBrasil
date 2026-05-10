import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

PASTA_BRUTOS     = Path("dados_brutos")
PASTA_PROC       = Path("dados_processados")
PASTA_PROC.mkdir(exist_ok=True)

REGIAO_UF = {
    "AC": "Norte",   "AM": "Norte",   "AP": "Norte",   "PA": "Norte",
    "RO": "Norte",   "RR": "Norte",   "TO": "Norte",
    "AL": "Nordeste","BA": "Nordeste","CE": "Nordeste","MA": "Nordeste",
    "PB": "Nordeste","PE": "Nordeste","PI": "Nordeste","RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste","GO": "Centro-Oeste","MS": "Centro-Oeste","MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul",     "RS": "Sul",     "SC": "Sul",
}

COORDENADAS = {
    "GRU": (-23.4356, -46.4731, "São Paulo", "SP"),
    "CGH": (-23.6261, -46.6564, "São Paulo", "SP"),
    "GIG": (-22.8099, -43.2505, "Rio de Janeiro", "RJ"),
    "SDU": (-22.9105, -43.1631, "Rio de Janeiro", "RJ"),
    "BSB": (-15.8711, -47.9186, "Brasília", "DF"),
    "CNF": (-19.6244, -43.9719, "Belo Horizonte", "MG"),
    "SSA": (-12.9086, -38.3225, "Salvador", "BA"),
    "FOR": (-3.7762,  -38.5326, "Fortaleza", "CE"),
    "REC": (-8.1265,  -34.9233, "Recife", "PE"),
    "MAO": (-3.0386,  -60.0497, "Manaus", "AM"),
    "POA": (-29.9944, -51.1713, "Porto Alegre", "RS"),
    "CWB": (-25.5285, -49.1758, "Curitiba", "PR"),
    "FLN": (-27.6703, -48.5472, "Florianópolis", "SC"),
    "VCP": (-23.0074, -47.1345, "Campinas", "SP"),
    "BEL": (-1.3792,  -48.4763, "Belém", "PA"),
    "THE": (-5.0599,  -42.8235, "Teresina", "PI"),
    "MCZ": (-9.5108,  -35.7916, "Maceió", "AL"),
    "NVT": (-26.8800, -48.6514, "Navegantes", "SC"),
    "CGB": (-15.6529, -56.1166, "Cuiabá", "MT"),
    "CGR": (-20.4687, -54.6725, "Campo Grande", "MS"),
    "SLZ": (-2.5853,  -44.2341, "São Luís", "MA"),
    "NAT": (-5.9113,  -35.2478, "Natal", "RN"),
    "JPA": (-7.1459,  -34.9508, "João Pessoa", "PB"),
    "AJU": (-10.9840, -37.0703, "Aracaju", "SE"),
    "PMW": (-10.2917, -48.3567, "Palmas", "TO"),
    "PVH": (-8.7093,  -63.9023, "Porto Velho", "RO"),
    "MCP": (0.0506,   -51.0722, "Macapá", "AP"),
    "BVB": (2.8414,   -60.6922, "Boa Vista", "RR"),
    "RBR": (-9.8688,  -67.8981, "Rio Branco", "AC"),
    "GYN": (-16.6320, -49.2207, "Goiânia", "GO"),
}


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê um CSV tentando separadores e encodings comuns."""
    for enc in ["utf-8-sig", "latin-1", "utf-8"]:
        for sep in [",", ";"]:
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=enc, dtype=str, low_memory=False)
                if len(df.columns) > 1:
                    print(f"  Lido: {caminho.name}  ({len(df):,} linhas, {len(df.columns)} colunas)")
                    return df
            except Exception:
                continue
    raise ValueError(f"Não foi possível ler {caminho}")


def limpar_vra(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e padroniza dados VRA."""
    print("\n  [VRA] Iniciando limpeza...")
    original = len(df)

    df.columns = (
        df.columns.str.strip()
                  .str.upper()
                  .str.replace(" ", "_")
                  .str.replace(r"[^\w]", "_", regex=True)
    )

    renomear = {
        "ICAO_EMPRESA_AEREA":    "EMPRESA",
        "NUMERO_VOO":            "NUM_VOO",
        "CODIGO_DI":             "COD_DI",
        "CODIGO_TIPO_LINHA":     "TIPO_LINHA",
        "ICAO_AERODROMO_ORIGEM": "ORIGEM",
        "ICAO_AERODROMO_DESTINO":"DESTINO",
        "PARTIDA_PREVISTA":      "PARTIDA_PREV",
        "PARTIDA_REAL":          "PARTIDA_REAL",
        "CHEGADA_PREVISTA":      "CHEGADA_PREV",
        "CHEGADA_REAL":          "CHEGADA_REAL",
        "SITUACAO_VOO":          "SITUACAO",
        "CODIGO_JUSTIFICATIVA":  "JUSTIFICATIVA",
        "EMPRESA_AEREA":         "EMPRESA",
        "AERODROMO_ORIGEM":      "ORIGEM",
        "AERODROMO_DESTINO":     "DESTINO",
    }
    df = df.rename(columns={k: v for k, v in renomear.items() if k in df.columns})

    cols_req = ["EMPRESA", "ORIGEM", "DESTINO", "PARTIDA_PREV"]
    faltando = [c for c in cols_req if c not in df.columns]
    if faltando:
        print(f"  AVISO: colunas não encontradas: {faltando}")
        print(f"  Colunas disponíveis: {list(df.columns)}")

    df = df.dropna(how="all")

    for col in ["PARTIDA_PREV", "PARTIDA_REAL", "CHEGADA_PREV", "CHEGADA_REAL"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    if "PARTIDA_PREV" in df.columns:
        df["ANO"]      = df["PARTIDA_PREV"].dt.year
        df["MES"]      = df["PARTIDA_PREV"].dt.month
        df["MES_NOME"] = df["PARTIDA_PREV"].dt.strftime("%b")
        df["DIA_SEM"]  = df["PARTIDA_PREV"].dt.day_name()
        df["TRIMESTRE"]= df["PARTIDA_PREV"].dt.quarter

        df = df[df["ANO"].between(2020, 2025)]

    for col in ["ORIGEM", "DESTINO", "EMPRESA"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.upper()

    for col in ["ORIGEM", "DESTINO"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: x[2:] if isinstance(x, str) and x.startswith("SB") and len(x) == 4 else x
            )

    if "PARTIDA_REAL" in df.columns and "PARTIDA_PREV" in df.columns:
        df["ATRASO_MIN"] = (
            (df["PARTIDA_REAL"] - df["PARTIDA_PREV"])
            .dt.total_seconds()
            .div(60)
            .round(1)
        )
        df["ATRASADO"] = df["ATRASO_MIN"] > 15

    if "SITUACAO" in df.columns:
        df["SITUACAO"] = df["SITUACAO"].str.strip().str.upper()
        df["CANCELADO"] = df["SITUACAO"].str.contains("CANCEL", na=False)

    if "ORIGEM" in df.columns and "DESTINO" in df.columns:
        df["ROTA"] = df["ORIGEM"] + "-" + df["DESTINO"]

    for prefix, col in [("ORIG", "ORIGEM"), ("DEST", "DESTINO")]:
        if col in df.columns:
            df[f"{prefix}_LAT"]    = df[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[0])
            df[f"{prefix}_LON"]    = df[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[1])
            df[f"{prefix}_CIDADE"] = df[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[2])
            df[f"{prefix}_UF"]     = df[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[3])
            df[f"{prefix}_REGIAO"] = df[f"{prefix}_UF"].map(REGIAO_UF)

    antes = len(df)
    chave_dup = [c for c in ["EMPRESA", "NUM_VOO", "PARTIDA_PREV", "ORIGEM", "DESTINO"]
                 if c in df.columns]
    if chave_dup:
        df = df.drop_duplicates(subset=chave_dup)
    print(f"  Duplicatas removidas: {antes - len(df):,}")

    print(f"  Limpeza VRA: {original:,} → {len(df):,} linhas")
    return df.reset_index(drop=True)


def limpar_tarifas(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e padroniza dados de tarifas."""
    print("\n  [TARIFAS] Iniciando limpeza...")
    original = len(df)

    df.columns = (
        df.columns.str.strip()
                  .str.upper()
                  .str.replace(" ", "_")
                  .str.replace(r"[^\w]", "_", regex=True)
    )

    renomear = {
        "EMPRESA":                "EMPRESA",
        "ORIGEM_SIGLA":           "ORIGEM",
        "DESTINO_SIGLA":          "DESTINO",
        "ANO":                    "ANO",
        "MES":                    "MES",
        "TARIFA_MEDIA":           "TARIFA_MEDIA",
        "ASSENTOS":               "ASSENTOS",
        "PASSAGEIROS_PAGOS":      "PASS_PAGOS",
        "BAGAGEM":                "BAGAGEM",
        "TARIFA":                 "TARIFA_MEDIA",
        "AERODROMO_ORIGEM":       "ORIGEM",
        "AERODROMO_DESTINO":      "DESTINO",
    }
    df = df.rename(columns={k: v for k, v in renomear.items() if k in df.columns})

    df = df.dropna(how="all")

    for col in ["TARIFA_MEDIA", "ASSENTOS", "PASS_PAGOS"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                       .str.replace(",", ".", regex=False)
                       .str.replace(r"[^\d\.]", "", regex=True)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "TARIFA_MEDIA" in df.columns:
        df = df[df["TARIFA_MEDIA"].between(50, 10000) | df["TARIFA_MEDIA"].isna()]

    for col in ["ORIGEM", "DESTINO", "EMPRESA"]:
        if col in df.columns:
            df[col] = df[col].str.strip().str.upper()

    if "ORIGEM" in df.columns and "DESTINO" in df.columns:
        df["ROTA"] = df["ORIGEM"] + "-" + df["DESTINO"]

    print(f"  Limpeza Tarifas: {original:,} → {len(df):,} linhas")
    return df.reset_index(drop=True)


def integrar(df_vra: pd.DataFrame, df_tar: pd.DataFrame) -> pd.DataFrame:
    """Integra VRA e tarifas por chaves comuns."""
    print("\n  [INTEGRAÇÃO] Fazendo merge VRA × Tarifas...")

    if df_tar.empty or df_vra.empty:
        print("  AVISO: um dos DataFrames está vazio, pulando merge")
        return df_vra

    chaves = [c for c in ["EMPRESA", "ORIGEM", "DESTINO", "ANO", "MES"]
              if c in df_vra.columns and c in df_tar.columns]

    if not chaves:
        print("  AVISO: sem chaves comuns para merge")
        return df_vra

    cols_tar = chaves + [c for c in ["TARIFA_MEDIA", "ASSENTOS", "PASS_PAGOS"]
                         if c in df_tar.columns]

    df_tar_grp = (
        df_tar[cols_tar]
        .groupby([c for c in chaves if c != "MES"] + (["MES"] if "MES" in chaves else []),
                 as_index=False)
        .agg({c: "mean" for c in cols_tar if c not in chaves})
    )

    merged = df_vra.merge(df_tar_grp, on=chaves, how="left")
    print(f"  Merge concluído: {len(merged):,} linhas")
    return merged


def gerar_dados_simulados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Gera dados simulados para desenvolvimento."""
    print("\n  [SIMULAÇÃO] Gerando dados sintéticos realistas...")
    np.random.seed(42)

    empresas  = ["GLO", "TAM", "AZU", "VBL", "PAM"]
    pesos_emp = [0.35, 0.30, 0.25, 0.07, 0.03]

    aeroportos = list(COORDENADAS.keys())
    hubs = ["GRU", "CGH", "BSB", "GIG", "CNF", "SSA", "FOR", "REC"]

    datas = pd.date_range("2022-01-01", "2024-12-31", freq="h")
    n = 80_000

    idx = np.random.choice(len(datas), n, replace=True)
    partida_prev = datas[idx]

    origens  = np.random.choice(aeroportos, n, p=None)
    destinos = np.random.choice(aeroportos, n, p=None)
    mask = origens == destinos
    destinos[mask] = np.random.choice(
        [a for a in aeroportos if a != "GRU"], mask.sum()
    )

    atraso_base = np.random.exponential(20, n)
    atraso_base[atraso_base > 300] = 300
    atraso_min = np.where(np.random.random(n) < 0.35, atraso_base, 0)

    partida_real = pd.to_datetime(partida_prev) + pd.to_timedelta(atraso_min, unit="m")

    cancelado = np.random.random(n) < 0.03
    situacao  = np.where(cancelado, "CANCELADO", "REALIZADO")

    mes = pd.to_datetime(partida_prev).month
    fator_saz = 1 + 0.3 * np.sin((mes - 1) * np.pi / 6)

    df_vra = pd.DataFrame({
        "EMPRESA":       np.random.choice(empresas, n, p=pesos_emp),
        "NUM_VOO":       [f"{np.random.randint(1000,9999)}" for _ in range(n)],
        "ORIGEM":        origens,
        "DESTINO":       destinos,
        "PARTIDA_PREV":  partida_prev,
        "PARTIDA_REAL":  partida_real,
        "CHEGADA_PREV":  pd.to_datetime(partida_prev) + pd.to_timedelta(
                             np.random.uniform(60, 240, n), unit="m"),
        "SITUACAO":      situacao,
        "TIPO_LINHA":    np.random.choice(["N", "I"], n, p=[0.85, 0.15]),
    })

    df_vra["ANO"]       = pd.to_datetime(df_vra["PARTIDA_PREV"]).dt.year
    df_vra["MES"]       = pd.to_datetime(df_vra["PARTIDA_PREV"]).dt.month
    df_vra["MES_NOME"]  = pd.to_datetime(df_vra["PARTIDA_PREV"]).dt.strftime("%b")
    df_vra["TRIMESTRE"] = pd.to_datetime(df_vra["PARTIDA_PREV"]).dt.quarter
    df_vra["DIA_SEM"]   = pd.to_datetime(df_vra["PARTIDA_PREV"]).dt.day_name()
    df_vra["ATRASO_MIN"]= atraso_min.round(1)
    df_vra["ATRASADO"]  = atraso_min > 15
    df_vra["CANCELADO"] = cancelado
    df_vra["ROTA"]      = df_vra["ORIGEM"] + "-" + df_vra["DESTINO"]

    for prefix, col in [("ORIG", "ORIGEM"), ("DEST", "DESTINO")]:
        df_vra[f"{prefix}_LAT"]    = df_vra[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[0])
        df_vra[f"{prefix}_LON"]    = df_vra[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[1])
        df_vra[f"{prefix}_CIDADE"] = df_vra[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[2])
        df_vra[f"{prefix}_UF"]     = df_vra[col].map(lambda x: COORDENADAS.get(x, (None,)*4)[3])
        df_vra[f"{prefix}_REGIAO"] = df_vra[f"{prefix}_UF"].map(REGIAO_UF)

    n_tar = 30_000
    df_tar = pd.DataFrame({
        "EMPRESA":      np.random.choice(empresas, n_tar, p=pesos_emp),
        "ORIGEM":       np.random.choice(aeroportos, n_tar),
        "DESTINO":      np.random.choice(aeroportos, n_tar),
        "ANO":          np.random.choice([2022, 2023, 2024], n_tar),
        "MES":          np.random.randint(1, 13, n_tar),
        "TARIFA_MEDIA": (np.random.lognormal(6.2, 0.5, n_tar) * fator_saz[:n_tar]).round(2),
        "ASSENTOS":     np.random.randint(100, 200, n_tar),
        "PASS_PAGOS":   np.random.randint(50, 190, n_tar),
    })
    df_tar["ROTA"] = df_tar["ORIGEM"] + "-" + df_tar["DESTINO"]

    print(f"  Dados simulados: VRA={len(df_vra):,}, Tarifas={len(df_tar):,}")
    return df_vra, df_tar

if __name__ == "__main__":
    t0 = datetime.now()
    print(f"\n{'═' * 60}")
    print(f"  PREPARAÇÃO INICIADA: {t0:%d/%m/%Y %H:%M:%S}")
    print(f"{'═' * 60}")

    arq_vra    = PASTA_BRUTOS / "vra_consolidado.csv"
    arq_tar    = PASTA_BRUTOS / "tarifas_consolidado.csv"

    if arq_vra.exists() and arq_tar.exists():
        print("\n  Lendo dados reais da ANAC...")
        df_vra_raw = ler_csv(arq_vra)
        df_tar_raw = ler_csv(arq_tar)
        df_vra  = limpar_vra(df_vra_raw)
        df_tar  = limpar_tarifas(df_tar_raw)
    else:
        print("\n  Dados brutos não encontrados → usando dados simulados")
        print("  (Execute 01_coletar_dados.py para usar dados reais)")
        df_vra, df_tar = gerar_dados_simulados()

    df_final = integrar(df_vra, df_tar)

    print("\n  Salvando arquivos processados...")
    df_vra.to_csv(PASTA_PROC / "voos_limpo.csv", index=False, encoding="utf-8-sig")
    df_tar.to_csv(PASTA_PROC / "tarifas_limpo.csv", index=False, encoding="utf-8-sig")
    df_final.to_csv(PASTA_PROC / "dataset_final.csv", index=False, encoding="utf-8-sig")

    print(f"\n  Arquivos salvos em '{PASTA_PROC}/':")
    print(f"    • voos_limpo.csv      ({len(df_vra):,} linhas)")
    print(f"    • tarifas_limpo.csv   ({len(df_tar):,} linhas)")
    print(f"    • dataset_final.csv   ({len(df_final):,} linhas)")

    dur = (datetime.now() - t0).seconds
    print(f"\n{'═' * 60}")
    print(f"  CONCLUÍDO em {dur}s  →  próximo: python 03_dashboard_visao_geral.py")
    print(f"{'═' * 60}\n")
