# AI Summaries Quality Evaluation Guide

This folder contains the ground-truth feature datasets used to evaluate and prevent regressions in the AI summary suggestion engine.

---

## 1. How the Evaluation Works

We use an **LLM-as-a-Judge** pipeline to compare the AI-generated release summaries against human-authored reference text. The evaluator grades results on a highly standardized **1-5 Likert scale** across three core vectors.

To ensure reproducibility and objectivity, the judge prompt explicitly defines every score point (1, 2, 3, 4, 5) for all vectors. For a detailed breakdown of the grading rubric, see the [Evaluation Framework Design Doc](file:///usr/local/google/home/jamescscott/.gemini/jetski/brain/25b0314c-6453-4f2b-ab3c-8a48a1afa32b/evaluation_framework_design.md).

1.  **Clarity & Style**: Verifies length (exactly 2-3 sentences), objective tone, developer focus, and the complete absence of prohibited marketing terms.
2.  **Accuracy & Drift**: Ensures technical facts match the raw summary and no feature capabilities are hallucinated.
3.  **Links & Baseline**: Validates that discovered MDN documentation links are highly relevant and browser compatibility Baseline status matches the ground truth.

---

## 2. Iterating on AI Prompts

The system prompt is versioned. The current active template is located at:
📄 **[framework/prompts/v1.md](file:///usr/local/google/home/jamescscott/code/chromium-dashboard/framework/prompts/v1.md)**

If you want to edit instructions or constraints:
1.  Create a copy of the active prompt, incrementing the version:
    `framework/prompts/v2.md`
2.  Tweak the instructions in the new markdown file.
3.  Run the evaluation script specifying the new version (see below) to make sure scores do not regress.

---

## 3. Adding New Ground-Truth Features

To add a new feature to the evaluation dataset, create a new YAML file inside this folder (e.g., `scripts/eval_data/feature_web_locks.yaml`). 

While both JSON and YAML formats are supported by the loader, **YAML is highly preferred** because it natively supports clean multiline text blocks (using the `|` literal scalar), making long summaries extremely easy to read and write without escaping quotes or inserting `\n` characters:

```yaml
- name: Web Locks API
  category: 7
  web_feature: web-locks
  summary: Allows web applications to asynchronously acquire a lock, hold it while work is performed, then release it.
  explainer_links:
    - https://github.com/w3c/web-locks
  spec_link: https://w3c.github.io/web-locks/
  gt_summary: |
    The Web Locks API allows scripts running in different tabs or workers to asynchronously acquire a lock, preventing concurrent resource mutations. This helps coordinate shared storage access without blocking the main execution thread.
  gt_links:
    - https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API
  gt_baseline: widely
```

*Note: For the `category` integer, map it to the categories defined in `internals/core_enums.py`.*

### 3.1. Ground-Truth Schema Reference

Every test case file (typically `.yaml` or `.json`) must contain a list containing a single feature object under test. The fields are defined as follows:

| Field Name | Type | Required? | Description |
| :--- | :--- | :--- | :--- |
| `name` | string | **Yes** | The user-facing name of the feature (e.g., `"Popover API"`). |
| `category` | string or integer | **Yes** | The category of the feature. Can be declared as a readable string name (e.g., `'CSS'`, `'JavaScript'`, `'Web Components'`) or its official integer ID. Strings are resolved case-insensitively (and common abbreviations like `'JS'` are supported), mapping back to the official IDs in [internals/core_enums.py](file:///usr/local/google/home/jamescscott/code/chromium-dashboard/internals/core_enums.py). |
| `summary` | string | **Yes** | The raw, brief, or poorly-drafted summary of the feature stored in the ChromeStatus database. This acts as the primary input for the AI generator. |
| `explainer_links` | array (strings) | No | A list of URLs pointing to explainer documents, GitHub issues, or design docs. |
| `spec_link` | string | No | The URL pointing to the official specification draft (e.g., W3C or WHATWG drafts). |
| `gt_summary` | string | **Yes** | The human-authored, high-quality, ground-truth reference summary. The LLM judge compares the AI summary against this for accuracy, tone, and length. |
| `gt_links` | array (strings) | **Yes** | The high-quality documentation links (usually MDN or web.dev) we expect the AI to discover and include in its suggestion. |
| `gt_baseline` | string | **Yes** | The ground-truth WebDX Baseline status of the feature. Must be one of: `"limited"`, `"newly"`, or `"widely"`. |
| `web_feature` | string | No | **(Optional)** The official WebDX Feature ID from `webstatus.dev` (e.g., `"popover"`, `"anchor-positioning"`). Maps directly to the `web_feature` field on ChromeStatus's `FeatureEntry` model, providing clear traceability to the WebDX compat ecosystem. |

---

## 4. Running the Quality Suite

Run all evaluations using the local Python environment.

### Run Default Evaluation (Single Pass)
```bash
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/
```

### Run Statistical Evaluation (Multiple Iterations)
Since LLM outputs are non-deterministic, you should run evaluations multiple times to compute statistical metrics (**Min/Avg/Median/Max**). This is crucial for catching flakiness and unstable prompts:
```bash
# Run 3 iterations per feature (Recommended for local dev)
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/ --iterations 3
```

### Save/Update Baseline Metrics
When you have finalized a prompt improvement and want to establish its scores as the **new gold standard**, manually export the baseline scores. Run a high-iteration pass to ensure statistical stability, and commit the updated JSON file to VCS:
```bash
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/ --iterations 5 --output-results scripts/baseline_scores.json
```

### Run and Compare (Regression Check)
After making edits to a new prompt file (e.g. `v2.md`), run the evaluation against your baseline:
```bash
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/ --prompt-version 2 --iterations 3 --compare-with scripts/baseline_scores.json
```

### The E2E Pass/Fail Gatekeeping Engine
The script acts as a formal CI/CD gatekeeper and will exit with a **non-zero exit code (1)** if any quality gates are violated, and **exit code (0)** only when successful.

A run is declared a **FAILURE** if:
1.  **Gate 1 (Quality Floor)**: The dataset-wide average score for Clarity or Accuracy drops below **4.0/5**.
2.  **Gate 2 (Robustness Floor)**: The *minimum* score for any individual run across all features drops below **3.0/5** (blocks flaky prompts).
3.  **Gate 3 (Regression Check)**: The average score drops by more than the tolerance of **0.2** points compared to the baseline.

```
=== Regression Comparison ===
[+] Feature "Popover API": No regressions detected.
[-] REGRESSION in feature "CSS Anchor Positioning":
    * clarity: 5 -> 3 (-2)
```

---

## 5. Local UI Testing and Manual Verification

When testing the ChromeStatus Releases Page dashboard, review dialogs, and feature-detail banners locally, you need actual draft suggestion data populated in your local Datastore emulator.

We provide a manual verification bash script to instantly generate and insert suggestions:

### Generate & Save a Suggestion Locally
```bash
./scripts/manual_test_summary.sh <feature_id>
```

### What this script does:
1. Connects to your running local Datastore emulator (`localhost:15606`).
2. Fetches the feature data via HTTP API.
3. Invokes the local Gemini summary generator engine to generate summary text, MDN documentation links, and baseline compatibility status.
4. Directly inserts or overwrites a `FeatureSummarySuggestion` entity in the local Datastore in `COMPLETE` status.

Once run, you can immediately open your local frontend browser dashboard, view the new suggestion card on the Releases Page, and open the Review Dialog to perform full apply/edit/discard and bypass workflow tests.
