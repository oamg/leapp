BEGIN;

CREATE TABLE metadata (
  id                INTEGER PRIMARY KEY NOT NULL,
  context           VARCHAR(36)         NOT NULL REFERENCES execution (context),
  kind              VARCHAR(256)        NOT NULL DEFAULT '',
  name              VARCHAR(1024)       NOT NULL DEFAULT '',
  metadata          TEXT                         DEFAULT NULL,
  UNIQUE (context, kind, name)
);

CREATE TABLE dialog (
  id                INTEGER PRIMARY KEY NOT NULL,
  context           VARCHAR(36)         NOT NULL REFERENCES execution (context),
  scope             VARCHAR(1024)       NOT NULL DEFAULT '',
  data              TEXT                         DEFAULT NULL,
  data_source_id    INTEGER             NOT NULL REFERENCES data_source (id)
);

PRAGMA user_version = 3;

COMMIT;
