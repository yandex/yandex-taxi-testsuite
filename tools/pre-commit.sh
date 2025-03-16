#!/bin/sh

set -ex

GIT_ROOT=$(git rev-parse --show-toplevel)

cd "$GIT_ROOT"


make venv-format
make venv-check-linters venv-check-mypy
