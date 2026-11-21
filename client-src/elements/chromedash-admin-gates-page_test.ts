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
import {DefaultApi, GateDefAdmin} from 'chromestatus-openapi';
import {html} from 'lit';
import sinon, {SinonStub} from 'sinon';
import type SlButton from '@shoelace-style/shoelace/dist/components/button/button.js';
import type SlTextarea from '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import './chromedash-toast.js';
import './chromedash-admin-gates-page.js';
import type {ChromedashAdminGatesPage} from './chromedash-admin-gates-page.js';

const MOCK_GATES: GateDefAdmin[] = [
  {
    gate_type: 4,
    name: 'Intent to Ship',
    description: 'Three API Owners must approve your intent',
    team_name: 'API Owners',
    rule: 'Three LGTMs',
    approvers: ['owner@chromium.org'],
    is_editable: false,
    approvers_url: 'https://example.com/API_OWNERS',
    escalation_email: undefined,
    rotation_url: undefined,
    slo_initial_response: 5,
    slo_resolve: 10,
  },
  {
    gate_type: 34,
    name: 'Privacy Ship Review',
    description: 'Privacy Ship Review',
    team_name: 'Privacy',
    rule: 'One LGTM',
    approvers: ['privacy1@example.com', 'privacy2@example.com'],
    is_editable: true,
    approvers_url: undefined,
    escalation_email: 'privacy-escalation@example.com',
    rotation_url: 'https://rotation.example.com/privacy',
    slo_initial_response: 6,
    slo_resolve: 10,
  },
];

describe('chromedash-admin-gates-page', () => {
  let getGateDefsStub: SinonStub;
  let updateGateDefStub: SinonStub;

  beforeEach(async () => {
    await fixture(html`<chromedash-toast></chromedash-toast>`);
    window.csOpenApiClient = new DefaultApi();
    getGateDefsStub = sinon
      .stub(window.csOpenApiClient, 'getGateDefs')
      .resolves({gates: MOCK_GATES});
    updateGateDefStub = sinon.stub(window.csOpenApiClient, 'updateGateDef');
  });

  afterEach(() => {
    getGateDefsStub.restore();
    updateGateDefStub.restore();
  });

  it('loads gates, displays read-only details, and disables Save initially', async () => {
    const el = await fixture<ChromedashAdminGatesPage>(
      html`<chromedash-admin-gates-page
        .user=${{is_admin: true, email: 'admin@example.com'}}
      ></chromedash-admin-gates-page>`
    );
    await el.updateComplete;

    assert.isTrue(getGateDefsStub.calledOnce);
    assert.equal(el.selectedGateType, 4);

    const textarea =
      el.shadowRoot!.querySelector<SlTextarea>('#approvers-input');
    assert.exists(textarea);
    assert.isTrue(textarea!.hasAttribute('readonly'));
    assert.equal(textarea!.value, 'owner@chromium.org');

    const saveBtn = el.shadowRoot!.querySelector<SlButton>('#save-button');
    assert.exists(saveBtn);
    assert.isTrue(saveBtn!.hasAttribute('disabled'));
  });

  it('enables Save after editing an editable gate and sends PATCH on click', async () => {
    const updatedGate: GateDefAdmin = {
      ...MOCK_GATES[1],
      approvers: ['privacy1@example.com', 'privacy3@example.com'],
    };
    updateGateDefStub.resolves(updatedGate);

    const el = await fixture<ChromedashAdminGatesPage>(
      html`<chromedash-admin-gates-page
        .user=${{is_admin: true, email: 'admin@example.com'}}
      ></chromedash-admin-gates-page>`
    );
    await el.updateComplete;

    // Select editable Privacy gate.
    el.selectGate(34);
    await el.updateComplete;

    const textarea =
      el.shadowRoot!.querySelector<SlTextarea>('#approvers-input')!;
    const saveBtn = el.shadowRoot!.querySelector<SlButton>('#save-button')!;
    assert.isFalse(textarea.hasAttribute('readonly'));
    assert.isTrue(saveBtn.hasAttribute('disabled'));

    // Edit approvers list.
    textarea.value = 'privacy1@example.com\nprivacy3@example.com';
    textarea.dispatchEvent(new CustomEvent('sl-input'));
    await el.updateComplete;

    assert.isFalse(saveBtn.hasAttribute('disabled'));

    // Save changes.
    saveBtn.click();
    await el.updateComplete;

    assert.isTrue(updateGateDefStub.calledOnce);
    assert.deepEqual(updateGateDefStub.firstCall.args[0], {
      id: 34,
      updateGateDefRequest: {
        approvers: ['privacy1@example.com', 'privacy3@example.com'],
      },
    });
    assert.isTrue(saveBtn.hasAttribute('disabled'));
  });

  it('shows access denied message for non-admin users', async () => {
    const el = await fixture<ChromedashAdminGatesPage>(
      html`<chromedash-admin-gates-page
        .user=${{is_admin: false, email: 'user@example.com'}}
      ></chromedash-admin-gates-page>`
    );
    await el.updateComplete;

    assert.isFalse(getGateDefsStub.called);
    assert.include(
      el.shadowRoot!.textContent || '',
      'You must be a site admin'
    );
  });
});
