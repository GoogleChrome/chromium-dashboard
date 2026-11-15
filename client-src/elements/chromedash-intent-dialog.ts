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

import {LitElement, css, html, nothing} from 'lit';
import {customElement, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  clearURLParams,
  getFieldValueFromFeature,
  isDefinedValue,
  renderValue,
  updateURLParams,
} from './utils.js';
import * as enums from './form-field-enums.js';
import {makeDisplaySpecs} from './form-field-specs.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {type GateDict} from './chromedash-gate-chip.js';

let intentDialogEl;

// The different types of intents used to dictate fields in the intent templates.
enum IntentDraftTypeEnum {
  PROTOTYPE = 'prototype',
  DEVELOPER_TESTING = 'developer_testing',
  EXPERIMENT = 'experiment',
  EXTEND_EXPERIMENT = 'extend_experiment',
  SHIP = 'ship',
  PSA = 'psa',
  DEPRECATE = 'deprecate',
}

const INTENT_DRAFT_TYPES_BY_STAGE_TYPE = {
  [enums.STAGE_BLINK_PROTOTYPE]: IntentDraftTypeEnum.PROTOTYPE,
  [enums.STAGE_BLINK_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_BLINK_ORIGIN_TRIAL]: IntentDraftTypeEnum.EXPERIMENT,
  [enums.STAGE_BLINK_EXTEND_ORIGIN_TRIAL]:
    IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  [enums.STAGE_BLINK_SHIPPING]: IntentDraftTypeEnum.SHIP,
  [enums.STAGE_FAST_PROTOTYPE]: IntentDraftTypeEnum.PROTOTYPE,
  [enums.STAGE_FAST_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_FAST_ORIGIN_TRIAL]: IntentDraftTypeEnum.EXPERIMENT,
  [enums.STAGE_FAST_EXTEND_ORIGIN_TRIAL]: IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  [enums.STAGE_FAST_SHIPPING]: IntentDraftTypeEnum.SHIP,
  [enums.STAGE_PSA_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_PSA_SHIPPING]: IntentDraftTypeEnum.PSA,
  [enums.STAGE_DEP_PLAN]: IntentDraftTypeEnum.DEPRECATE,
  [enums.STAGE_DEP_DEV_TRIAL]: IntentDraftTypeEnum.DEVELOPER_TESTING,
  [enums.STAGE_DEP_DEPRECATION_TRIAL]: IntentDraftTypeEnum.EXPERIMENT,
  [enums.STAGE_DEP_EXTEND_DEPRECATION_TRIAL]:
    IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  [enums.STAGE_DEP_SHIPPING]: IntentDraftTypeEnum.SHIP,
};

const SUBJECT_PREFIXES = {
  [IntentDraftTypeEnum.PROTOTYPE]: 'Intent to Prototype',
  [IntentDraftTypeEnum.DEVELOPER_TESTING]: 'Ready for Developer Testing',
  [IntentDraftTypeEnum.EXPERIMENT]: 'Intent to Experiment',
  [IntentDraftTypeEnum.EXTEND_EXPERIMENT]: 'Intent to Extend Experiment',
  [IntentDraftTypeEnum.PSA]: 'Web-Facing Change PSA',
  [IntentDraftTypeEnum.DEPRECATE]: 'Intent to Deprecate and Remove',
  [IntentDraftTypeEnum.SHIP]: 'Intent to Ship',
};

const GATE_TYPES_WITH_INTENTS = [
  enums.GATE_TYPES.API_PROTOTYPE,
  enums.GATE_TYPES.API_ORIGIN_TRIAL,
  enums.GATE_TYPES.API_EXTEND_ORIGIN_TRIAL,
  enums.GATE_TYPES.API_SHIP,
  enums.GATE_TYPES.API_PLAN,
];

const NORTHWEST_FIELDS = [
  'name',
  'owner',
  'explainer_links',
  'spec_link',
  'blink_components',
  'web_feature',
  'intent_thread_url',
];

const NORTHEAST_FIELDS = [
  'dt_milestone_desktop_start',
  'dt_milestone_android_start?',
  'dt_milestone_ios_start?',

  'ot_milestone_desktop_start',
  'ot_milestone_desktop_end',
  'ot_milestone_android_start?',
  'ot_milestone_android_end?',
  'ot_milestone_webview_start?',
  'ot_milestone_webview_end?',

  'shipped_milestone',
  'shipped_android_milestone?',
  'shipped_ios_milestone?',
  'shipped_webview_milestone?',
  'rollout_milestone?',

  'bug_url',
  'launch_bug_url?',
  'initial_public_proposal_url?',
];

