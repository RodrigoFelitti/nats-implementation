"""monta a tabela resumo comparativa (console + output/tabela_resumo.tex)."""

from pathlib import Path
import pandas as pd
from load_data import load_all, agrega, filtra, formata_bytes

OUTPUT_DIR = Path(__file__).parent / "output"

#coluna que descreve a configuracao de cada cenario (resiliencia nao tem)
COLUNA_CONFIG = {"vazao": "tamanho_msg", "escalabilidade": "n_publishers", "replicacao": "replicas"}


def descreve_config(cenario, linha):
    if cenario == "vazao":
        return formata_bytes(linha["tamanho_msg"])
    if cenario == "escalabilidade":
        return f"{int(linha['n_publishers'])} pubs"
    if cenario == "replicacao":
        return f"R={int(linha['replicas'])}"
    return "1 pub, sub cai 30s"


def build_summary(df):
    """junta os cenarios numa tabela, uma linha por configuracao e modo."""
    linhas_tabela = []
    for cenario in ["vazao", "escalabilidade", "resiliencia", "replicacao"]:
        dados = filtra(df, cenario)
        if dados.empty:
            continue
        coluna_config = COLUNA_CONFIG.get(cenario)
        colunas_grupo = ["modo"] + ([coluna_config] if coluna_config else [])
        for _, linha in agrega(dados, *colunas_grupo).iterrows():
            linhas_tabela.append({
                "Cenario": cenario,
                "Config": descreve_config(cenario, linha),
                "Modo": linha["modo"],
                "p50 (ms)": round(linha["p50"], 3),
                "p95 (ms)": round(linha["p95"], 3),
                "p99 (ms)": round(linha["p99"], 3),
                "Vazao (msg/s)": int(round(linha["vazao_msg_s"])),
                "Perda (%)": round(linha["perda_pct"], 1),
            })
    return pd.DataFrame(linhas_tabela)


#modelo da tabela; FORMATO/CABECALHO/CORPO sao trocados na hora de gerar
TEMPLATE_TABELA = r"""\begin{table}[h]
\centering
\caption{Resumo comparativo das métricas medidas por cenário.}
\label{tab:resumo}
\begin{tabular}{FORMATO}
\toprule
CABECALHO
\midrule
CORPO
\bottomrule
\end{tabular}
\end{table}
"""


def escapa(texto):
    #troca os caracteres que o latex interpreta errado (%, _, &)
    for caractere, substituto in [("%", r"\%"), ("_", r"\_"), ("&", r"\&")]:
        texto = str(texto).replace(caractere, substituto)
    return texto


def linha_latex(celulas):
    #uma linha da tabela: celulas separadas por & e terminadas em \\
    return " & ".join(escapa(celula) for celula in celulas) + r" \\"


def exporta_latex(summary):
    """gera a tabela em latex (booktabs), sem depender de jinja2."""
    formato_colunas = "lll" + "r" * (len(summary.columns) - 3)
    cabecalho = linha_latex(summary.columns)
    corpo = "\n".join(linha_latex(linha) for _, linha in summary.iterrows())

    tabela = (TEMPLATE_TABELA
              .replace("FORMATO", formato_colunas)
              .replace("CABECALHO", cabecalho)
              .replace("CORPO", corpo))

    caminho = OUTPUT_DIR / "tabela_resumo.tex"
    caminho.write_text(tabela, encoding="utf-8")
    print(f"gerado: {caminho.name}")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = load_all()
    summary = build_summary(df)
    print(summary.to_string(index=False))
    print()
    exporta_latex(summary)
