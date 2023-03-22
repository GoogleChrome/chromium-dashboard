import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {
  FEATURE_CATEGORIES,
  FEATURE_TYPES,
  IMPLEMENTATION_STATUS,
  INTENT_STAGES,
  // PLATFORM_CATEGORIES,
  STANDARD_MATURITY_CHOICES,
  REVIEW_STATUS_CHOICES,
  VENDOR_VIEWS_COMMON,
  VENDOR_VIEWS_GECKO,
  WEB_DEV_VIEWS,
  ROLLOUT_IMPACT,
} from './form-field-enums';

const ENTER_KEY_CODE = 13;

const EQ_OP = 'Equals';
const BETWEEN_OP = 'Between';
const CONTAINS_OP = 'Contains words';

const TEXT_TYPE = 'text';
const NUM_TYPE = 'number';
const DATE_TYPE = 'date';
const EMAIL_TYPE = 'email';
const ENUM_TYPE = 'enum';
// const BOOL_TYPE = 'bool';

// This works around a lint warning for <input type="${inputType}">.
const FIELD_TYPE_TO_INPUT_TYPE = {
  text: 'text', number: 'number', date: 'date', email: 'email', enum: 'enum',
};


const AVAILABLE_OPS = {};
// TODO: CONTAINS_OP is not yet supported in TEXT_TYPE.
AVAILABLE_OPS[TEXT_TYPE] = [EQ_OP];
AVAILABLE_OPS[NUM_TYPE] = [BETWEEN_OP, EQ_OP];
AVAILABLE_OPS[DATE_TYPE] = [BETWEEN_OP];
// TODO: CONTAINS_OP is yet supported in EMAIL_TYPE.
AVAILABLE_OPS[EMAIL_TYPE] = [EQ_OP];
AVAILABLE_OPS[ENUM_TYPE] = [EQ_OP];
// AVAILABLE_OPS[BOOL_TYPE] = [EQ_OP];


