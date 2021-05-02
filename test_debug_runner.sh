#!/bin/bash
echo "Starting tests, run debug config to start testing"

test_dir=app/tests/

if [ -z "$1" ]; then
    docker container exec -t budget-backend-test python3 -m debugpy --listen 0.0.0.0:5679 --wait-for-client -m pytest --disable-pytest-warnings
else
    unit=$test_dir$1
    docker container exec -t budget-backend-test python3 -m debugpy --listen 0.0.0.0:5679 --wait-for-client -m pytest $unit --disable-pytest-warnings
fi
