# Copyright 2025 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM mcr.microsoft.com/devcontainers/base:bookworm as ide

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && sudo apt-get install -y \
       bash-completion

# Install gcloud
ENV CLOUD_SDK_VERSION=542.0.0
# Install gcloud similarly to how it is done in cloud-sdk-docker
# https://github.com/GoogleCloudPlatform/cloud-sdk-docker/blob/master/debian_component_based/Dockerfile
RUN if [ `uname -m` = 'x86_64' ]; then echo -n "x86_64" > /tmp/arch; else echo -n "arm" > /tmp/arch; fi;
RUN ARCH=`cat /tmp/arch` && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${CLOUD_SDK_VERSION}-linux-${ARCH}.tar.gz && \
    tar xzf google-cloud-cli-${CLOUD_SDK_VERSION}-linux-${ARCH}.tar.gz && \
    rm google-cloud-cli-${CLOUD_SDK_VERSION}-linux-${ARCH}.tar.gz
RUN echo -n "beta" > /tmp/additional_components
RUN /google-cloud-sdk/install.sh --usage-reporting=false \
    --additional-components `cat /tmp/additional_components` && rm -rf /google-cloud-sdk/.install/.backup

USER vscode

RUN echo 'PATH=${PATH}:/google-cloud-sdk/bin' >> ~/.bashrc
