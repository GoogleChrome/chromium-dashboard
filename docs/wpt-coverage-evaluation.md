# AI-Powered Test Coverage Evaluation: Technical Reference

## Overview
The **AI-Powered Test Coverage Evaluation** system is a semi-automated pipeline
that audits the test coverage of a web platform feature. It utilizes a chain of
Gemini prompts to compare a feature's specification against its Web Platform
Tests (WPT).

Depending on the size of the test suite, the system dynamically selects between
a **Unified Flow** (single chain-of-thought prompt) or a **Complex Flow**
(multi-stage prompt chain) to optimize for context retention and processing
speed.

This feature is backed by **App Engine Task Queues** (Cloud Tasks)
to handle the long-running, asynchronous nature of LLM analysis and WPT content
fetching.


## Codebase Map

| Component | File Path | Description |
| :--- | :--- | :--- |
| **Frontend UI** | `client-src/elements/chromedash-wpt-eval-page.ts` | Handles user input validation, polling, and report rendering. |
| **Client Wrapper** | `framework/gemini_client.py` | Manages `google.genai` client, timeouts, and retries. |
| **Pipeline Logic** | `framework/gemini_helpers.py` | Orchestrates the branching pipeline (Unified vs. Batch) and formats prompts. |
| **API Handler** | `api/wpt_coverage_api.py` | Handles the POST request, permissions, and locking/throttling logic. |
| **WPT Fetching** | `framework/utils.py` | Handles GitHub API interaction, directory parsing, and URL normalization (e.g., `.any.js`). |
| **Task Handler** | `framework/gemini_helpers.py` | `GenerateWPTCoverageEvalReportHandler` executes the background task. |
| **Prompts** | `templates/prompts/` | Contains prompt templates sent in Gemini requests in the pipeline. |

---

## The Analysis Pipeline
The core logic resides in `run_wpt_test_eval_pipeline` within
`framework/gemini_helpers.py`.

### 1. Initialization & Fetching
* **Input:** The system accepts `wpt.fyi` URLs from the `wpt_descr` field.
* **Resolution:** It uses `utils.get_mixed_wpt_contents_async` to resolve these
URLs.
    * **Directories:** If a URL points to a directory, `utils._fetch_dir_listing`
    calls the GitHub API to list all files.
    * **Files:** Individual files are fetched via `raw.githubusercontent.com`.
    * **Normalization:** The system automatically converts `.any.worker.html`
    variants back to their source `.any.js` files using
    `utils.reformat_wpt_fyi_url`.
    * **Fallback:** If an `.html` file fetch fails, it attempts to fetch the
    equivalent `.js` file before giving up.

### 2. Branching Logic
Once files are fetched, the pipeline determines the strategy based on the
count of valid test files:
* **≤ 10 Files:** Executes **Path A (Unified Flow)**.
* **> 10 Files:** Executes **Path B (Complex Flow)**.

---

### Path A: Unified Flow (≤ 10 Files)
For smaller test suites, the risk of context overloading is low. A single prompt
is used to prevent the loss of nuance that can occur when summarizing individual
files in the multi-stage flow.

1.  **Prompt Assembly:** The system loads `templates/prompts/unified-gap-analysis.html`.
2.  **Context Injection:**
    * `<spec_document>`: The full text or diff of the specification.
    * `<feature_definition>`: The name and summary of the feature.
    * `<test_suite>`: All raw test files and dependencies are injected directly
      into the prompt context.
3.  **Execution:** A single request is sent to Gemini via
    `gemini_client.get_response_async`.
4.  **Chain-of-Thought:** The model is instructed to perform internal
    "scratchpad" phases (Scope Analysis, Spec Extraction, Test Verification)
    before generating the final Markdown report.
5.  **Result:** The response is returned directly as the final report.

---

### Path B: Complex Flow (> 10 Files)
For larger suites, the context window would be exceeded by a unified prompt.
The system uses `asyncio.gather` to run prompts concurrently and summarize data
step-by-step.

1.  **Batch Processing (Spec & Test Analysis):**
    * **Prompt Generation:** Iterates through every fetched WPT file and
      generates a `TEST_ANALYSIS` prompt for each.
    * **Spec Injection:** A `<` prompt is appended to the **end** of this list.
    * **Execution:** `GeminiClient.get_batch_responses_async` sends all prompts
      to Gemini simultaneously.
    * **Unpacking:**
        * The system pops the **last** response from the list (Spec Synthesis).
        * The remaining responses are collected as Test Analyses summaries.

2.  **Gap Analysis:**
    * The `spec_synthesis_response` and aggregated `test_analysis_responses` are
      combined into the `GAP_ANALYSIS` template.
    * This final step is executed via `gemini_client.get_response_async`.

---

## Configuration & Timeouts
The system is tuned to balance App Engine limits against LLM generation time.
These constants are defined in `framework/gemini_client.py`.

### Gemini Model
* **Model:** `gemini-3.0-pro-preview` (Hardcoded as `GEMINI_MODEL`).

