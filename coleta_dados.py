import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

PASTA_DADOS = Path("dados_brutos")
PASTA_VRA   = PASTA_DADOS / "vra"

for p in [PASTA_DADOS, PASTA_VRA]:
    p.mkdir(parents=True, exist_ok=True)

ANO_INICIO = 2022
ANO_FIM    = 2025

BASE_VRA = "https://siros.anac.gov.br/siros/registros/diversos/vra"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/octet-stream,*/*",
}

def baixar_arquivo(url: str, destino: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "html" in content_type.lower():
            return False

        with open(destino, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        if destino.stat().st_size < 1024:
            destino.unlink(missing_ok=True)
            return False

        return True

    except requests.HTTPError as e:
        if e.response.status_code != 404:
            print(f"\n    ERRO HTTP {e.response.status_code}")
        return False
    except Exception as e:
        print(f"\n    ERRO: {e}")
        return False

def baixar_vra() -> list[Path]:
    print("\n" + "═" * 60)
    print("  COLETANDO: VRA - Voo Regular Ativo")
    print(f"  Fonte: siros.anac.gov.br/.../vra/{{ANO}}/VRA_{{ANO}}_{{MES}}.csv")
    print("═" * 60)

    baixados = []
    hoje = datetime.now()

    for ano in range(ANO_INICIO, ANO_FIM + 1):
        for mes in range(1, 13):

            if ano == hoje.year and mes >= hoje.month:
                break

            nome    = f"VRA_{ano}_{mes:02d}.csv"
            destino = PASTA_VRA / nome

            if destino.exists() and destino.stat().st_size > 1024:
                kb = destino.stat().st_size // 1024
                print(f"  [CACHE] {nome}  ({kb:,} KB)")
                baixados.append(destino)
                continue

            url = f"{BASE_VRA}/{ano}/{nome}"
            print(f"  Baixando {nome}...", end=" ", flush=True)

            if baixar_arquivo(url, destino):
                kb = destino.stat().st_size // 1024
                print(f"OK ✓  ({kb:,} KB)")
                baixados.append(destino)
            else:
                print("não encontrado, pulando")

            time.sleep(0.5)

    print(f"\n  ✓ Total VRA: {len(baixados)} arquivo(s)")
    return baixados

def consolidar(arquivos: list[Path], saida: Path) -> pd.DataFrame:
    if not arquivos:
        print(f"  Nenhum arquivo para consolidar em {saida.name}")
        return pd.DataFrame()

    dfs = []
    for f in arquivos:
        for enc in ["latin-1", "utf-8-sig", "utf-8"]:
            try:
                df = pd.read_csv(f, sep=";", encoding=enc, dtype=str, low_memory=False)
                if len(df.columns) > 1:
                    dfs.append(df)
                    break
            except Exception:
                continue

    if not dfs:
        print(f"  Erro: nenhum CSV legível")
        return pd.DataFrame()

    resultado = pd.concat(dfs, ignore_index=True)
    resultado.to_csv(saida, index=False, encoding="utf-8-sig")
    print(f"  {saida.name}: {len(resultado):,} linhas × {len(resultado.columns)} cols")
    return resultado

if __name__ == "__main__":
    t0 = datetime.now()
    print(f"\n{'═' * 60}")
    print(f"  COLETA INICIADA: {t0:%d/%m/%Y %H:%M:%S}")
    print(f"  Período: {ANO_INICIO}–{ANO_FIM}")
    print(f"{'═' * 60}")

    arq_vra = baixar_vra()

    print("\n" + "═" * 60)
    print("  CONSOLIDANDO")
    print("═" * 60)
    consolidar(arq_vra, PASTA_DADOS / "vra_consolidado.csv")

    dur = (datetime.now() - t0).seconds
    print(f"\n{'═' * 60}")
    print(f"  CONCLUÍDO em {dur}s")
    print(f"  VRA: {len(arq_vra)} arquivo(s)")
    print(f"\n  Próximo passo: python prepara_dados.py")
    print(f"{'═' * 60}\n")