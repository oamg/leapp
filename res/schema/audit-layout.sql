BEGIN;

PRAGMA user_version = 1;

CREATE TABLE IF NOT EXISTS execution (
  id            INTEGER PRIMARY KEY NOT NULL,
  context       VARCHAR(36)         NOT NULL UNIQUE,
  stamp         TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  configuration TEXT                         DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS host (
  id       INTEGER PRIMARY KEY NOT NULL,
  context  VARCHAR(36)         NOT NULL REFERENCES execution (context),
  hostname VARCHAR(255)        NOT NULL,
  UNIQUE (context, hostname)
);

CREATE TABLE IF NOT EXISTS message_data (
  hash VARCHAR(64) PRIMARY KEY NOT NULL,
  data TEXT
);

CREATE TABLE IF NOT EXISTS data_source (
  id      INTEGER PRIMARY KEY NOT NULL,
  context VARCHAR(36)         NOT NULL REFERENCES execution (context),
  host_id INTEGER             NOT NULL REFERENCES host (id),
  actor   VARCHAR(1024)       NOT NULL DEFAULT '',
  phase   VARCHAR(1024)       NOT NULL DEFAULT '',
  UNIQUE (context, host_id, actor, phase)
);


CREATE TABLE IF NOT EXISTS message (
  id                INTEGER PRIMARY KEY NOT NULL,
  context           VARCHAR(36)         NOT NULL REFERENCES execution (context),
  stamp             TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  topic             VARCHAR(1024)       NOT NULL,
  type              VARCHAR(1024)       NOT NULL,
  data_source_id    INTEGER             NOT NULL REFERENCES data_source (id),
  message_data_hash VARCHAR(64)         NOT NULL REFERENCES message_data (hash)
);


CREATE TABLE IF NOT EXISTS audit (
  id             INTEGER PRIMARY KEY NOT NULL,
  event          VARCHAR(256)        NOT NULL REFERENCES execution (context),
  stamp          TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  context        VARCHAR(36)         NOT NULL,
  data_source_id INTEGER             NOT NULL REFERENCES data_source (id),

  message_id     INTEGER                      DEFAULT NULL REFERENCES message (id),
  data           TEXT                         DEFAULT NULL
);

CREATE VIEW IF NOT EXISTS messages_data AS
  SELECT
    message.id        AS id,
    message.context   AS context,
    message.stamp     AS stamp,
    message.topic     AS topic,
    message.type      AS type,
    data_source.actor AS actor,
    data_source.phase AS phase,
    msg_data.hash     AS message_hash,
    msg_data.data     AS message_data,
    host.hostname     AS hostname
  FROM
    message
  JOIN
    data_source              ON data_source.id            = message.data_source_id,
    message_data AS msg_data ON message.message_data_hash = msg_data.hash,
    host                     ON host.id                   = data_source.host_id
;

COMMIT;