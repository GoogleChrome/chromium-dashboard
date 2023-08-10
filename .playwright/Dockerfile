FROM mcr.microsoft.com/playwright:v1.35.1-jammy

ARG USERID
ARG GROUPID

USER root
# playwright already created this user. Delete it and use the UID & GID from the host
RUN userdel -r pwuser && \
    groupadd -g $GROUPID pwuser && \
    useradd pwuser -u $USERID -g $GROUPID -m -s /bin/bash && \
    mkdir -p /work/client-src/elements/__screenshots__ && \
    mkdir -p /work/test-results && \
    mkdir -p /work/playwright-report && \
    chown -R pwuser /work

USER pwuser
WORKDIR /work
COPY --chown=pwuser:pwuser openapi /work/openapi/
COPY --chown=pwuser:pwuser gen /work/gen/
# Cache the infrequent but time consuming changes early
COPY --chown=pwuser:pwuser requirements.txt requirements.dev.txt package.json package-lock.json /work/
RUN npm ci && npx playwright install
# Copy the rest
COPY --chown=pwuser:pwuser . /work
