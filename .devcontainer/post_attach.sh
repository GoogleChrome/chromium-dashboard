#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Setup Gemini & MCP Servers
# https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer#configure-mcp-servers
npm install -g @google/gemini-cli
GEMINI_CONFIG='{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}'
# Check if the user is authenticated to GitHub.
# If so, append the mcpServers section with the Github MCP server.
# If not, print out a warning message.
if gh auth status &>/dev/null; then
  echo "GitHub CLI authenticated. Adding GitHub MCP server to Gemini config."
  GH_TOKEN=$(gh auth token)
  GEMINI_CONFIG=$(echo "$GEMINI_CONFIG" | jq --arg token "$GH_TOKEN" '.mcpServers.github = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": $token
    }
  }')
else
  echo "WARNING: GitHub CLI not authenticated. GitHub MCP server will not be configured."
  echo "To configure the GitHub MCP Server, use 'gh auth login' and then reload (not rebuild) the devcontainer."
  echo "In the Command Palette, run: Developer: Reload Window"
fi

mkdir -p "$HOME/.gemini"
echo "$GEMINI_CONFIG" > "$HOME/.gemini/settings.json"

# Configure Gemini API Key if available
if [ -n "$GEMINI_API_KEY" ]; then
  echo "GEMINI_API_KEY found."
else
  echo "WARNING: GEMINI_API_KEY environment variable not set."
  echo "You may need to configure an API key manually to use certain Gemini features."
fi


echo "Note: After starting the Gemini CLI for the first time, it may present you with some errors."
echo "In that case, it will tell you to open a new terminal and start the Gemini CLI again."
