ARG PLAYWRIGHT_VERSION

FROM mcr.microsoft.com/playwright:v${PLAYWRIGHT_VERSION}-jammy

ARG USERID
ARG GROUPID


USER root
# playwright already created this user. Delete it and use the UID & GID from the host
RUN userdel -r pwuser && \
    groupadd -g $GROUPID pwuser && \
    useradd pwuser -u $USERID -g $GROUPID -m -s /bin/bash && \
    mkdir -p /work/tests/__screenshots__ && \
    mkdir -p /work/test-results && \
    chown -R pwuser /work

RUN npm config set script-shell bash --global

USER pwuser
WORKDIR /work

# Install a consistent version of Playwright. The duplicate ARG line is needed to copy the value
# into this build stage.
ARG PLAYWRIGHT_VERSION
RUN npm install @playwright/test@${PLAYWRIGHT_VERSION}

# Copy the root directory. Subdirectories are mounted in docker-compose.yml.
COPY --chown=pwuser:pwuser wait-for-app.sh playwright.config.cjs /work/
