#!/bin/bash

export USERID=$(id -u)
export GROUPID=$(id -g)
export COMPOSE_FILES_FLAG="-f .playwright/docker-compose.yml -f .devcontainer/docker-compose.yml"
build() {
   docker compose \
    ${COMPOSE_FILES_FLAG} \
    build \
    --parallel \
    --build-arg USERID=${USERID} \
    --build-arg GROUPID=${GROUPID}
}



if [ "$1" == "down" ];
then
    docker compose \
        ${COMPOSE_FILES_FLAG} \
        down
    exit 0
fi

build

docker compose \
    ${COMPOSE_FILES_FLAG} \
    run --user=${USERID}:${GROUPID} playwright "$@"