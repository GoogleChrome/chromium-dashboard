// @ts-check
import { test, expect } from '@playwright/test';
import { exec } from 'child_process';
import { promisify } from 'util';

const execPromise = promisify(exec);

test('Demo 6: AI Pipeline Trust & Grounded Evaluation', async () => {
  // Guard to skip this demo script during standard automated E2E test runs
  if (!process.env.RUN_DEMO) {
    test.skip();
  }
  test.setTimeout(120000); // 2-minute runway for live Gemini evaluation

  console.log('[Demo 6] Executing offline evaluation pipeline (scripts/eval_summaries.py) on spam test dataset...');
  
  // We run the script inside the container's virtual environment (activated by the test runner)
  const command = './cs-env/bin/python3 scripts/eval_summaries.py --dataset scripts/eval_data/feature_spam_test.yaml --prompt-version 2';
  
  try {
    const { stdout, stderr } = await execPromise(command);
    console.log('[Demo 6] Evaluator stdout:\n', stdout);
    if (stderr) {
      console.error('[Demo 6] Evaluator stderr:\n', stderr);
    }
    
    // Assertions for pipeline trust and grounded evaluation PASS scorecard!
    expect(stdout).toContain('Average Clarity & Style: 5.00/5');
    expect(stdout).toContain('Average Accuracy & Drift: 5.00/5');
    expect(stdout).toContain('Average Links & Baseline: 5.00/5');
    expect(stdout).toContain('✅ E2E EVALUATION PASSED SUCCESFULLY!');
    console.log('[Demo 6] Offline evaluation pipeline successfully validated and PASS scorecard verified!');
  } catch (error) {
    console.error('[Demo 6] Evaluation execution failed:', error);
    throw error;
  }
});
