# AI Release Notes Evaluation & Benchmarking: DevRel & Engineering Playbook

## 1. Overview & Mission

The **AI Release Notes Evaluation Framework** is a lightweight, offline benchmarking suite for evaluating, testing, and refining the AI prompt templates and model pipelines that generate Chrome release notes summaries.

### Why Evaluation Matters
Developer-facing release notes must be:
- **Concise & Scannable:** Strictly 40–80 words to keep release notes easy to digest.
- **Developer-Centric:** Focused on *what web developers can do*, rather than internal Chromium implementation details.
- **Free of Internal Blink Jargon:** Completely free of launch review terminology (e.g., `intent to ship`, `blink-dev`, `lgtm`, `I2S`, `chromestatus`).
- **Syntactically Clean:** Formatted with valid markdown, backticks around API identifiers (`popover`, `position-anchor`), and verified documentation links.

This evaluation suite allows **Chrome DevRel**, **Technical Writers**, and **Feature Owners** to rapidly iterate on prompt templates, benchmark candidate models, and catch regressions before changes reach production.

---

## 2. Codebase Map

| Component | File Path | Description |
| :--- | :--- | :--- |
| **Evaluation Runner** | `scripts/eval_summaries.py` | CLI tool that evaluates summaries against deterministic scoring rules and exports `eval_results_latest.json`. |
| **Prompt Comparator** | `scripts/evaluate_prompts.py` | CLI tool that runs multiple candidate prompt templates side-by-side against the benchmark suite. |
| **Benchmark Fixtures** | `scripts/eval_data/*.yaml` | Real-world feature test fixtures across CSS, Web APIs, on-device AI, and adversarial edge cases. |
| **Baseline Thresholds** | `scripts/baseline_scores.json` | Master configuration of target word counts, score thresholds, and forbidden Blink jargon phrases. |
| **Canonical Prompt** | `prompts/generate_release_notes.md` | Production Jinja2 prompt template used by `GeminiSummaryGenerator`. |
| **Unit Test Suite** | `scripts/eval_summaries_test.py` | Automated tests verifying scoring algorithms and mock generators. |

---

## 3. How to Run the Suite

All scripts can be executed inside the development container or local virtual environment (`. cs-env/bin/activate`).

### 3.1. Offline Mock Mode (Zero-Cost / Deterministic)
Runs evaluation instantly without requiring a `GEMINI_API_KEY` or network access:

```bash
python3 scripts/eval_summaries.py --offline-mock
```

**Example Output:**
```text
---------------------------------------------------------------------------------
Fixture                              | Words  | Jargon  | MD    | Score  | Status
---------------------------------------------------------------------------------
feature_css_anchor_positioning.yaml  | 37     | 0       | 1.00  | 100.0% | PASS  
feature_css_gap_decorations.yaml     | 30     | 0       | 1.00  | 95.7 % | PASS  
feature_insufficient_details.yaml    | 20     | 0       | 1.00  | 100.0% | PASS  
feature_popover_api.yaml             | 37     | 0       | 1.00  | 100.0% | PASS  
feature_prompt_api.yaml              | 31     | 0       | 1.00  | 96.6 % | PASS  
feature_spam_test.yaml               | 22     | 0       | 1.00  | 100.0% | PASS  
---------------------------------------------------------------------------------

Wrote evaluation results to eval_results_latest.json
```

### 3.2. Live Model Evaluation (with Gemini API)
To benchmark actual Gemini model responses across all fixtures using the production model (`gemini-3.1-pro-preview`, configured via `settings.SUMMARY_GENERATOR_MODEL`):

```bash
export GEMINI_API_KEY="your-gemini-api-key"
# Runs against the active production model: gemini-3.1-pro-preview
python3 scripts/eval_summaries.py --model gemini-3.1-pro-preview --verbose
```

---

## 4. How DevRel Can Add New Benchmark Features

To add a new feature to the evaluation benchmark suite, create a YAML file in `scripts/eval_data/feature_<name>.yaml`:

