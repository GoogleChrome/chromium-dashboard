/**
 * Copyright 2024 Google LLC
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

import {assert, fixture} from '@open-wc/testing';

import {ChromedashFeaturePagination} from './chromedash-feature-pagination';

describe('chromedash-feature-pagination', () => {
  let el: ChromedashFeaturePagination;

  beforeEach(async () => {
    el = await fixture<ChromedashFeaturePagination>(
      '<chromedash-feature-pagination></chromedash-feature-pagination>'
    );
    el.totalCount = 20;
    el.start = 10;
    el.pageSize = 2;

    await el.updateComplete;
  });

  it('can be added to the page', async () => {
    assert.exists(el);
    assert.instanceOf(el, ChromedashFeaturePagination);
  });

  it('renders navigation buttons', async () => {
    const previous = el.shadowRoot!.querySelector('#previous');
    assert.exists(previous);

    const jump_1 = el.shadowRoot!.querySelector('#jump_1');
    assert.notExists(jump_1);
    const jump_2 = el.shadowRoot!.querySelector('#jump_2');
    assert.notExists(jump_2);
    const jump_3 = el.shadowRoot!.querySelector('#jump_3');
    assert.exists(jump_3);
    const jump_4 = el.shadowRoot!.querySelector('#jump_4');
    assert.exists(jump_4);
    const jump_5 = el.shadowRoot!.querySelector('#jump_5');
    assert.exists(jump_5);
    const jump_6 = el.shadowRoot!.querySelector('#jump_6');
    assert.exists(jump_6);
    const jump_7 = el.shadowRoot!.querySelector('#jump_7');
    assert.exists(jump_7);
    const jump_8 = el.shadowRoot!.querySelector('#jump_8');
    assert.exists(jump_8);
    const jump_9 = el.shadowRoot!.querySelector('#jump_9');
    assert.exists(jump_9);
    const jump_10 = el.shadowRoot!.querySelector('#jump_10');
    assert.notExists(jump_10);

    const next = el.shadowRoot!.querySelector('#next');
    assert.exists(next);
  });

  it('renders standard options for items-per-page', async () => {
    const opt_25 = el.shadowRoot!.querySelector('#opt_25');
    assert.exists(opt_25);
    const opt_50 = el.shadowRoot!.querySelector('#opt_50');
    assert.exists(opt_50);
    const opt_77 = el.shadowRoot!.querySelector('#opt_77');
    assert.notExists(opt_77);
    const opt_100 = el.shadowRoot!.querySelector('#opt_100');
    assert.exists(opt_100);
  });
});