### Timeout Strategy
To prevent "Task Deadline Exceeded" errors in Cloud Tasks, the system uses a
two-layer timeout approach:

1.  **Inner Timeout (`API_TIMEOUT_SECONDS = 175`)**: passed to the
`google.genai` SDK. If a single generation request takes longer than ~3 minutes,
the SDK raises an error, allowing our code to catch it and retry.
2.  **Outer Timeout (`ASYNC_TIMEOUT_SECONDS = 540`)**: The absolute maximum time
(9 minutes) the async wrapper will wait for a response. This safeguards the
background thread from hanging indefinitely.

---

## Retry Logic & Error Handling

### 1. Network/API Retries
The `GeminiClient` uses a custom decorator `@utils.retry` for synchronous calls,
and internal logic for async calls.
* **Max Retries:** 3 (`MAX_RETRIES`).
* **Backoff:** 2 seconds (`RETRY_BACKOFF_SECONDS`) - exponential.
* **Scope:** This handles transient network errors or 5xx errors from the Gemini
API.

### 2. The "Response Failed" Sentinel
The prompts are engineered to return a specific string if the LLM cannot process
the input (e.g., empty file content).
* **Detection:** `gemini_client.py` checks if `response.text` starts with
`RESPONSE FAILED` (case-insensitive).
* **Action:** It raises a `RuntimeError`, triggering the standard retry
mechanism. If it fails 3 times, the specific error from the model is logged.

### 3. Batch Resilience
In `get_batch_responses_async` (Path B), `asyncio.gather` is called with
`return_exceptions=True`.
* **Significance:** If *one* test file analysis fails (e.g., a specific file is
too large), it **does not** crash the entire pipeline. The error object is
returned in the list, logged in `run_wpt_test_eval_pipeline`, and skipped during
the final aggregation.

---

## API Locking & Throttling
The API endpoint (`api/wpt_coverage_api.py`) implements locking to prevent abuse
and race conditions.

### The "In-Progress" Lock
* **Condition:** `ai_test_eval_run_status == IN_PROGRESS`
* **Expiration:** 1 Hour.
* **Logic:** If a request is `IN_PROGRESS` but the
`ai_test_eval_status_timestamp` is older than 1 hour, the system assumes the
previous task crashed silently and allows a new request.

### The Cooldown
* **Condition:** `ai_test_eval_run_status == COMPLETE`
* **Duration:** 29 Minutes.
* **Logic:** Users cannot re-run the evaluation immediately after a success.
* **Response:** Returns HTTP `409 Conflict` with a `Retry-After` header
indicating the remaining seconds.

---

## Troubleshooting Guide

### 1. Developer sees HTTP 409 "Pipeline already running"
* **Cause:** A task is currently processing, or the "In-Progress" lock hasn't
expired.
* **Check:** Look at `ai_test_eval_status_timestamp` in the Datastore viewer.
* **Fix:** If the task is definitely dead but the lock is active, manually
update `ai_test_eval_run_status` to `FAILED` or wait for the 1-hour expiration.

### 2. Task fails with `PipelineError: No successful test analysis responses`
* **Cause (Path B):** The batch processing finished, but every single test
analysis prompt returned an exception or failure.
* **Check:** Verify `wpt_descr` contains valid URLs.
* **Check:** If using a directory, ensure the GitHub API token (`GITHUB_TOKEN`
in settings) is valid and not rate-limited. `utils.get_mixed_wpt_contents_async`
relies on this token to list directory contents.

### 3. Coverage report is empty or "Model reported failure"
* **Cause:** The Gemini model returned the `RESPONSE FAILED` sentinel.
* **Check:** View the Application Logs. `GeminiClient` logs
`Model returned failure sentinel: <reason>`.
* **Common Reason:** The fetched URL returned a 404, or the file content was
empty.

### 4. Tests for `.worker.html` or `.window.html` are missing
* **Cause:** The file fetching logic in `utils.py` might be failing to normalize
the URL.
* **Logic:** The system explicitly looks for `.any.` in the URL to convert it to
`.js`.
* **Fix:** Verify if the specific test file uses a naming convention not covered
by `reformat_wpt_fyi_url`.

### 5. `TimeoutError` in Logs
* **Cause:** The `ASYNC_TIMEOUT_SECONDS` (540s) was exceeded.
* **Context:** This usually happens if the Spec Synthesis (the largest prompt) +
Batch processing takes too long.
* **Fix:** If this happens frequently, consider reducing the number of
concurrent test files processed or increasing the timeout (though Cloud Tasks
has a hard 10-minute limit for HTTP requests).

### 6. Report generation fails immediately
* **Check Directory Depth:** The system does **not** scan subdirectories. If
    the user provided a directory URL that contains only subfolders but no
    files *directly* inside it, the file list will be empty, causing a
    `PipelineError`.
* **Check File Count:** If the directory contains >50 individual test files, the
pipeline will fail to run, and a generic error will populate the report contents
with an error message. E.g. "The number of individual Web Platform Test files
was too large for automated report generation."
