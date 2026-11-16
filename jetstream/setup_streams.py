"""cria o stream SENSORES no cluster jetstream."""

import argparse
import asyncio
import sys
from pathlib import Path

import nats
from nats.js.api import StreamConfig, StorageType, RetentionPolicy

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import config

#capacidade folgada para segurar o backlog da queda e os volumes da escalabilidade
MAX_MSGS = 5_000_000


async def setup(replicas: int = 1):
    """cria o stream, recriando se ja existir (permite trocar o fator de replicas)."""
    conn = await nats.connect(servers=config.NATS_URL_CLUSTER.split(","))
    js = conn.jetstream()

    #recria do zero para alternar o fator de replicacao
    try:
        await js.delete_stream(config.STREAM_NAME)
    except Exception:
        pass

    await js.add_stream(StreamConfig(
        name=config.STREAM_NAME,
        subjects=["sensores.>"],
        storage=StorageType.FILE,
        retention=RetentionPolicy.LIMITS,
        num_replicas=replicas,
        max_msgs=MAX_MSGS,
    ))

    print(f"Stream {config.STREAM_NAME} criado (replicas={replicas}, max_msgs={MAX_MSGS}).")
    await conn.drain()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicas", type=int, default=1, choices=[1, 3])
    args = parser.parse_args()
    asyncio.run(setup(args.replicas))
