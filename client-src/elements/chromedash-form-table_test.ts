/**
 * Copyright 2026 Google LLC
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
import {html} from 'lit';
import {ChromedashFormTable} from './chromedash-form-table.js';
import {slotAssignedElements} from './utils.js';

describe('chromedash-form-table', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-form-table></chromedash-form-table>`
    );
    assert.exists(component);
    assert.instanceOf(component, ChromedashFormTable);
    const formContents = component.renderRoot.querySelector('*');
    assert.exists(formContents);
  });

  it('renders with array of slots for rows', async () => {
    const component: ChromedashFormTable = await fixture(
      html` <chromedash-form-table>
        <span>Row 1</span>
        <span>Row 2</span>
      </chromedash-form-table>`
    );
    assert.exists(component);
    await component.updateComplete;

    const children = slotAssignedElements(component, '');

    const firstRow = children[0];
    assert.exists(firstRow);
    assert.include(firstRow.innerHTML, 'Row 1');

    const secondRow = children[1];
    assert.exists(secondRow);
    assert.include(secondRow.innerHTML, 'Row 2');
  });
});
