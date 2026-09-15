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

# Set environment variable so we can tell we're performing Playwright tests.
ENV PLAYWRIGHT_MODE=true

# Install consistent versions of Playwright and Axe. The duplicate ARG lines are needed
# to copy values into this build stage.
ARG PLAYWRIGHT_VERSION
ARG AXE_CORE_PLAYWRIGHT_VERSION
RUN npm install @playwright/test@${PLAYWRIGHT_VERSION} @axe-core/playwright@${AXE_CORE_PLAYWRIGHT_VERSION}

# Copy the root directory. Subdirectories are mounted in docker-compose.yml.
COPY --chown=pwuser:pwuser wait-for-app.sh playwright.config.ts /work/

# The playwright.config.ts file is copied from the repository root, where it is
# needed for VS Code integration. Inside the container, the test directory is
# the root, so we update the path.
RUN sed -i "s|testDir: 'packages/playwright/tests'|testDir: '.'|" /work/playwright.config.ts
