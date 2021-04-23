#!/bin/sh -eux

python3 ./make_test_results.py
chmod -R 755 "$ARTIFACT_DIR" && cp -r "$ARTIFACT_DIR" .
