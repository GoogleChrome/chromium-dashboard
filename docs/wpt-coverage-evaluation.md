# AI-Powered Test Coverage Evaluation: Technical Reference

## Overview
The **AI-Powered Test Coverage Evaluation** system is a semi-automated pipeline that audits the test coverage of a web platform feature. It compares a feature's specification against its Web Platform Tests (WPT) using Gemini.

The core analysis logic is offloaded to the external [wpt-gen](https://github.com/GoogleChromeLabs/wpt-gen) library. Depending on the size of the test suite, `wpt-gen` dynamically selects between a **Unified Flow** (single prompt) or a **Complex Flow** (multi-stage prompt chain) to optimize for context retention and processing speed.

This feature is backed by **App Engine Task Queues** (Cloud Tasks) to handle the long-running, asynchronous nature of LLM analysis and WPT content fetching.

## Codebase Map

| Component | File Path | Description |
| :--- | :--- | :--- |
| **Frontend UI** | `client-src/elements/chromedash-wpt-eval-page.ts` | Handles user input validation, polling, and report rendering. |
| **Pipeline Logic** | `framework/gemini_helpers.py` | Thin wrapper that triggers the `wpt-gen` pipeline and saves the result. |
| **API Handler** | `api/wpt_coverage_api.py` | Handles the POST/DELETE requests, permissions, and locking/throttling logic. |
| **Task Handler** | `framework/gemini_helpers.py` | `GenerateWPTCoverageEvalReportHandler` executes the background task. |
| **External Library** | `wpt-gen` (installed via pip) | Encapsulates the entire analysis pipeline, including WPT fetching, prompt orchestration, and Gemini API interaction. |

*Note: `framework/utils.py` contains legacy WPT fetching functions (e.g., `get_mixed_wpt_contents_async`), but these are no longer used by the active pipeline, which delegates fetching to `wpt-gen`.*

---

## The Analysis Pipeline

The pipeline is triggered asynchronously via Cloud Tasks.

1.  **Trigger:** A user clicks "Evaluate test coverage" on the frontend, which calls the `WPTCoverageAPI` (POST).
2.  **Task Enqueue:** The API validates the request and enqueues a task to `/tasks/generate-wpt-coverage-analysis`.
3.  **Execution:** `GenerateWPTCoverageEvalReportHandler` handles the task and calls `run_wpt_test_eval_pipeline` in `framework/gemini_helpers.py`.
4.  **External Call:** `run_wpt_test_eval_pipeline` calls `generate_audit_report` from the `wptgen` library, passing:
    *   `feature_id`: The ID of the feature.
    *   `provider`: 'gemini'.
    *   `api_key`: The Gemini API key from settings.
    *   `explainer_urls`: A list of explainer URLs if the user chose to include them.
5.  **Audit Report Generation (`wpt-gen`):**
    *   `wpt-gen` fetches the feature details and spec from the dashboard API (or uses passed info).
    *   `wpt-gen` resolves WPT URLs, fetches test contents, and normalizes them.
    *   `wpt-gen` runs the Gemini analysis (Unified or Complex flow depending on test suite size).
6.  **Storage:** The returned markdown report is saved to `feature.ai_test_eval_report`, and the status is updated to `COMPLETE`.

---

## Configuration & Timeouts

Since the analysis logic resides in `wpt-gen`, most configuration (model selection, prompt templates, timeouts, and retries) is managed internally by that library.

### API Key
*   The system requires `GEMINI_API_KEY` to be configured in `settings.py`. This key is exposed to the environment for the `google.genai` SDK used by `wpt-gen`.

---

## API Locking & Throttling

The API endpoint (`api/wpt_coverage_api.py`) implements locking and cooldowns to prevent abuse and resource exhaustion.

### Permissions & Constraints
*   **Access:** Only users with edit permissions for the feature and who are logged in with Google or Chromium accounts can trigger the analysis.
*   **Confidentiality:** Confidential features are blocked from using this tool to prevent leaking sensitive information to the LLM.

### The "In-Progress" Lock
*   **Condition:** `ai_test_eval_run_status == IN_PROGRESS`
*   **Expiration:** 59 Minutes.
*   **Logic:** If a request is `IN_PROGRESS` but the `ai_test_eval_status_timestamp` is older than 59 minutes, the system assumes the previous task hung and allows a new request (which will display as a retry button in the UI).

### The Cooldown
*   **Condition:** `ai_test_eval_run_status == COMPLETE` or `DELETED`
*   **Duration:** 29 Minutes.
*   **Logic:** Users cannot re-run the analysis immediately after a success or deletion.
*   **Response:** Returns HTTP `409 Conflict` with a `Retry-After` header indicating the remaining seconds.

---

## Troubleshooting Guide

### 1. Developer sees HTTP 409 "Pipeline already running" or "on cooldown"
*   **Cause:** A task is currently processing, or the cooldown period hasn't expired.
*   **Check:** Check the `ai_test_eval_run_status` and `ai_test_eval_status_timestamp` in the Datastore.
*   **Fix:** Wait for the cooldown to expire, or if the task is hung, wait for the 59-minute timeout. For local development, you can manually reset these fields in the Datastore emulator.

### 2. Task fails with "Failed to generate WPT coverage report"
*   **Cause:** An error occurred within the `wpt-gen` library (e.g., API failure, fetching failure).
*   **Check:** Check the App Engine logs for errors raised by `wptgen.generate_audit_report`.
*   **Common reasons:**
    *   Invalid `GEMINI_API_KEY`.
    *   Rate limiting on the Gemini API or GitHub API (used by `wpt-gen` for fetching).
    *   The spec URL is invalid or inaccessible.

### 3. Report generation fails immediately due to WPT URL issues
*   **Subdirectories:** The system does not scan subdirectories of listed WPT directories. Ensure tests are directly in the listed directory.
*   **File Count Limit:** There is a limit of 50 individual test files. If the listed WPT URLs resolve to more than 50 files, `wpt-gen` may fail or the UI will warn about it.