const QUERIABLE_FIELDS = [
  {name: 'created.when', display: 'Created', type: DATE_TYPE},
  {name: 'updated.when', display: 'Updated', type: DATE_TYPE},

  // TODO(jrobbins): The backend cannot handle User-type fields.
  // These need to be migrated to string fields with emails.
  // {name: 'created.by', display: 'Created by', type: EMAIL_TYPE},
  // {name: 'updated.by', display: 'Updated by', type: EMAIL_TYPE},

  // {name: 'category', display: 'Category', type: ENUM_TYPE,
  //  values: ['one', 'two', 'three']},

  {name: 'name', display: 'Name', type: TEXT_TYPE},
  //  'feature_type': Feature.feature_type,
  //  'intent_stage': Feature.intent_stage,
  {name: 'summary', display: 'Summary', type: TEXT_TYPE},
  // 'unlisted': Feature.unlisted,
  //  'motivation': Feature.motivation,
  //  'star_count': Feature.star_count,
  {name: 'tags', display: 'Tags', type: TEXT_TYPE},
  {name: 'owner', display: 'Owner', type: EMAIL_TYPE},
  //  'intent_to_implement_url': Feature.intent_to_implement_url,
  //  'intent_to_ship_url': Feature.intent_to_ship_url,
  //  'ready_for_trial_url': Feature.ready_for_trial_url,
  //  'intent_to_experiment_url': Feature.intent_to_experiment_url,
  //  'intent_to_extend_experiment_url': Feature.intent_to_extend_experiment_url,
  //  'i2e_lgtms': Feature.i2e_lgtms,
  //  'i2s_lgtms': Feature.i2s_lgtms,
  //  'browsers.chrome.bug': Feature.bug_url,
  //  'launch_bug_url': Feature.launch_bug_url,
  //  'initial_public_proposal_url': Feature.initial_public_proposal_url,
  //  'browsers.chrome.blink_components': Feature.blink_components,
  {name: 'browsers.chrome.devrel', display: 'DevRel contact', type: EMAIL_TYPE},
  // {name: 'browsers.chrome.prefixed', display: 'Prefixed', type: BOOL_TYPE},

  //  'browsers.chrome.status': Feature.impl_status_chrome,
  {name: 'browsers.chrome.desktop',
    display: 'Desktop Shipping Milestone',
    type: NUM_TYPE},
  {name: 'browsers.chrome.android',
    display: 'Android Shipping Milestone',
    type: NUM_TYPE},
  {name: 'browsers.chrome.ios',
    display: 'iOS Shipping Milestone',
    type: NUM_TYPE},
  {name: 'browsers.chrome.webview',
    display: 'Webview Shipping Milestone',
    type: NUM_TYPE},
  // 'requires_embedder_support': Feature.requires_embedder_support,

  {name: 'browsers.chrome.flag_name', display: 'Flag name', type: TEXT_TYPE},
  // 'all_platforms': Feature.all_platforms,
  // 'all_platforms_descr': Feature.all_platforms_descr,
  // 'wpt': Feature.wpt,
  {name: 'browsers.chrome.devtrial.desktop.start',
    display: 'Desktop Dev Trial Start',
    type: NUM_TYPE},
  {name: 'browsers.chrome.devtrial.android.start',
    display: 'Android Dev Trial Start',
    type: NUM_TYPE},
  {name: 'browsers.chrome.devtrial.ios.start',
    display: 'iOS Dev Trial Start',
    type: NUM_TYPE},
  {name: 'browsers.chrome.devtrial.webview.start',
    display: 'WebView Dev Trial Start',
    type: NUM_TYPE},

  // 'standards.maturity': Feature.standard_maturity,
  // 'standards.spec': Feature.spec_link,
  // 'api_spec': Feature.api_spec,
  // 'spec_mentors': Feature.spec_mentors,
  // 'security_review_status': Feature.security_review_status,
  // 'privacy_review_status': Feature.privacy_review_status,
  // 'tag_review.url': Feature.tag_review,
  // 'explainer': Feature.explainer_links,

  // 'resources.docs': Feature.doc_links,
  // 'non_oss_deps': Feature.non_oss_deps,

  // 'browsers.chrome.ot.desktop.start': Feature.ot_milestone_desktop_start,
  {name: 'browsers.chrome.ot.desktop.start',
    display: 'Desktop Origin Trial Start',
    type: NUM_TYPE},
  // 'browsers.chrome.ot.desktop.end': Feature.ot_milestone_desktop_end,
  {name: 'browsers.chrome.ot.desktop.end',
    display: 'Desktop Origin Trial End',
    type: NUM_TYPE},
  // 'browsers.chrome.ot.android.start': Feature.ot_milestone_android_start,
  {name: 'browsers.chrome.ot.android.start',
    display: 'Android Origin Trial Start',
    type: NUM_TYPE},
  // 'browsers.chrome.ot.android.end': Feature.ot_milestone_android_end,
  {name: 'browsers.chrome.ot.android.end',
    display: 'Android Origin Trial End',
    type: NUM_TYPE},
  // 'browsers.chrome.ot.webview.start': Feature.ot_milestone_webview_start,
  {name: 'browsers.chrome.ot.webview.start',
    display: 'WebView Origin Trial Start',
    type: NUM_TYPE},
  // 'browsers.chrome.ot.webview.end': Feature.ot_milestone_webview_end,
  {name: 'browsers.chrome.ot.webview.end',
    display: 'WebView Origin Trial End',
    type: NUM_TYPE},
  // 'browsers.chrome.ot.feedback_url': Feature.origin_trial_feedback_url,
  // 'finch_url': Feature.finch_url,

  // TODO(kyleju): Use ALL_FIELDS from form-field-specs.js.
  // Available ENUM fields.
  {name: 'category',
    display: 'Feature category',
    choices: FEATURE_CATEGORIES,
    type: ENUM_TYPE},
  {name: 'feature_type',
    display: 'Feature type',
    choices: FEATURE_TYPES,
    type: ENUM_TYPE},
  {name: 'impl_status_chrome',
    display: 'Implementation status',
    choices: IMPLEMENTATION_STATUS,
    type: ENUM_TYPE},
  {name: 'intent_stage',
    display: 'Spec process stage',
    choices: INTENT_STAGES,
    type: ENUM_TYPE},
  {name: 'rollout_impact',
    display: 'Impact',
    choices: ROLLOUT_IMPACT,
    type: ENUM_TYPE},
  // TODO: rollout_platforms is not yet supported.
  // {name: 'rollout_platforms',
  //  display: 'Rollout platforms',
  //  choices: PLATFORM_CATEGORIES,
  //  type: ENUM_TYPE},
  {name: 'standard_maturity',
    display: 'Standard maturity',
    choices: STANDARD_MATURITY_CHOICES,
    type: ENUM_TYPE},
  {name: 'security_review_status',
    display: 'Security review status',
    choices: REVIEW_STATUS_CHOICES,
    type: ENUM_TYPE},
  {name: 'privacy_review_status',
    display: 'Privacy review status',
    choices: REVIEW_STATUS_CHOICES,
    type: ENUM_TYPE},
  {name: 'tag_review_status',
    display: 'TAG Specification Review Status',
    choices: REVIEW_STATUS_CHOICES,
    type: ENUM_TYPE},
  {name: 'browsers.safari.view',
    display: 'Safari views',
    choices: VENDOR_VIEWS_COMMON,
    type: ENUM_TYPE},
  {name: 'browsers.ff.view',
    display: 'Firefox views',
    choices: VENDOR_VIEWS_GECKO,
    type: ENUM_TYPE},
  {name: 'browsers.webdev.view',
    display: 'Web / Framework developer views',
    choices: WEB_DEV_VIEWS,
    type: ENUM_TYPE},
];


