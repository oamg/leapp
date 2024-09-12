BEGIN;

CREATE TABLE IF NOT EXISTS actor_config (
  id                INTEGER PRIMARY KEY NOT NULL,
  context           VARCHAR(36)         NOT NULL REFERENCES execution (context),
  actor_config_hash VARCHAR(64)         NOT NULL REFERENCES actor_config_data (hash)
);

CREATE TABLE IF NOT EXISTS actor_config_data (
  hash    VARCHAR(64) PRIMARY KEY NOT NULL,
  config  TEXT
);

PRAGMA user_version = 4;

COMMIT;
