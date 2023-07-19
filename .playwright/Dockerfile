FROM mcr.microsoft.com/playwright:v1.35.1-jammy
ARG UID
ARG GID

WORKDIR /work
RUN useradd pwuser -u $UID -g $GID -m -s /bin/bash || true && \
    mkdir /work/node_modules && \
    chown -R pwuser /work/
USER pwuser