ARG PYTHON_IMG=3-alpine

FROM python:${PYTHON_IMG}

EXPOSE 5000

ENV PROJECT_DIR /app
ENV PYTHONUNBUFFERED 1

# module holding our project instance
ENV FLASK_APP=wsgi.py
ENV FLASK_DEBUG=1
ENV FLASK_ENV=development

WORKDIR /app
COPY Pipfile /app
RUN apk add --no-cache --update fish
RUN apk add --no-cache --update --virtual \
  gcc\
  make\
  g++\
  zlib-dev\
  libc-dev\&& pip install pipenv && pipenv install

# we make sure to run the project as a regular user
USER ${USR}
WORKDIR ${PROJECT_DIR}
CMD ["python", "wsgi.py"]
