#!/bin/bash

export USERID=$(id -u)
export GROUPID=$(id -g)

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export COMPOSE_FILES_FLAG="-f ${SCRIPT_DIR}/docker-compose.yml 
    -f  ${SCRIPT_DIR}/../../.devcontainer/db-docker-compose.yml"
echo $COMPOSE_FILES_FLAG
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

set -x
USERID=${USERID} GROUPID=${GROUPID} docker compose \
    ${COMPOSE_FILES_FLAG} \
    run --user=${USERID}:${GROUPID} playwright "$@"