"""carrega os csvs dos cenarios e oferece funcoes de apoio para os graficos e a tabela."""

from pathlib import Path
import pandas as pd

CORE_RESULTS_DIR = Path(__file__).parent.parent / "core" / "results"
JETSTREAM_RESULTS_DIR = Path(__file__).parent.parent / "jetstream" / "results"

ORDEM_MODOS = ["core", "jetstream"]


def load_all():
    """carrega todos os csvs (core + jetstream) num dataframe unico."""
    tabelas = []
    #aceita .csv e .csv.gz (os grandes vao compactados para caber no github)
    for pasta in (CORE_RESULTS_DIR, JETSTREAM_RESULTS_DIR):
        for arquivo in list(pasta.glob("*.csv")) + list(pasta.glob("*.csv.gz")):
            tabelas.append(pd.read_csv(arquivo))
    if not tabelas:
        raise FileNotFoundError("nenhum csv encontrado — rode os cenarios primeiro.")
    return pd.concat(tabelas, ignore_index=True)


def modos_presentes(df):
    """modos que existem no dataframe, na ordem padrao."""
    return [modo for modo in ORDEM_MODOS if modo in set(df["modo"])]


def filtra(df, cenario):
    """recorta o dataframe para um cenario."""
    return df[df["cenario"] == cenario]


def agrega(df, *colunas_grupo):
    """agrupa por `colunas_grupo` e resume latencia (p50/p95/p99), vazao e perda."""
    resumos = []
    for valores_grupo, grupo in df.groupby(list(colunas_grupo), sort=False):
        if not isinstance(valores_grupo, tuple):
            valores_grupo = (valores_grupo,)
        #os contadores sao iguais em todas as linhas do grupo, pega o primeiro
        msg_enviadas = int(grupo["msg_enviadas"].iloc[0])
        msg_recebidas = int(grupo["msg_recebidas"].iloc[0])
        duracao_s = float(grupo["duracao_s"].iloc[0])
        latencias = grupo["latencia_ms"]

        resumo = dict(zip(colunas_grupo, valores_grupo))
        resumo.update(
            p50=latencias.quantile(0.50),
            p95=latencias.quantile(0.95),
            p99=latencias.quantile(0.99),
            vazao_msg_s=msg_recebidas / duracao_s,
            perda_pct=100 * (1 - msg_recebidas / msg_enviadas),
            msg_enviadas=msg_enviadas,
            msg_recebidas=msg_recebidas,
        )
        resumos.append(resumo)
    return pd.DataFrame(resumos)


def formata_bytes(tamanho):
    """100 -> '100 B', 1000 -> '1 KB'."""
    tamanho = int(tamanho)
    return f"{tamanho // 1000} KB" if tamanho >= 1000 else f"{tamanho} B"


if __name__ == "__main__":
    df = load_all()
    print(df.head())
    print(f"\ntotal de linhas: {len(df)}")
    print(f"cenarios: {df['cenario'].unique()}")
    print(f"modos: {df['modo'].unique()}")
