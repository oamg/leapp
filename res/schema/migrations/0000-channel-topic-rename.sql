BEGIN;

ALTER TABLE message
  RENAME TO message_0;

CREATE TABLE message (
  id                INTEGER PRIMARY KEY NOT NULL,
  context           VARCHAR(36)         NOT NULL REFERENCES execution (context),
  stamp             TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  topic             VARCHAR(1024)       NOT NULL,
  type              VARCHAR(1024)       NOT NULL,
  data_source_id    INTEGER             NOT NULL REFERENCES data_source (id),
  message_data_hash VARCHAR(64)         NOT NULL REFERENCES message_data (hash)
);

INSERT INTO message (id, context, stamp, topic, type, data_source_id, message_data_hash)
  SELECT
    id,
    context,
    stamp,
    channel,
    type,
    data_source_id,
    message_data_hash
  FROM message_0;

DROP TABLE message_0;
DROP VIEW messages_data;

CREATE VIEW IF NOT EXISTS messages_data AS
  SELECT
    message.id        AS id,
    message.context   AS context,
    message.stamp     AS stamp,
    message.topic     AS topic,
    message.type      as type,
    data_source.actor as actor,
    data_source.phase as phase,
    msg_data.hash     as message_hash,
    msg_data.data     as message_data,
    host.hostname     as hostname
  FROM
    message
    JOIN
    data_source ON data_source.id = message.data_source_id
    ,
    message_data as msg_data ON message.message_data_hash = msg_data.hash,
  host ON host.id = data_source.host_id;

PRAGMA user_version = 1;

COMMIT;