import os
import time
import zipfile
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

PASTA_DADOS    = Path("dados_brutos")
PASTA_VRA      = PASTA_DADOS / "vra"
PASTA_TARIFAS  = PASTA_DADOS / "tarifas"

for pasta in [PASTA_DADOS, PASTA_VRA, PASTA_TARIFAS]:
    pasta.mkdir(parents=True, exist_ok=True)

ANO_INICIO = 2022
ANO_FIM    = 2024

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

BASE_VRA = (
    "https://sistemas.anac.gov.br/dadosabertos/"
    "Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/VRA"
)

BASE_TARIFAS = (
    "https://sistemas.anac.gov.br/dadosabertos/"
    "Tarifas%20A%C3%A9reas/Tarifas%20Dom%C3%A9sticas"
)


def _baixar(url: str, destino: Path) -> bool:
    """Baixa um arquivo e salva no destino."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        destino.write_bytes(resp.content)
        return True
    except requests.HTTPError as e:
        code = e.response.status_code
        if code != 404:
            print(f"  ERRO HTTP {code}: {url}")
        return False
    except Exception as e:
        print(f"  ERRO: {e}")
        return False


def baixar_vra() -> list[Path]:
    """Baixa os arquivos mensais de VRA."""
    print("\n" + "═" * 60)
    print("  COLETANDO: VRA — Voo Regular Ativo")
    print("═" * 60)

    baixados = []
    hoje = datetime.now()

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        for mes in range(1, 13):
            if ano == hoje.year and mes >= hoje.month:
                break

            nome_csv = f"VRA_{ano}_{mes:02d}.csv"
            destino_csv = PASTA_VRA / nome_csv

            if destino_csv.exists():
                print(f"  [CACHE] {nome_csv}")
                baixados.append(destino_csv)
                continue

            nome_zip = f"VRA_{ano}_{mes:02d}.zip"
            destino_zip = PASTA_VRA / nome_zip
            url_zip = f"{BASE_VRA}/{ano}/{nome_zip}"
            url_csv = f"{BASE_VRA}/{ano}/{nome_csv}"

            print(f"  Baixando {nome_zip}...", end=" ", flush=True)

            if _baixar(url_zip, destino_zip):
                try:
                    with zipfile.ZipFile(destino_zip, "r") as zf:
                        csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                        if csvs:
                            zf.extract(csvs[0], PASTA_VRA)
                            extraido = PASTA_VRA / csvs[0]
                            if extraido != destino_csv:
                                extraido.rename(destino_csv)
                    destino_zip.unlink(missing_ok=True)
                    print("OK ✓")
                    baixados.append(destino_csv)
                except Exception as e:
                    print(f"  Erro ao extrair ZIP: {e}")
                    destino_zip.unlink(missing_ok=True)
            else:
                print(f"ZIP não encontrado, tentando CSV...", end=" ", flush=True)
                if _baixar(url_csv, destino_csv):
                    print("OK ✓")
                    baixados.append(destino_csv)
                else:
                    print("não disponível, pulando")

            time.sleep(0.3)

    print(f"\n  Total VRA: {len(baixados)} arquivo(s)")
    return baixados


def baixar_tarifas() -> list[Path]:
    """Baixa os arquivos trimestrais de tarifas."""
    print("\n" + "═" * 60)
    print("  COLETANDO: Tarifas Aéreas Domésticas")
    print("═" * 60)

    baixados = []

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        for tri in range(1, 5):
            nome = f"Tarifas_{ano}T{tri}.csv"
            destino = PASTA_TARIFAS / nome

            if destino.exists():
                print(f"  [CACHE] {nome}")
                baixados.append(destino)
                continue

            url = f"{BASE_TARIFAS}/{nome}"
            print(f"  Baixando {nome}...", end=" ", flush=True)

            if _baixar(url, destino):
                print("OK ✓")
                baixados.append(destino)
            else:
                print("não disponível, pulando")

            time.sleep(0.3)

    print(f"\n  Total Tarifas: {len(baixados)} arquivo(s)")
    return baixados


def consolidar(arquivos: list[Path], saida: Path, sep: str = ";") -> pd.DataFrame:
    """Consolida uma lista de CSVs em um único arquivo."""
    dfs = []
    for f in arquivos:
        try:
            df = pd.read_csv(f, sep=sep, encoding="latin-1", dtype=str, low_memory=False)
            dfs.append(df)
        except Exception as e:
            print(f"  Erro ao ler {f.name}: {e}")

    if not dfs:
        print(f"  Nenhum dado para consolidar em {saida.name}")
        return pd.DataFrame()

    resultado = pd.concat(dfs, ignore_index=True)
    resultado.to_csv(saida, index=False, encoding="utf-8-sig")
    print(f"  {saida.name}: {len(resultado):,} linhas × {len(resultado.columns)} colunas")
    return resultado


if __name__ == "__main__":
    t0 = datetime.now()
    print(f"\n{'═' * 60}")
    print(f"  COLETA INICIADA: {t0:%d/%m/%Y %H:%M:%S}")
    print(f"  Período: {ANO_INICIO}–{ANO_FIM}")
    print(f"{'═' * 60}")

    arq_vra     = baixar_vra()
    arq_tarifas = baixar_tarifas()

    print("\n" + "═" * 60)
    print("  CONSOLIDANDO")
    print("═" * 60)
    consolidar(arq_vra,     PASTA_DADOS / "vra_consolidado.csv")
    consolidar(arq_tarifas, PASTA_DADOS / "tarifas_consolidado.csv")

    dur = (datetime.now() - t0).seconds
    print(f"\n{'═' * 60}")
    print(f"  CONCLUÍDO em {dur}s  →  próximo: python 02_preparar_dados.py")
    print(f"{'═' * 60}\n")
