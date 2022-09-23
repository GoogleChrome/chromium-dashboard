# Development Container For Chromium Dashboard

[Devcontainers](https://containers.dev/) provide a way for

Currently, the devcontainer setup leverages docker compose to setup two containers:
1. The main development container which contains:
  - Node and Python
2. Datastore emulator
3. Datastore emulator viewer

## Using the Devcontainer


| Service | Click The Badge | Requirements |
|-----|-----|-----|
| [Visual Studio Code Remote - Containers](https://code.visualstudio.com/docs/remote/create-dev-container) | [![Open in Remote - Containers](https://img.shields.io/static/v1?label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/microsoft/vscode-remote-try-java) | Locally: Docker and Visual Studio Code |
| [GitHub Codespaces](https://docs.github.com/en/enterprise-cloud@latest/codespaces) | [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](COPIED-URL) | Codespaces |

Upon creating the devcontainer, `npm run setup` is ran automatically.

Most commands from the root README.md work as-is. There are some exceptions due to the database container being outside the main dev container.

| Local | DevContainer |
|-------|------|
| `npm test` | `npm run do-tests` |
| `npm start` | `npm run start-app` |

## Upgrading versions of Node and Python

In the docker-compose.yml file:
- For Python: Change the `VARIANT` argument to the appropirate [variant](https://github.com/microsoft/vscode-dev-containers/tree/main/containers/python-3)
- For Node: Change the `NODE_VERSION` to the appropriate version used by [nvm](https://github.com/nvm-sh/nvm)


## Curent limitations

It starts the datastore with 