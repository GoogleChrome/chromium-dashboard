FROM mcr.microsoft.com/playwright:v1.39.0-jammy

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
# Currently, no need to run `npm install` because currently the docker image mcr.microsoft.com/playwright
# has playwright libraries already installed. Revisit if other dependencies are added to this package.json.
# Copy everything (which includes the test files).
COPY --chown=pwuser:pwuser . /work
