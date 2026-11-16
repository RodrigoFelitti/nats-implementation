"""sensor (publisher) que publica leituras em sensores.<id>.leitura."""

import asyncio
import json
import random
import time
from datetime import datetime, timezone

import nats

from app import config


async def esperar_ate(momento: float):
    """dorme ate o cronometro chegar em `momento`."""
    falta = momento - time.perf_counter()
    if falta > 0:
        await asyncio.sleep(falta)


def cria_mensagem(sensor_id: str, tamanho: int) -> bytes:
    """monta uma leitura em json com exatamente `tamanho` bytes."""
    dados = {
        "id": sensor_id,
        "valor": round(random.uniform(0, 100), 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "padding": "",
    }
    tamanho_base = len(json.dumps(dados).encode())
    dados["padding"] = "x" * (tamanho - tamanho_base)
    return json.dumps(dados).encode()


async def run_sensor(sensor_id: str, taxa_hz: int, duracao_s: int, tamanho_payload: int, modo: str) -> int:
    """publica leituras na taxa pedida e devolve quantas foram enviadas."""
    conn = await nats.connect(config.NATS_URL_LOCAL)
    js = conn.jetstream() if modo == "jetstream" else None

    total_msgs = taxa_hz * duracao_s
    inicio = time.perf_counter()
    intervalo = 1 / taxa_hz

    enviadas = 0
    for i in range(total_msgs):
        await esperar_ate(inicio + i * intervalo)
        msg = cria_mensagem(sensor_id, tamanho_payload)
        subject = config.SUBJECT_SENSOR.format(sensor_id=sensor_id)
        if modo == "jetstream":
            #js.publish espera o ack de persistencia; no core e publish simples
            await js.publish(subject, msg)
        else:
            await conn.publish(subject, msg)
        enviadas += 1

    await conn.drain()
    return enviadas
