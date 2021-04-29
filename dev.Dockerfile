FROM python:3.8

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PROJECT_DIR /usr/src/app

WORKDIR ${PROJECT_DIR}

COPY Pipfile Pipfile.lock ${PROJECT_DIR}/

RUN apt-get install libpq-dev -y

RUN pip install pipenv && \
    pip install debugpy && \
    pip install pytest && \
    pipenv install --system --deploy

COPY . .
