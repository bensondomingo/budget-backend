#!/bin/bash

debug=""
test_dir=app/tests/

while getopts ":d:u:" arg; do
    case $arg in
    d) debug=--wait-for-client ;;
    u) unit=$test_dir$OPTARG ;;
    esac
done

if [ -z "$debug" ]; then
    echo "Starting test ..."
else
    echo "Starting test in debug mode, press F5 to continue ..."
fi

docker container exec -t budget-backend-test python3 -m debugpy --listen 0.0.0.0:5679 $debug -m pytest $unit --disable-pytest-warnings