```yaml
name: View Transitions Multi-Page (MPA)
summary: >
  View Transitions for same-origin cross-document navigations (MPA) allows
  developers to create seamless visual page transitions across distinct HTML pages
  without requiring a Single-Page Application (SPA) architecture.
shipped_milestone: 126
spec_link: https://drafts.csswg.org/css-view-transitions-2/
doc_links:
  - https://developer.chrome.com/docs/web-platform/view-transitions/same-document
search_tags:
  - transitions
  - animation
  - navigation
  - mpa
standard_maturity: 2
category: 1
expected_keywords:
  - view transition
  - navigation
  - page
min_words: 40
max_words: 80
```

### YAML Schema Fields:
- `name` *(string, required)*: Official name of the feature.
- `summary` *(string, required)*: Feature description from ChromeStatus or specification explainer.
- `shipped_milestone` *(int/string)*: Target shipping Chrome milestone (e.g. `126`).
- `spec_link` *(string)*: Canonical W3C / WHATWG specification URL.
- `doc_links` *(list of strings)*: MDN or developer.chrome.com article links.
- `expected_keywords` *(list of strings)*: Key technical terms that should appear in the generated summary.
- `min_words` *(int, default 35)*: Minimum acceptable word count.
- `max_words` *(int, default 85)*: Maximum acceptable word count.

---

## 5. How to Iterate on Prompts and Compare Performance

When testing changes to prompt instructions, tone, or formatting:

1. Create a candidate prompt template file (e.g. `prompts/candidate_concise.md`).
2. Run `evaluate_prompts.py` to compare the candidate against the canonical production template:

```bash
python3 scripts/evaluate_prompts.py --prompts prompts/generate_release_notes.md prompts/candidate_concise.md
```

**Comparison Table Output:**
```text
Benchmarking 2 prompt template(s) against fixtures in scripts/eval_data...

=================================================================================
Prompt Template                            | Pass Rate  | Avg Words  | Avg Score 
=================================================================================
generate_release_notes.md                  | 100.0    % | 45.2       | 98.7     %
candidate_concise.md                       | 100.0    % | 38.4       | 94.2     %
=================================================================================
```

---

## 6. Scoring Dimensions & Quality Criteria

The evaluation engine computes an **Overall Composite Score (0–100%)** based on 4 weighted criteria:

### 1. Word Count Adherence (30% Weight)
- **Optimal Range:** 40 to 80 words.
- Penalties scale linearly for summaries that are too short (<30 words) or too verbose (>90 words).

### 2. Absence of Blink Jargon (30% Weight)
- **Zero Tolerance:** 0 jargon terms = 100% score.
- Forbidden terms configured in `scripts/baseline_scores.json`:
  - `intent to ship`
  - `intent to prototype`
  - `blink-dev`
  - `chromestatus`
  - `lgtm`
  - `i2s`
  - `i2p`
  - `tag review`
  - `launch bug`

### 3. Markdown Formatting Validity (20% Weight)
- Checks for balanced backticks (`` ` ``) around API names.
- Checks for balanced asterisks (`*`) for bolding/emphasis.
- Validates that markdown links are complete without broken URL syntax.

### 4. Technical Terminology Coverage (20% Weight)
- Matches the ratio of `expected_keywords` present in the generated output text.

---

## 7. Baseline Score Configuration

The `scripts/baseline_scores.json` file defines global benchmark settings:

```json
{
  "version": "1.0.0",
  "target_word_count_min": 40,
  "target_word_count_max": 80,
  "forbidden_jargon": [
    "intent to ship",
    "blink-dev",
    "chromestatus",
    "lgtm",
    "i2s"
  ]
}
```

To add new forbidden terms or adjust target word count boundaries, edit `scripts/baseline_scores.json` and re-run `python3 scripts/eval_summaries.py`.

---

## 8. Unit Testing & CI Verification

Run the test suite to verify scoring logic and mock generator integration:

```bash
# Run unit tests
python3 -m unittest scripts/eval_summaries_test.py

# Linting & code formatting
ruff check scripts/
ruff format --check scripts/
```