const difference = <T>(a: Set<T>, b: Set<T>): Set<T> =>
  new Set([...a].filter(x => !b.has(x)));

const ALL_INTENTS = new Set<IntentDraftTypeEnum>(
  Object.values(IntentDraftTypeEnum)
);
const ALL_EXCEPT_PROTOTYPE = difference(
  ALL_INTENTS,
  new Set([IntentDraftTypeEnum.PROTOTYPE])
);
const ALL_EXCEPT_OT = difference(
  ALL_INTENTS,
  new Set([
    IntentDraftTypeEnum.EXPERIMENT,
    IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  ])
);
const OT_AND_SHIPPING = new Set([
  IntentDraftTypeEnum.EXPERIMENT,
  IntentDraftTypeEnum.EXTEND_EXPERIMENT,
  IntentDraftTypeEnum.SHIP,
  IntentDraftTypeEnum.DEPRECATE,
]);
const ALL_SHIPPING = new Set([
  IntentDraftTypeEnum.SHIP,
  IntentDraftTypeEnum.DEPRECATE,
]);

const CENTRAL_FIELDS = [
  'summary',
  {
    group: 'Details',
    intents: ALL_EXCEPT_OT,
    fields: ['motivation?', 'dev_trial_instructions?'],
  },

  {
    group: 'Spec and TAG',
    intents: OT_AND_SHIPPING,
    fields: ['tag_review', 'tag_review_status', 'anticipated_spec_changes?'],
  },

  {
    group: 'Experiment details',
    intents: new Set([
      IntentDraftTypeEnum.EXPERIMENT,
      IntentDraftTypeEnum.EXTEND_EXPERIMENT,
    ]),
    fields: [
      // Need more: name, reason
      'experiment_goals',
      'experiment_risks',
      'ongoing_constraints',
    ],
  },

  {
    group: 'Risks',
    intents: ALL_EXCEPT_PROTOTYPE,
    fields: [
      'interop_compat_risks',
      'ergonomics_risks',
      'activation_risks',
      'security_risks',
      'webview_risks',
    ],
  },

  {
    group: 'Signals',
    intents: ALL_EXCEPT_PROTOTYPE,
    fields: [
      'safari_views',
      'safari_views_link?',
      'safari_views_notes?',
      'ff_views',
      'ff_views_link?',
      'ff_views_notes?',
      'web_dev_views',
      'web_dev_views_link?',
      'web_dev_views_notes?',
      'other_views_notes',
    ],
  },

  {
    group: 'Implementation',
    intents: ALL_EXCEPT_PROTOTYPE,
    fields: [
      'debuggability?',
      'all_platforms',
      'all_platforms_descr?',
      'wpt',
      'wpt_descr?',
      'flag_name',
      'finch_name',
      'non_finch_justification?',
      'requires_embedder_support',
    ],
  },

  {
    group: 'Deployment and adoption',
    intents: ALL_SHIPPING,
    fields: ['rollout_plan', 'measurement', 'adoption_plan?', 'non_oss_deps?'],
  },
];

interface FieldGroup {
  group: string;
  intents: Set<IntentDraftTypeEnum>;
  fields: string[];
}

function makeIntentDisplaySpecs(fieldNames: string[]) {
  const cleanNames = fieldNames.map(name =>
    name.endsWith('?') ? name.slice(0, -1) : name
  );
  const specs = makeDisplaySpecs(cleanNames);
  return specs.map((spec, i) => {
    if (fieldNames[i].endsWith('?')) {
      const copy = [...spec];
      copy[3] = true;
      return copy;
    }
    return spec;
  });
}

export function stageTypeToIntentSubject(stage_type: number): string {
  const intentDraftType = INTENT_DRAFT_TYPES_BY_STAGE_TYPE[stage_type];
  return SUBJECT_PREFIXES[intentDraftType] || 'Unknown intent';
}

export function shouldOfferIntentDialog(gate: {
  gate_type: number;
  state: number;
}): boolean {
  return (
    gate.state !== enums.GATE_PREPARING &&
    GATE_TYPES_WITH_INTENTS.includes(gate.gate_type)
  );
}

