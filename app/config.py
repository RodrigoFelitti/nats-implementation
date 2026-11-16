"""configuracoes compartilhadas entre os componentes."""

#subjects
SUBJECT_SENSOR = "sensores.{sensor_id}.leitura"
SUBJECT_SENSOR_WILDCARD = "sensores.>"
SUBJECT_ALERTA_REQUEST = "alertas.verificar"

#stream e consumer do jetstream
STREAM_NAME = "SENSORES"
CONSUMER_NAME = "processador"

#limite para disparar alerta
LIMITE_ALERTA = 80.0

#enderecos
NATS_URL_LOCAL = "nats://localhost:4222"
NATS_URL_CLUSTER = "nats://localhost:4222,nats://localhost:4223,nats://localhost:4224"
