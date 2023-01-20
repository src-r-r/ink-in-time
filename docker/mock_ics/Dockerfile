FROM node:current-alpine

EXPOSE 3000

RUN apk add \
    --update --virtual --no-cache \
    g++ \
    make \
    python3

WORKDIR /app
COPY ./docker/mock_ics/start.sh /
RUN chmod +x /start.sh
COPY package.json /app
COPY mocking /app/mocking/
WORKDIR /app
RUN npm i