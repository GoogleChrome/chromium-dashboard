FROM mcr.microsoft.com/playwright:v1.35.1-jammy

# playwright already created this user
USER pwuser
WORKDIR /work
COPY --chown=pwuser:pwuser openapi /work/openapi/
COPY --chown=pwuser:pwuser gen /work/gen/
# Cache the infrequent but time consuming changes early
COPY --chown=pwuser:pwuser requirements.txt requirements.dev.txt package.json package-lock.json /work/
RUN npm ci && npx playwright install
# Copy the rest
COPY --chown=pwuser:pwuser . /work