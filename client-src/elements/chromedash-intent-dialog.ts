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
import {Feature, FeatureLink, StageDict} from '../js-src/cs-client.js';
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

interface FieldGroup {
  group: string;
  intents: Set<IntentDraftTypeEnum>;
  fields: string[];
}

const CENTRAL_FIELDS: (string | FieldGroup)[] = [
  'summary',
  {
    group: 'Details',
    intents: ALL_EXCEPT_OT,
    fields: ['motivation?', 'devtrial_instructions?'],
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

const OT_STAGE_FIELDS = new Set<string>([
  ...enums.OT_MILESTONE_START_FIELDS,
  'ot_milestone_desktop_end',
  'ot_milestone_android_end',
  'ot_milestone_webview_end',
  'experiment_goals',
  'experiment_risks',
]);

const ROLLOUT_STAGE_TYPES = new Set<number>([enums.STAGE_ENT_ROLLOUT]);

function findStageByTypes(
  stageTypes: Set<number>,
  currentStage: StageDict | undefined,
  feature: Feature | undefined
): StageDict | null {
  if (currentStage && stageTypes.has(currentStage.stage_type)) {
    return currentStage;
  }
  return (
    feature?.stages?.findLast(stage => stageTypes.has(stage.stage_type)) ?? null
  );
}

function getStageForField(
  fieldId: string,
  currentStage: StageDict | undefined,
  feature: Feature | undefined
): StageDict | null {
  if (enums.DT_MILESTONE_FIELDS.has(fieldId)) {
    return findStageByTypes(enums.STAGE_TYPES_DEV_TRIAL, currentStage, feature);
  }
  if (OT_STAGE_FIELDS.has(fieldId)) {
    if (
      currentStage &&
      enums.STAGE_TYPES_ORIGIN_TRIAL.has(currentStage.stage_type)
    ) {
      return currentStage;
    }
    if (
      currentStage &&
      enums.OT_EXTENSION_STAGE_TYPES.has(currentStage.stage_type)
    ) {
      const parentOtStage = feature?.stages?.find(
        stage =>
          stage.id === currentStage.ot_stage_id ||
          stage.extensions?.some(ext => ext.id === currentStage.id)
      );
      if (parentOtStage) {
        return parentOtStage;
      }
    }
    return findStageByTypes(
      enums.STAGE_TYPES_ORIGIN_TRIAL,
      currentStage,
      feature
    );
  }
  if (enums.SHIPPED_MILESTONE_FIELDS.has(fieldId)) {
    return findStageByTypes(enums.STAGE_TYPES_SHIPPING, currentStage, feature);
  }
  if (fieldId === 'rollout_milestone') {
    return findStageByTypes(ROLLOUT_STAGE_TYPES, currentStage, feature);
  }
  return currentStage ?? null;
}

type DisplaySpec = [
  string,
  string,
  string,
  boolean | undefined,
  boolean | undefined,
];

function makeIntentDisplaySpecs(fieldNames: string[]): DisplaySpec[] {
  const cleanNames = fieldNames.map(name =>
    name.endsWith('?') ? name.slice(0, -1) : name
  );
  const specs = makeDisplaySpecs(cleanNames) as DisplaySpec[];
  return specs.map((spec, i) => {
    if (fieldNames[i].endsWith('?')) {
      const copy: DisplaySpec = [...spec];
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
  gate: GateDict,
  featureLinks: FeatureLink[] = []
) {
  if (!intentDialogEl || !intentDialogEl.isConnected) {
    intentDialogEl = document.createElement('chromedash-intent-dialog');
    document.body.appendChild(intentDialogEl);
    await intentDialogEl.updateComplete;
  }
  intentDialogEl.openWithContext(feature, stage, gate, featureLinks);
}

@customElement('chromedash-intent-dialog')
export class ChromedashIntentDialog extends LitElement {
  @state()
  feature!: Feature;
  @state()
  stage!: StageDict;
  @state()
  gate!: GateDict;
  @state()
  featureLinks: FeatureLink[] = [];

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-dialog::part(base) {
          right: calc(
            var(--sidebar-space, 410px) +
              max(
                0px,
                (
                    100vw - var(--content-margin-left, 210px) - var(
                        --max-content-width,
                        860px
                      ) - var(--sidebar-space, 410px)
                  ) /
                  2
              )
          );
        }

        sl-dialog::part(panel) {
          max-width: min(
            calc(300px + var(--max-content-width, 860px)),
            calc(100% - var(--content-padding))
          );
          max-height: calc(100vh - 2 * var(--content-padding));
        }

        #content-grid {
          display: flex;
          flex-wrap: wrap;
          gap: var(--content-padding);
        }

        #northwest,
        #northeast {
          flex: 1 1 min-content;
          max-width: 100%;
        }

        #central {
          flex: 1 1 100%;
          max-width: 100%;
        }

        @media only screen and (max-width: 860px) {
          sl-dialog::part(base) {
            right: 0;
          }

          sl-dialog::part(panel) {
            max-width: calc(100vw - 2 * var(--content-padding));
          }
        }

        .card {
          background: var(--card-background);
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

  openWithContext(
    feature: Feature,
    stage: StageDict,
    gate: GateDict,
    featureLinks: FeatureLink[] = []
  ) {
    this.feature = feature;
    this.stage = stage;
    this.gate = gate;
    this.featureLinks = featureLinks;
    updateURLParams('dialog', 'intent');
    void this.renderRoot.querySelector('sl-dialog')?.show();

    if (featureLinks.length === 0 && feature?.id && window.csClient) {
      const featureId = feature.id;
      window.csClient
        .getFeatureLinks(featureId)
        .then(res => {
          if (this.feature?.id === featureId && res?.data) {
            this.featureLinks = res.data;
          }
        })
        .catch(() => {
          // Links still render as plain anchors if enrichment fails.
        });
    }
  }

  hide() {
    clearURLParams('dialog');
    void this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  handleHide(e: Event) {
    if (e.target !== e.currentTarget) {
      return;
    }
    clearURLParams('dialog');
  }

  renderField(fieldDef: DisplaySpec) {
    const [fieldId, fieldDisplayName, , deprecated] = fieldDef;
    const fieldStage = getStageForField(fieldId, this.stage, this.feature);
    const value = getFieldValueFromFeature(fieldId, fieldStage, this.feature);
    const isDefined = isDefinedValue(value);
    if (!isDefined && deprecated) {
      return nothing;
    }

    return html`
      <dt id=${fieldId}>${fieldDisplayName}</dt>
      <dd>
        ${renderValue(fieldStage, this.feature, fieldId, this.featureLinks)}
      </dd>
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
        .map(fieldDef => this.renderField(fieldDef))
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
          const rendered = this.renderField(fieldDef);
          return rendered === nothing ? nothing : html`<dl>${rendered}</dl>`;
        }
        return this.renderFieldGroup(item, feStage);
      })}
    `;
  }

  renderTableRow(fieldDef: DisplaySpec) {
    const [fieldId, fieldDisplayName, , deprecated] = fieldDef;
    const fieldStage = getStageForField(fieldId, this.stage, this.feature);
    const value = getFieldValueFromFeature(fieldId, fieldStage, this.feature);
    const isDefined = isDefinedValue(value);
    if (!isDefined && deprecated) {
      return nothing;
    }

    return html`
      <tr id=${fieldId}>
        <td>${fieldDisplayName}</td>
        <td>
          ${renderValue(fieldStage, this.feature, fieldId, this.featureLinks)}
        </td>
      </tr>
    `;
  }

  renderSectionTable(fieldNames: string[]) {
    const fields = makeIntentDisplaySpecs(fieldNames);
    return html`
      <table class="data-table">
        ${fields.map(fieldDef => this.renderTableRow(fieldDef))}
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
          ${this.renderSectionTable(NORTHWEST_FIELDS)}
        </section>
        <section id="northeast" class="card">
          ${this.renderSectionTable(NORTHEAST_FIELDS)}
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
