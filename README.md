# Trabalho GB — NATS Core vs JetStream

Comparação empírica entre os dois modos de operação do NATS (Core e JetStream) em um cenário de telemetria IoT simulada, medindo latência, vazão e perda de mensagens.

**Autores:** Rodrigo Felitti D'Ávila, Pedro Engel, Ramiro Manoel — Sistemas Distribuídos, UNISINOS.

## Estrutura

```
app/          aplicação de referência (sensor e consumidor), compartilhada pelos dois modos
core/         NATS Core: ambiente, cenários e resultados
jetstream/    NATS JetStream: cluster, cenários e resultados
analysis/     scripts de análise (gráficos e tabela comparativa)
```

Os resultados de cada modo ficam em `core/results/` e `jetstream/results/` em CSV compactado, e os gráficos em `analysis/output/`.

## Como rodar

Requer Docker e Python 3.10+.

### NATS Core

```bash
cd core
docker compose up -d
pip install -r ../app/requirements.txt
python run_scenarios.py --cenario vazao
python run_scenarios.py --cenario escalabilidade
python run_scenarios.py --cenario resiliencia
docker compose down
```

### NATS JetStream

```bash
cd jetstream
docker compose up -d
pip install -r ../app/requirements.txt
python setup_streams.py
python run_scenarios.py --cenario vazao
python run_scenarios.py --cenario escalabilidade
python run_scenarios.py --cenario resiliencia
python run_scenarios.py --cenario replicacao
docker compose down -v
```

### Análise

Com os CSVs já gerados em `core/results/` e `jetstream/results/`:

```bash
cd analysis
pip install -r requirements.txt
python plots.py
python summary_table.py
```