class ChromedashFeatureFilter extends LitElement {
  static get properties() {
    return {
      query: {type: String},
      showFilters: {type: Boolean},
      filterConditions: {type: Array},
    };
  }

  constructor() {
    super();
    this.query = '';
    this.showFilters = false;
    this.filterConditions = [];
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail,
    });
    this.dispatchEvent(event);
  }

  computeQuery() {
    const searchBarEl = this.shadowRoot.querySelector('#searchbar');
    const queryTerms = [searchBarEl.value.trim()];
    for (const cond of this.filterConditions) {
      if (cond.op == EQ_OP && cond.value && cond.value.trim()) {
        queryTerms.push(cond.fieldName + '="' + cond.value + '"');
      }
      if (cond.op == BETWEEN_OP && cond.low) {
        queryTerms.push(cond.fieldName + '>=' + cond.low);
      }
      if (cond.op == BETWEEN_OP && cond.high) {
        queryTerms.push(cond.fieldName + '<=' + cond.high);
      }
      if (cond.op == CONTAINS_OP && cond.value && cond.value.trim()) {
        queryTerms.push(cond.fieldName + ':' + cond.value.trim());
      }
    }
    return queryTerms.join(' ').trim();
  }

  handleSearchKey(event) {
    if (event.keyCode == ENTER_KEY_CODE) {
      const newQuery = this.computeQuery();
      this._fireEvent('search', {query: newQuery});
    }
  }

  handleSearchClick() {
    const newQuery = this.computeQuery();
    this._fireEvent('search', {query: newQuery});
  }

  handleFilterClick() {
    const newQuery = this.computeQuery();
    this._fireEvent('search', {query: newQuery});
  }

  toggleFilters() {
    this.showFilters = !this.showFilters;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      sl-icon-button {
        font-size: 1.6rem;
        margin: 0 !important;
      }
      #searchbar::part(base), #filterwidgets {
       background: #eee;
       border: none;
       border-radius: 8px;
      }
      #filterwidgets {
       padding: 4px;
       margin: 4px 0;
      }
      .filterrow {
        display: flex;
      }
      .filterrow * {
        margin: 6px 3px;
      }
      .field-name-select {
        width: 240px;
      }
      .enum-select {
        flex: 1 1 auto;
      }
      .cond-op-menu {
        width: 150px;
      }
      .filterrow label {
        padding-right: 4px;
        align-self: center;
      }
      .filterrow sl-input {
        flex: 1;
      }
      .cond-delete {
        padding: 0;
      }
      .cond-delete:hover {
        background: #ccc;
      }
      .cond-delete:active {
       background: #222;
       color: white;
      }
    `];
  }

  getSearcbarValue(query) {
    // Only update the searchbar value if filter widgets are not in use.
    // TODO(kyle): eventually we should populate the widget and searchbox.
    if (this.filterConditions.length) {
      const searchBarEl = this.shadowRoot.querySelector('#searchbar');
      return searchBarEl.value;
    }
    return query;
  }

  renderSearchBar() {
    return html`
      <div>
        <sl-input id="searchbar" placeholder="Search"
            value=${this.getSearcbarValue(this.query)}
            @keyup="${this.handleSearchKey}">
          <sl-icon-button library="material" name="search" slot="prefix"
              @click="${this.handleSearchClick}">
          </sl-icon-button>
          <sl-icon-button library="material" name="tune" slot="suffix"
              @click="${this.toggleFilters}">
          </sl-icon-button>
        </sl-input>
      </div>
    `;
  }

  renderFilterFieldMenu(fieldName, index) {
    return html`
      <sl-select class="field-name-select" size="small"
              value=${fieldName}
              @sl-change="${(e) => this.handleChangeField(e.target.value, index)}">
       ${QUERIABLE_FIELDS.map((item) => html`
         <sl-option value="${item.name}">
           ${item.display}
         </sl-option>
        `)}
      </sl-select>
    `;
  }

  findAvailableOps(fieldName) {
    const field = QUERIABLE_FIELDS.find(f => f.name == fieldName);
    return AVAILABLE_OPS[field.type];
  }

  handleChangeOp(op, index) {
    const oldCond = this.filterConditions[index];
    const newCond = {fieldName: oldCond.fieldName, op: op}; // Reset values.
    this.replaceCond(newCond, index);
  }

  renderFilterOpMenu(cond, index) {
    const operatorOptions = this.findAvailableOps(cond.fieldName);
    return html`
      <sl-select class="cond-op-menu" size="small"
              value=${cond.op}
              @sl-change="${(e) => this.handleChangeOp(e.target.value, index)}">
       ${operatorOptions.map(opOption => html`
         <sl-option value="${opOption}">
           ${opOption}
         </sl-option>
        `)}
      </sl-select>
    `;
  }

  handleChangeField(fieldName, index) {
    // Reset field and operator, but keep value, low, and high.
    const oldCond = this.filterConditions[index];
    const newCond = {
      ...oldCond,
      fieldName: fieldName,
      op: this.findAvailableOps(fieldName)[0],
    };
    this.replaceCond(newCond, index);
  }

  handleChangeValue(value, index) {
    const oldCond = this.filterConditions[index];
    const newCond = {...oldCond, value: value};
    this.replaceCond(newCond, index);
  }

  handleChangeLow(low, index) {
    const oldCond = this.filterConditions[index];
    const newCond = {...oldCond, low: low};
    this.replaceCond(newCond, index);
  }

  handleChangeHigh(high, index) {
    const oldCond = this.filterConditions[index];
    const newCond = {...oldCond, high: high};
    this.replaceCond(newCond, index);
  }

  renderFilterValues(cond, index) {
    const field = QUERIABLE_FIELDS.find(f => f.name == cond.fieldName);
    const inputType = FIELD_TYPE_TO_INPUT_TYPE[field && field.type] || 'text';

    if (cond.op == EQ_OP) {
      if (inputType == ENUM_TYPE) {
        return html`
          <sl-select class="enum-select" size="small" placeholder="Select a field value"
                @sl-change="${(e) => this.handleChangeValue(e.target.value, index)}">
            ${Object.values(field.choices).map(
              (val) => html`
                <sl-option value="${val[1]}"> ${val[1]} </sl-option>
              `,
            )}
          </sl-select>
          `;
      } else {
        return html`
          <sl-input type="${inputType}" value="${cond.value || ''}" size="small"
                @sl-change="${(e) => this.handleChangeValue(e.target.value, index)}">
          </sl-input>
          `;
      }
    }

    if (cond.op == BETWEEN_OP) {
      return html`
        <label>Min:</label>
        <sl-input type="${inputType}" value="${cond.low}" size="small"
               @sl-change="${(e) => this.handleChangeLow(e.target.value, index)}">
        </sl-input>
        <label>Max:</label>
        <sl-input type="${inputType}" value="${cond.high}" size="small"
               @sl-change="${(e) => this.handleChangeHigh(e.target.value, index)}">
        </sl-input>
        `;
    }

    if (cond.op == CONTAINS_OP) {
      return html`
        <sl-input value="${cond.value}" size="small"
               @sl-change="${(e) => this.handleChangeValue(e.target.value, index)}">
        </sl-input>
        `;
    }

    return 'Unrecognized operator';
  }

  replaceCond(cond, index) {
    if (cond) {
      this.filterConditions = [
        ...this.filterConditions.slice(0, index),
        cond,
        ...this.filterConditions.slice(index + 1)];
    } else {
      this.filterConditions = [
        ...this.filterConditions.slice(0, index),
        // nothing in the middle
        ...this.filterConditions.slice(index + 1)];
    }
  }

  handleDeleteCond(index) {
    this.replaceCond(null, index);
  }

  renderFilterRow(cond, index) {
    return html`
     <div class="filterrow">
      ${this.renderFilterFieldMenu(cond.fieldName, index)}
      ${this.renderFilterOpMenu(cond, index)}
      ${this.renderFilterValues(cond, index)}
      <sl-icon-button name="x" @click="${() => this.handleDeleteCond(index)}">
      </sl-icon-button>
     </div>
    `;
  }

  renderBlankCondition() {
    return html`
     <div class="filterrow">
      <sl-select id="choose_field" class="field-name-select" size="small"
          placeholder="Select a field name"
              @sl-change="${this.addFilterCondition}">
       ${QUERIABLE_FIELDS.map((item) => html`
         <sl-option value="${item.name}">
           ${item.display}
         </sl-option>
        `)}
      </sl-select>
     </div>
    `;
  }

  addFilterCondition(event) {
    const fieldName = event.target.value;
    if (fieldName === null) return;
    const newCond = {
      fieldName: fieldName,
      op: this.findAvailableOps(fieldName)[0],
    };
    const newFilterConditions = [...this.filterConditions, newCond];
    this.filterConditions = newFilterConditions;
    // Reset the choose_field menu so user can add another.
    this.shadowRoot.querySelector('#choose_field').value = null;
  }


  renderFilterWidgets() {
    return html`
      <div id="filterwidgets">
       ${this.filterConditions.map((cond, index) =>
      this.renderFilterRow(cond, index))}
       ${this.renderBlankCondition()}

       <div class="filterrow">
        <sl-button class="searchbutton" variant="primary" size="small"
          @click="${this.handleFilterClick}">
          Search
        </sl-button>
       </div>
      </div>
    `;
  }

  render() {
    return html`
      ${this.renderSearchBar()}
      ${this.showFilters ? this.renderFilterWidgets() : nothing}
    `;
  }
}


customElements.define('chromedash-feature-filter', ChromedashFeatureFilter);