export async function openIntentDialog(
  feature: Feature,
  stage: StageDict,
  gate: GateDict
) {
  if (!intentDialogEl || !intentDialogEl.isConnected) {
    intentDialogEl = document.createElement('chromedash-intent-dialog');
    document.body.appendChild(intentDialogEl);
    await intentDialogEl.updateComplete;
  }
  intentDialogEl.openWithContext(feature, stage, gate);
}

@customElement('chromedash-intent-dialog')
export class ChromedashIntentDialog extends LitElement {
  @state()
  feature!: Feature;
  @state()
  stage!: StageDict;
  @state()
  gate!: GateDict;

  private resizeObserver?: ResizeObserver;
  private lastNarrowClientWidth = 0;
  private lastNarrowWindowWidth = 0;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #content-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--content-padding);
        }

        #northwest {
          grid-row: 1;
          grid-column: 1;
        }

        #northeast {
          grid-row: 1;
          grid-column: 2;
        }

        #central {
          grid-row: 2;
          grid-column: 1 / -1;
        }

        #content-grid.narrow {
          grid-template-columns: 1fr;
        }

        #content-grid.narrow #northwest,
        #content-grid.narrow #northeast,
        #content-grid.narrow #central {
          grid-row: auto;
          grid-column: 1;
        }

        @media only screen and (max-width: 700px) {
          #content-grid {
            grid-template-columns: 1fr;
          }

          #northwest,
          #northeast,
          #central {
            grid-row: auto;
            grid-column: 1;
          }
        }

        .card {
          background: var(--card-background);
          max-width: var(--max-content-width);
          padding: 16px;
        }

        sl-details::part(content) {
          padding-top: var(--content-padding-half);
        }

        dl {
          padding: 0 var(--content-padding-half);
        }

        dt {
          font-weight: 500;
        }

        dd {
          padding: var(--content-padding-half);
          padding-left: var(--content-padding);
          padding-bottom: var(--content-padding-large);
        }

        .inline-list {
          display: inline-block;
          list-style: none;
          padding: 0;
        }

        .url-link {
          display: block;
          max-width: 20em;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .longtext {
          display: block;
          white-space: pre-wrap;
        }

        .longurl {
          display: block;
          padding: var(--content-padding-half);
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    this.resizeObserver = new ResizeObserver(() => {
      this.checkGridOverflow();
    });
    window.addEventListener('resize', this.handleWindowResize);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.resizeObserver?.disconnect();
    window.removeEventListener('resize', this.handleWindowResize);
  }

  protected updated() {
    const gridEl = this.renderRoot.querySelector<HTMLElement>('#content-grid');
    if (gridEl && this.resizeObserver) {
      this.resizeObserver.observe(gridEl);
    }
    this.lastNarrowClientWidth = 0;
    this.lastNarrowWindowWidth = 0;
    this.checkGridOverflow();
  }

  private handleWindowResize = () => {
    this.checkGridOverflow();
  };

  checkGridOverflow() {
    const gridEl = this.renderRoot.querySelector<HTMLElement>('#content-grid');
    if (!gridEl || gridEl.clientWidth === 0) {
      return;
    }

    if (gridEl.classList.contains('narrow')) {
      if (
        window.innerWidth <= this.lastNarrowWindowWidth &&
        gridEl.clientWidth <= this.lastNarrowClientWidth
      ) {
        return;
      }
      gridEl.classList.remove('narrow');
    }

    if (gridEl.scrollWidth > gridEl.clientWidth) {
      gridEl.classList.add('narrow');
      this.lastNarrowClientWidth = gridEl.clientWidth;
      this.lastNarrowWindowWidth = window.innerWidth;
    } else {
      this.lastNarrowClientWidth = 0;
      this.lastNarrowWindowWidth = 0;
    }
  }

  openWithContext(feature: Feature, stage: StageDict, gate: GateDict) {
    this.feature = feature;
    this.stage = stage;
    this.gate = gate;
    updateURLParams('dialog', 'intent');
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    clearURLParams('dialog');
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleHide(e: Event) {
    if (e.target !== e.currentTarget) {
      return;
    }
    clearURLParams('dialog');
  }

  renderField(fieldDef: any[], feStage: StageDict) {
    const [fieldId, fieldDisplayName, , deprecated] = fieldDef;
    const value = getFieldValueFromFeature(fieldId, feStage, this.feature);
    const isDefined = isDefinedValue(value);
    if (!isDefined && deprecated) {
      return nothing;
    }

    return html`
      <dt id=${fieldId}>${fieldDisplayName}</dt>
      <dd>${renderValue(feStage, this.feature, fieldId)}</dd>
    `;
  }

  renderFieldGroup(groupDef: FieldGroup, feStage: StageDict) {
    const intentDraftType =
      INTENT_DRAFT_TYPES_BY_STAGE_TYPE[feStage?.stage_type];
    if (!intentDraftType || !groupDef.intents.has(intentDraftType)) {
      return nothing;
    }
    const content = this.renderSectionFields(groupDef.fields, feStage);
    if (content === nothing) {
      return nothing;
    }
    return html`
      <sl-details summary=${groupDef.group} open>${content}</sl-details>
    `;
  }

  renderSectionFields(fieldItems: (string | FieldGroup)[], feStage: StageDict) {
    if (fieldItems.every(item => typeof item === 'string')) {
      const fields = makeIntentDisplaySpecs(fieldItems as string[]);
      const renderedFields = fields
        .map(fieldDef => this.renderField(fieldDef, feStage))
        .filter(rendered => rendered !== nothing);
      if (renderedFields.length === 0) {
        return nothing;
      }
      return html`<dl>${renderedFields}</dl>`;
    }

    return html`
      ${fieldItems.map(item => {
        if (typeof item === 'string') {
          const [fieldDef] = makeIntentDisplaySpecs([item]);
          const rendered = this.renderField(fieldDef, feStage);
          return rendered === nothing ? nothing : html`<dl>${rendered}</dl>`;
        }
        return this.renderFieldGroup(item, feStage);
      })}
    `;
  }

  renderTableValue(fieldDef: any[], feStage: StageDict) {
    const [fieldId, , fieldType] = fieldDef;
    const value = getFieldValueFromFeature(fieldId, feStage, this.feature);
    if (!isDefinedValue(value)) {
      return html`<i>None</i>`;
    }
    if (fieldType === 'url' || fieldId.endsWith('_url')) {
      return html`<a
        class="url-link"
        href=${value}
        target="_blank"
        rel="noopener"
        >${value}</a
      >`;
    }
    if (fieldType === 'multi-url') {
      return html`
        <ul class="inline-list">
          ${value.map(
            url => html`
              <li>
                <a class="url-link" href=${url} target="_blank" rel="noopener"
                  >${url}</a
                >
              </li>
            `
          )}
        </ul>
      `;
    }
    return renderValue(feStage, this.feature, fieldId);
  }

  renderTableRow(fieldDef: any[], feStage: StageDict) {
    const [fieldId, fieldDisplayName, , deprecated] = fieldDef;
    const value = getFieldValueFromFeature(fieldId, feStage, this.feature);
    const isDefined = isDefinedValue(value);
    if (!isDefined && deprecated) {
      return nothing;
    }

    return html`
      <tr id=${fieldId}>
        <td>${fieldDisplayName}</td>
        <td>${this.renderTableValue(fieldDef, feStage)}</td>
      </tr>
    `;
  }

  renderSectionTable(fieldNames: string[], feStage: StageDict) {
    const fields = makeIntentDisplaySpecs(fieldNames);
    return html`
      <table class="data-table">
        ${fields.map(fieldDef => this.renderTableRow(fieldDef, feStage))}
      </table>
    `;
  }

  renderDialogContent() {
    if (!this.feature) {
      return nothing;
    }
    return html`
      <div id="content-grid">
        <section id="northwest" class="card">
          ${this.renderSectionTable(NORTHWEST_FIELDS, this.stage)}
        </section>
        <section id="northeast" class="card">
          ${this.renderSectionTable(NORTHEAST_FIELDS, this.stage)}
        </section>
        <section id="central" class="card">
          ${this.renderSectionFields(CENTRAL_FIELDS, this.stage)}
        </section>
      </div>
    `;
  }

  render() {
    const subject = stageTypeToIntentSubject(this.stage?.stage_type);
    return html`
      <sl-dialog
        label="${subject}"
        style="--width:fit-content"
        @sl-hide=${this.handleHide}
      >
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}
