"""servico de alerta (request/reply) que responde em alertas.verificar."""

import asyncio
import json

import nats

from app import config


async def run_alert_service(modo: str, duracao_s: float):
    """responde se o valor recebido passa do limite de alerta."""
    conn = await nats.connect(config.NATS_URL_LOCAL)

    async def responde(msg):
        dados = json.loads(msg.data)
        resposta = {"alerta": dados["valor"] > config.LIMITE_ALERTA}
        await msg.respond(json.dumps(resposta).encode())

    await conn.subscribe(config.SUBJECT_ALERTA_REQUEST, cb=responde)
    await asyncio.sleep(duracao_s)
    await conn.drain()
