"""gera os graficos comparativos core vs jetstream (saem em output/)."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")  #nao abre janela, so salva o arquivo
import matplotlib.pyplot as plt
import numpy as np

from load_data import load_all, agrega, filtra, modos_presentes, formata_bytes

OUTPUT_DIR = Path(__file__).parent / "output"

#uma cor e um rotulo por modo, para manter igual em todos os graficos
COR = {"core": "#4C72B0", "jetstream": "#DD8452"}
ROTULO = {"core": "NATS Core", "jetstream": "NATS JetStream"}


def plot_latencia(df):
    """latencia p50 e p99 por tamanho de mensagem (cenario vazao)."""
    dados = filtra(df, "vazao")
    if dados.empty:
        print("sem dados de vazao — pulando")
        return

    resumo = agrega(dados, "modo", "tamanho_msg")
    tamanhos = sorted(resumo["tamanho_msg"].unique())
    modos = modos_presentes(df)
    posicoes = np.arange(len(tamanhos))
    largura_barra = 0.8 / len(modos)

    figura, (eixo_p50, eixo_p99) = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for eixo, percentil, titulo in [(eixo_p50, "p50", "Mediana (p50)"),
                                    (eixo_p99, "p99", "Cauda (p99)")]:
        for indice_modo, modo in enumerate(modos):
            dados_modo = resumo[resumo["modo"] == modo].set_index("tamanho_msg")
            latencias = [dados_modo.loc[tamanho, percentil] for tamanho in tamanhos]
            eixo.bar(posicoes + indice_modo * largura_barra, latencias, largura_barra,
                     label=ROTULO[modo], color=COR[modo])
        eixo.set_xticks(posicoes + largura_barra * (len(modos) - 1) / 2)
        eixo.set_xticklabels([formata_bytes(tamanho) for tamanho in tamanhos])
        eixo.set_title(titulo)
        eixo.set_xlabel("Tamanho da mensagem")
        eixo.grid(axis="y", alpha=0.3)
    eixo_p50.set_ylabel("Latência (ms)")
    eixo_p50.legend()
    figura.suptitle("Latência fim-a-fim por tamanho de mensagem")
    salva(figura, "latencia_comparacao.png")


def plot_vazao(df):
    """escalabilidade: vazao sustentada e latencia p99 por nº de publishers."""
    dados = filtra(df, "escalabilidade")
    if dados.empty:
        print("sem dados de escalabilidade — pulando")
        return

    resumo = agrega(dados, "modo", "n_publishers")
    figura, (eixo_vazao, eixo_latencia) = plt.subplots(1, 2, figsize=(11, 4.5))
    for modo in modos_presentes(df):
        dados_modo = resumo[resumo["modo"] == modo].sort_values("n_publishers")
        eixo_vazao.plot(dados_modo["n_publishers"], dados_modo["vazao_msg_s"],
                        marker="o", color=COR[modo], label=ROTULO[modo])
        eixo_latencia.plot(dados_modo["n_publishers"], dados_modo["p99"],
                           marker="o", color=COR[modo], label=ROTULO[modo])

    eixo_vazao.set_title("Vazão sustentada")
    eixo_vazao.set_ylabel("Mensagens recebidas / s")
    eixo_latencia.set_title("Latência de cauda (p99)")
    eixo_latencia.set_ylabel("Latência (ms)")
    for eixo in (eixo_vazao, eixo_latencia):
        eixo.set_xlabel("Nº de publishers")
        eixo.grid(alpha=0.3)
        eixo.legend()
    figura.suptitle("Escalabilidade com o nº de publishers")
    salva(figura, "vazao_comparacao.png")


def plot_resiliencia(df):
    """enviadas vs recebidas na queda do consumidor."""
    dados = filtra(df, "resiliencia")
    if dados.empty:
        print("sem dados de resiliencia — pulando")
        return

    modos = modos_presentes(df)
    #uma linha por modo, reordenada na ordem padrao para casar com o eixo x
    resumo = agrega(dados, "modo").set_index("modo").loc[modos]
    posicoes = np.arange(len(modos))

    figura, eixo = plt.subplots(figsize=(7, 4.5))
    eixo.bar(posicoes - 0.2, resumo["msg_enviadas"], 0.4, label="Enviadas", color="#999999")
    eixo.bar(posicoes + 0.2, resumo["msg_recebidas"], 0.4, label="Recebidas",
             color=[COR[modo] for modo in modos])
    #anota a perda em cima da barra de recebidas
    for indice, modo in enumerate(modos):
        eixo.text(posicoes[indice] + 0.2, resumo["msg_recebidas"].iloc[indice],
                  f"perda {resumo['perda_pct'].iloc[indice]:.1f}%",
                  ha="center", va="bottom", fontweight="bold")

    eixo.set_xticks(posicoes)
    eixo.set_xticklabels([ROTULO[modo] for modo in modos])
    eixo.set_ylabel("Mensagens")
    eixo.grid(axis="y", alpha=0.3)
    eixo.legend()
    figura.suptitle("Resiliência: perda de mensagens na queda do consumidor")
    salva(figura, "resiliencia.png")


def plot_replicacao(df):
    """latencia p99 do jetstream com R=1 vs R=3 (cenario extra)."""
    dados = filtra(df, "replicacao")
    #o fator de replicacao precisa de uma coluna 'replicas'
    if dados.empty or "replicas" not in dados.columns:
        print("sem dados de replicacao — pulando (depende do jetstream, pessoa 2)")
        return

    resumo = agrega(dados, "replicas").sort_values("replicas")
    rotulos = [f"R={int(fator)}" for fator in resumo["replicas"]]

    figura, eixo = plt.subplots(figsize=(7, 4.5))
    eixo.bar(rotulos, resumo["p99"], color=COR["jetstream"])
    eixo.set_ylabel("Latência p99 (ms)")
    eixo.grid(axis="y", alpha=0.3)
    figura.suptitle("Custo da replicação (RAFT): R=1 vs R=3")
    salva(figura, "replicacao.png")


def salva(figura, nome_arquivo):
    figura.tight_layout()
    figura.savefig(OUTPUT_DIR / nome_arquivo, dpi=200, bbox_inches="tight")
    plt.close(figura)
    print(f"gerado: {nome_arquivo}")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = load_all()
    plot_latencia(df)
    plot_vazao(df)
    plot_resiliencia(df)
    plot_replicacao(df)
    print(f"\ngraficos salvos em {OUTPUT_DIR}")
