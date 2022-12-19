ARG PYTHON_IMG=3-alpine

FROM python:${PYTHON_IMG:-latest}

EXPOSE 5000

ENV PROJECT_DIR /app
ENV PYTHONUNBUFFERED 1

# module holding our project instance
ENV FLASK_APP=wsgi.py
ENV FLASK_DEBUG=False
ENV FLASK_ENV=production

WORKDIR ${PROJECT_DIR}
COPY docker/damngoodtech/entrypoint.sh /
COPY Pipfile Pipfile.lock ${PROJECT_DIR}
# COPY src ${PROJECT_DIR}/src
RUN apk add --no-cache --update fish

# https://jonathanmeier.io/using-pipenv-with-docker/
RUN apk add --no-cache --update --virtual \
  gcc \
  make && \
  python -m pip install pipenv && \
  pipenv install --system --deploy

WORKDIR ${PROJECT_DIR}

# ENTRYPOINT [ "/entrypoint.sh" ]
