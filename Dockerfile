ARG PYTHON_VARIANT=3.12-bullseye
FROM python:${PYTHON_VARIANT} as app

RUN groupadd -g 1001 appuser && \
    useradd appuser -u 1001 -g 1001 -m -d /home/appuser -s /bin/bash

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    # openapi-generator-cli dependencies
    && apt-get install -y openjdk-17-jre

USER appuser

# Install node
ENV NVM_DIR=/home/appuser/.nvm \
    # Need the full major.minor.patch version for NODE_VERISON
    # https://nodejs.org/en/download/releases
    NODE_VERSION=18.17.1

RUN mkdir /home/appuser/.nvm && \
    curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.4/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default \
    && npm config set script-shell bash

ENV NODE_PATH=$NVM_DIR/v$NODE_VERSION/lib/node_modules \
    PATH="${PATH}:$NVM_DIR/versions/node/v$NODE_VERSION/bin"

WORKDIR /workspace
# Cache the infrequent but time consuming changes early
COPY --chown=appuser:appuser requirements.txt requirements.dev.txt package.json package-lock.json /workspace/
COPY --chown=appuser:appuser openapi /workspace/openapi/
COPY --chown=appuser:appuser gen /workspace/gen/
RUN npm install -g gulp-cli && npm run setup && cs-env/bin/python -m pip install debugpy==1.6.7.post1
# Copy the rest
COPY --chown=appuser:appuser . /workspace
