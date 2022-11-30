# Development Container For Chromium Dashboard

[Devcontainers](https://containers.dev/) provide a way for developers with an
IDE. Like regular containers, devcontainers can be packaged with the
appropriate tool versions, extensions, build & test targets out of the box.

Currently, the devcontainer setup leverages docker compose to setup two
containers:

1. The main development container which contains:
    - Node and Python
2. [Datastore Emulator](https://cloud.google.com/datastore/docs/tools/datastore-emulator)
3. [Datastore Emulator viewer](https://github.com/remko/dsadmin)

## Using the Devcontainer on macOS

An extra step is required for Devcontainer on Mac:
- Click on the Docker icon, go to `Preferences`
- Go to the Resources tab and select FILE SHARING
- Add `/workspaces` to the mountable directories
- Click on Apply & Restart

## Using the Devcontainer

You can click on the appropriate badge to get the environment setup:

| Service | Click The Badge | Requirements | Pros | Cons |
|-----|-----|-----|-----|-----|
| [Visual Studio Code Remote - Containers](https://code.visualstudio.com/docs/remote/create-dev-container) | [![Open in Remote - Containers](https://img.shields.io/static/v1?label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/GoogleChrome/chromium-dashboard) | Locally: Docker and Visual Studio Code | Runs locally. Have more resources | Need to have VS Code and Docker setup |
| [GitHub Codespaces](https://docs.github.com/en/enterprise-cloud@latest/codespaces) | <ul><li>East US[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=8633551&machine=standardLinux32gb&location=EastUs&devcontainer_path=.devcontainer%2Fdevcontainer.json)</li><li>West US[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=8633551&machine=standardLinux32gb&location=WestUs2&devcontainer_path=.devcontainer%2Fdevcontainer.json)</li></ul> | Access to Codespaces | Nothing to install locally | Limited resources: 4 cores, 8GB RAM, 32GB Storage |

Upon creating the devcontainer by clicking the appropriate badge, `npm run setup` is ran automatically.

*Note*: Sometimes when you open the terminal, it won't automatically activate
the python environment. Either 1) Open a new terminal (usually it works the
second time) or 2) manually activate it by running `source cs-env/bin/activate`

Most commands from the root README.md work as-is. There are some exceptions
due to the database container being outside the main dev container.

| Local | DevContainer |
|-------|------|
| `npm test` | `npm run do-tests` |
| `npm start` | `npm run start-app` |

## Accessing the various services

To access the database, database viewer or the app when it is running, go to
the "Ports" section next to the "Terminal". Find the Port you are looking for
and click on the corresponding Local Address.

There are other ports needed for the IDE itself but mainly, you only need to watch:

| Port | Service |
|------|---------|
| 15606| Datastore Emulator |
| 8888 | Datastore Viewer |
| 8080 | Application (when running)|
| 8000 | Webtest (when running) |

## Upgrading versions of Node and Python

In the docker-compose.yml file:
- For Python: Change the `VARIANT` argument to the appropirate [variant](https://github.com/microsoft/vscode-dev-containers/tree/main/containers/python-3)
- For Node: Change the `NODE_VERSION` to the appropriate version used by [nvm](https://github.com/nvm-sh/nvm)

## Troubleshooting

When there are depedency changes and environment changes in requirements.txt or package.json, the Devcontainer needs to be rebuilt:
- `rm -rf node_modules cs-env` in terminal
- View -> Command Palette -> Rebuild container without cache
