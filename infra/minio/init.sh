#!/bin/sh
set -e

mc alias set local http://minio:9000 minio minio12345
mc mb --ignore-existing local/dpa-guard
