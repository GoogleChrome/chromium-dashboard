# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.245.2/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version (use -bullseye variants on local arm64/Apple Silicon): 3, 3.10, 3.9, 3.8, 3.7, 3.6, 3-bullseye, 3.10-bullseye, 3.9-bullseye, 3.8-bullseye, 3.7-bullseye, 3.6-bullseye, 3-buster, 3.10-buster, 3.9-buster, 3.8-buster, 3.7-buster, 3.6-buster
# Update 'VARIANT' to pick a version of Python: 3, 3.10, 3.9, 3.8, 3.7, 3.6
# Append -bullseye or -buster to pin to an OS version.
# Use -bullseye variants on local arm64/Apple Silicon.
ARG VARIANT="3.12-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT} as ide

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="18"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && sudo apt-get install -y \
       # openapi-generator-cli dependencies
       openjdk-17-jre \
       # Convenience tools
       bash-completion

# Install gcloud
ENV CLOUD_SDK_VERSION=497.0.0
# Install gcloud similarly to how it is done in cloud-sdk-docker
# https://github.com/GoogleCloudPlatform/cloud-sdk-docker/blob/master/debian_component_based/Dockerfile
RUN if [ `uname -m` = 'x86_64' ]; then echo -n "x86_64" > /tmp/arch; else echo -n "arm" > /tmp/arch; fi;
RUN ARCH=`cat /tmp/arch` && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${CLOUD_SDK_VERSION}-linux-${ARCH}.tar.gz && \
    tar xzf google-cloud-cli-${CLOUD_SDK_VERSION}-linux-${ARCH}.tar.gz && \
    rm google-cloud-cli-${CLOUD_SDK_VERSION}-linux-${ARCH}.tar.gz
RUN echo -n "beta" > /tmp/additional_components
RUN /google-cloud-sdk/install.sh --usage-reporting=false \
    --additional-components `cat /tmp/additional_components` && rm -rf /google-cloud-sdk/.install/.backup

RUN su vscode -c "echo 'PATH=${PATH}:/google-cloud-sdk/bin' >> ~/.bashrc"

RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g gulp-cli" 2>&1
