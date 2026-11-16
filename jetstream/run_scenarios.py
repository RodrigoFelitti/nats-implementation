"""runner dos cenarios de teste do nats jetstream; grava os resultados em csv."""

import argparse
import asyncio
import csv
import gzip
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import sensor, consumer
from jetstream import setup_streams

COLUNAS = ["cenario", "modo", "tamanho_msg", "n_publishers", "n_subscribers",
           "latencia_ms", "msg_enviadas", "msg_recebidas", "duracao_s"]


def salvar_csv(linhas, nome_arquivo, colunas=COLUNAS):
    caminho = Path(__file__).parent / "results" / nome_arquivo
    with gzip.open(caminho, "wt", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(colunas)
        escritor.writerows(linhas)


async def cenario_vazao():
    """1 pub e 1 sub, variando o tamanho da mensagem."""
    linhas = []

    for tamanho in [100, 1000, 10000]:
        await setup_streams.setup()
        parar = asyncio.Event()
        tarefa = asyncio.create_task(consumer.run_consumer("jetstream", duracao_s=600, parar=parar))
        await asyncio.sleep(0.5)

        inicio = time.perf_counter()
        enviadas = await sensor.run_sensor("sensor-1", taxa_hz=1000, duracao_s=60,
                                           tamanho_payload=tamanho, modo="jetstream")
        duracao = round(time.perf_counter() - inicio, 1)

        await asyncio.sleep(5)  #folga para o consumer drenar o backlog final
        parar.set()
        latencias = await tarefa

        for lat in latencias:
            linhas.append(["vazao", "jetstream", tamanho, 1, 1, lat, enviadas, len(latencias), duracao])

    salvar_csv(linhas, "resultados_jetstream_vazao.csv.gz")


async def cenario_escalabilidade():
    """n pubs e 3 subs em queue group."""
    linhas = []

    for n_pubs in [1, 10, 50]:
        await setup_streams.setup()
        parar = asyncio.Event()
        consumers = [asyncio.create_task(consumer.run_consumer("jetstream", duracao_s=600,
                                                               queue_group="processadores", parar=parar))
                     for _ in range(3)]
        await asyncio.sleep(0.5)

        inicio = time.perf_counter()
        sensores = [sensor.run_sensor(f"sensor-{i}", taxa_hz=500, duracao_s=60,
                                      tamanho_payload=1000, modo="jetstream")
                    for i in range(n_pubs)]
        enviadas = sum(await asyncio.gather(*sensores))
        duracao = round(time.perf_counter() - inicio, 1)

        await asyncio.sleep(5)  #folga para os consumers drenarem o backlog
        parar.set()
        latencias = []
        for c in consumers:
            latencias += await c

        for lat in latencias:
            linhas.append(["escalabilidade", "jetstream", 1000, n_pubs, 3, lat,
                           enviadas, len(latencias), duracao])

    salvar_csv(linhas, "resultados_jetstream_escalabilidade.csv.gz")


async def cenario_resiliencia():
    """1 pub a 500 msg/s por 60s, sub cai entre os segundos 20 e 50 e volta."""
    await setup_streams.setup()
    antes_da_queda = asyncio.create_task(consumer.run_consumer("jetstream", duracao_s=20.5))
    await asyncio.sleep(0.5)

    tarefa_sensor = asyncio.create_task(sensor.run_sensor("sensor-1", taxa_hz=500, duracao_s=60,
                                                          tamanho_payload=1000, modo="jetstream"))

    latencias_antes = await antes_da_queda
    await asyncio.sleep(30)  #consumer fora do ar por 30s

    #o consumer que volta reusa o mesmo duravel e retoma de onde parou
    parar = asyncio.Event()
    de_volta = asyncio.create_task(consumer.run_consumer("jetstream", duracao_s=600, parar=parar))

    enviadas = await tarefa_sensor
    await asyncio.sleep(10)  #folga para drenar o backlog da queda
    parar.set()
    latencias_depois = await de_volta

    latencias = latencias_antes + latencias_depois

    linhas = []
    for lat in latencias:
        linhas.append(["resiliencia", "jetstream", 1000, 1, 1, lat, enviadas, len(latencias), 60])

    salvar_csv(linhas, "resultados_jetstream_resiliencia.csv.gz")


async def cenario_replicacao():
    """cenario 1 (1 pub, 1 sub, 1kb) com stream r=1 e r=3."""
    TAMANHO = 1000
    linhas = []
    for replicas in [1, 3]:
        await setup_streams.setup(replicas)

        parar = asyncio.Event()
        tarefa = asyncio.create_task(consumer.run_consumer("jetstream", duracao_s=600, parar=parar))
        await asyncio.sleep(0.5)

        inicio = time.perf_counter()
        enviadas = await sensor.run_sensor("sensor-1", taxa_hz=1000, duracao_s=60,
                                           tamanho_payload=TAMANHO, modo="jetstream")
        duracao = round(time.perf_counter() - inicio, 1)

        await asyncio.sleep(5)  #folga para drenar o backlog final
        parar.set()
        latencias = await tarefa

        for lat in latencias:
            linhas.append(["replicacao", "jetstream", TAMANHO, 1, 1, lat,
                           enviadas, len(latencias), duracao, replicas])

    salvar_csv(linhas, "resultados_jetstream_replicacao.csv.gz", COLUNAS + ["replicas"])


CENARIOS = {
    "vazao": cenario_vazao,
    "escalabilidade": cenario_escalabilidade,
    "resiliencia": cenario_resiliencia,
    "replicacao": cenario_replicacao,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cenario", required=True, choices=CENARIOS.keys())
    args = parser.parse_args()
    asyncio.run(CENARIOS[args.cenario]())
