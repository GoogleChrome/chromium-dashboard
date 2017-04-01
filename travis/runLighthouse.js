/**
 * Copyright 2017 Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
'use strict';

const chalk = require('chalk');
const fetch = require('node-fetch'); // polyfill

const args = process.argv.slice(2);
const LH_TEST_URL = args[0];
const LH_MIN_PASS_SCORE = args[1];
const PR_NUM = process.env.TRAVIS_PULL_REQUEST;
const PR_SHA = process.env.TRAVIS_PULL_REQUEST_SHA;
const REPO_SLUG = process.env.TRAVIS_PULL_REQUEST_SLUG;

const CI_HOST = 'https://lighthouse-ci.appspot.com';
const API_KEY = process.env.API_KEY;
const RUNNERS = {chrome: 'chrome', wpt: 'wpt'};

/**
 * @param {!string} runner Where to run Lighthouse.
 */
function run(runner) {
  const data = {
    testUrl: LH_TEST_URL,
    minPassScore: Number(LH_MIN_PASS_SCORE),
    repo: {
      owner: REPO_SLUG.split('/')[0],
      name: REPO_SLUG.split('/')[1]
    },
    pr: {
      number: parseInt(PR_NUM, 10),
      sha: PR_SHA
    }
  };

  let endpoint;
  let body = JSON.stringify(data);

  switch (runner) {
    case RUNNERS.wpt:
      endpoint = `${CI_HOST}/run_on_wpt`;
      break;
    case RUNNERS.chrome: // same as default
    default:
      endpoint = `${CI_HOST}/run_on_chrome`;
      body = JSON.stringify(Object.assign({format: 'json'}, data));
  }

  fetch(endpoint, {
    method: 'POST',
    body,
    headers: {
      'Content-Type': 'application/json',
      'X-API-KEY': API_KEY // Keep usage tight for now.
    }
  })
  .then(resp => resp.json())
  .then(json => {
    let colorize = chalk.green;
    if (json.score < LH_MIN_PASS_SCORE) {
      colorize = chalk.red;
    }
    console.log(colorize('Lighthouse CI score:'), json.score);
  })
  .catch(err => {
    console.log(chalk.red('Lighthouse CI failed'), err);
    process.exit(1);
  });
}

// Run LH if this is a PR.
if (process.env.TRAVIS_EVENT_TYPE === 'pull_request') {
  run(RUNNERS.chrome);
}
