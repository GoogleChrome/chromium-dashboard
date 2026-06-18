# AI Release Notes Summary Generation - Local Testing & Iteration Guide

This guide explains how to run, test, and iterate on the AI-assisted release notes summary generator locally. 

The CLI tool allows DevRel to fetch feature details via HTTP from any ChromeStatus environment (local, staging, or production), run the ADK (Agent Development Kit) summary agent locally, and inspect the generated summaries, documentation links, and baseline statuses without needing direct database access.

---

## Prerequisites

### 1. Setup Virtual Environment
Ensure your Python environment is set up and all required packages are installed:
```bash
make setup
```
This initializes `cs-env/` and installs dependencies from `requirements.txt` (including `google-adk` and `httpx-sse`).

### 2. Configure Gemini API Key
The generator requires a Gemini API key. You can set it in two ways:

*   **File-based (Recommended for local dev)**: Create a file named `gemini_api_key.txt` in the root of the project containing your API key:
    ```bash
    echo "your-api-key-here" > gemini_api_key.txt
    ```
*   **Environment Variable**: Set the `GEMINI_API_KEY` environment variable:
    ```bash
    export GEMINI_API_KEY="your-api-key-here"
    ```

---

## Running the CLI Script

The script `scripts/generate_summary.py` fetches feature data from a server via the public HTTP API, runs the local agent, and prints the suggestions to the console.

### Running Against Production Features
To test the prompt and agent against a real feature in production (e.g. feature ID `5149560434589696`):
```bash
./cs-env/bin/python3 scripts/generate_summary.py \
  --host https://chromestatus.com \
  --feature_id 5149560434589696
```

### Running Against Localhost
If you are running the ChromeStatus App Engine server locally (`npm start` or standard server at `http://localhost:8080`):
```bash
./cs-env/bin/python3 scripts/generate_summary.py \
  --feature_id <local_feature_id>
```

### Options
*   `--host`: Domain with protocol pointing to the server to fetch feature data from (defaults to `http://localhost:8080`).
*   `--feature_id`: **(Required)** The database ID of the feature.
*   `--write`: Simulated run showing what would be sent back to the server in `POST` (currently a dry-run log).

---

## Iterating on Prompt Style & Instructions

The prompt and technical writing guidelines are stored in a Markdown template in the repository:
`framework/prompts/v1.md`

To update the writing style, word restrictions, or instructions:
1.  Open [v1.md](file:///usr/local/google/home/jamescscott/code/chromium-dashboard/framework/prompts/v1.md).
2.  Add or modify guidelines (e.g. adjusting sentence limits, tone requirements, or forbidden terms).
3.  Run `scripts/generate_summary.py` again to evaluate the output quality.

---

## Under the Hood

1.  **XSSI Prefix Stripping**: The script automatically handles Google's XSSI protection prefix (`)]}'\n`) returned by ChromeStatus JSON endpoints.
2.  **Tool Calling**: The agent uses two local tools to fetch and verify references:
    *   `search_mdn`: Queries Mozilla Developer Network for matching APIs/docs.
    *   `verify_link`: Validates that suggested links resolve to HTTP 200 OK.
3.  **JSON Mode**: The agent is instructed to output a raw JSON structure conforming to the `SummaryResponseSchema` model.
