#!/bin/bash

export USERID=$(id -u)
export GROUPID=$(id -g)
export PLAYWRIGHT_VERSION=$(bash -c './get-npm-package-version.sh ./package.json "@playwright/test"')

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
    --build-arg GROUPID=${GROUPID} \
    --build-arg PLAYWRIGHT_VERSION=${PLAYWRIGHT_VERSION}
}


if [ "$1" == "down" ];
then
    docker rm $(docker ps --filter status=exited -q) || true
    docker compose \
        ${COMPOSE_FILES_FLAG} \
        down --remove-orphans -v
    exit 0
fi

build

CONTAINER=playwright
CMD=("$@")
if [ "$1" == "debug" ];
then
    CONTAINER=playwright_display
    CMD=(bash -c './wait-for-app.sh && npx playwright test --debug')
fi

set -x
USERID=${USERID} GROUPID=${GROUPID} docker compose \
    ${COMPOSE_FILES_FLAG} \
    run --remove-orphans --rm --user=${USERID}:${GROUPID} "$CONTAINER" "${CMD[@]}"
