#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPO_ROOT_DIR="${SCRIPT_DIR}/../"
PLAYWRIGHT_DIR="${REPO_ROOT_DIR}/packages/playwright"

export USERID=$(id -u)
export GROUPID=$(id -g)
export PLAYWRIGHT_VERSION=$(bash -c "${PLAYWRIGHT_DIR}/get-npm-package-version.sh ./package.json '@playwright/test'")

# playwright.config.ts needs to be in the root of the repository so that vscode will pick up automatically.
# In the meantime for the pwtests container, we copy a version over
cp ${REPO_ROOT_DIR}/playwright.config.ts ${PLAYWRIGHT_DIR}/playwright.config.ts

set -e

export COMPOSE_FILES_FLAG="-f ${PLAYWRIGHT_DIR}/docker-compose.yml
    -f  ${REPO_ROOT_DIR}/.devcontainer/db-docker-compose.yml"
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
