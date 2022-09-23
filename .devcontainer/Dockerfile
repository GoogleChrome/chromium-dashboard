# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.2/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon): 3, 3.10, 3.9, 3.8, 3.7, 3.6, 3-bullseye, 3.10-bullseye, 3.9-bullseye, 3.8-bullseye, 3.7-bullseye, 3.6-bullseye, 3-buster, 3.10-buster, 3.9-buster, 3.8-buster, 3.7-buster, 3.6-buster
ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \ 
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \ 
    # Playwright dependencies
    && sudo apt-get install -y libgtk-3-0 \
       libasound2 \
       libdrm2 \
       libgbm1 \
       libxcomposite1 \
       libxdamage1 \
       libxfixes3 \
       libxrandr2 \
       libxtst6 \
       libpangocairo-1.0-0 \
       libpango-1.0-0 \
       libatk1.0-0 \
       libcairo-gobject2 \
       libcairo2 \
       libgdk-pixbuf-2.0-0 \
       libdbus-glib-1-2 \
       libdbus-1-3 \
       libxcb-shm0 \
       libx11-xcb1 \
       libxcursor1 \
       libxi6

# [Optional] Uncomment this line to install global node packages.
RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g gulp-cli" 2>&1

# Setup the virtual environment
# Without this line, when opening the devcontainer for the first,
# it will not be able to find the path and the user will have to restart manually.
# RUN python3.9 -m venv cs-env \
#     && /workspace/cs-env/bin/python -m pip3 install pylint