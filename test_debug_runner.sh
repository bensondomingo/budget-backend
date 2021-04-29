echo "Starting tests, run debug config to start debugging"
docker container exec -t budget-backend-test python3 -m debugpy --listen 0.0.0.0:5679 --wait-for-client -m pytest --disable-pytest-warnings