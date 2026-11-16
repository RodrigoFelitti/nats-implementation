"""consumer (subscriber) que assina sensores.> e mede a latencia de cada mensagem."""

import asyncio
import json
from datetime import datetime, timezone

import nats

from app import config


async def run_consumer(modo: str, duracao_s: float, queue_group: str = None,
                       com_alerta: bool = False, parar: "asyncio.Event" = None) -> list[float]:
    """assina as leituras e devolve a latencia (ms) de cada mensagem recebida."""
    conn = await nats.connect(config.NATS_URL_LOCAL)

    latencias = []

    async def recebe_msg(msg):
        agora = datetime.now(timezone.utc)
        dados = json.loads(msg.data)
        timestamp = datetime.fromisoformat(dados["timestamp"])
        latencia = (agora - timestamp).total_seconds() * 1000
        latencias.append(latencia)

        if com_alerta:
            asyncio.create_task(conn.request(config.SUBJECT_ALERTA_REQUEST, msg.data))

        if modo == "jetstream":
            await msg.ack()

    if modo == "jetstream":
        js = conn.jetstream()
        if queue_group:
            #no nats-py o nome do queue vira o nome do duravel, entao nao passamos CONSUMER_NAME
            await js.subscribe(config.SUBJECT_SENSOR_WILDCARD, queue=queue_group,
                               cb=recebe_msg, manual_ack=True)
        else:
            await js.subscribe(config.SUBJECT_SENSOR_WILDCARD, durable=config.CONSUMER_NAME,
                               cb=recebe_msg, manual_ack=True)
    else:
        await conn.subscribe(config.SUBJECT_SENSOR_WILDCARD, queue=queue_group, cb=recebe_msg)

    if parar is not None:
        #roda ate receber o sinal de parar, com duracao_s como teto
        try:
            await asyncio.wait_for(parar.wait(), timeout=duracao_s)
        except asyncio.TimeoutError:
            pass
    else:
        await asyncio.sleep(duracao_s)
    await conn.drain()

    return latencias
