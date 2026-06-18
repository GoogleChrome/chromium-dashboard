# AI Summaries Quality Evaluation Guide

This folder contains the ground-truth feature datasets used to evaluate and prevent regressions in the AI summary suggestion engine.

---

## 1. How the Evaluation Works

We use an **LLM-as-a-Judge** pipeline to compare the AI-generated release summaries against human-authored reference text. The evaluator grades results on a **1-5 scale** across three core vectors:

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

To add a new feature to the evaluation dataset, create a new JSON file inside this folder (e.g., `scripts/eval_data/feature_web_locks.json`):

```json
[
  {
    "name": "Web Locks API",
    "category": 7,
    "summary": "Allows web applications to asynchronously acquire a lock, hold it while work is performed, then release it.",
    "explainer_links": ["https://github.com/w3c/web-locks"],
    "spec_link": "https://w3c.github.io/web-locks/",
    "gt_summary": "The Web Locks API allows scripts running in different tabs or workers to asynchronously acquire a lock, preventing concurrent resource mutations. This helps coordinate shared storage access without blocking the main execution thread.",
    "gt_links": ["https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API"],
    "gt_baseline": "widely"
  }
]
```

*Note: For the `category` integer, map it to the categories defined in `internals/core_enums.py`.*

---

## 4. Running the Quality Suite

Run all evaluations using the local Python environment:

### Run Default Evaluation
```bash
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/
```

### Save Baseline Metrics
Before editing prompts or core generator logic, export the baseline scores:
```bash
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/ --output-results scripts/eval_data/baseline.json
```

### Run and Compare (Regression Check)
After making edits to your new prompt file (e.g. `v2.md`), run the evaluation against the baseline to verify quality:
```bash
./cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/ --prompt-version 2 --compare-with scripts/eval_data/baseline.json
```

The script will automatically compute the score differences and report any regressions (e.g., if clarity or accuracy scores drop):

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
