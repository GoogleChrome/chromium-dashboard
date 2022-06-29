import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';

const ENTER_KEY_CODE = 13;

const EQ_OP = 'Equals';
const BETWEEN_OP = 'Between';
const CONTAINS_OP = 'Contains';

const TEXT_TYPE = 'text';
const NUM_TYPE = 'number';
const DATE_TYPE = 'date';
const EMAIL_TYPE = 'email';
// const ENUM_TYPE = 'enum';
// const BOOL_TYPE = 'bool';

// This works around a lint warning for <input type="${inputType}">.
const FIELD_TYPE_TO_INPUT_TYPE = {
  text: 'text', number: 'number', date: 'date', email: 'email',
};


const AVAILABLE_OPS = {};
AVAILABLE_OPS[TEXT_TYPE] = [EQ_OP, CONTAINS_OP];
AVAILABLE_OPS[NUM_TYPE] = [BETWEEN_OP, EQ_OP];
AVAILABLE_OPS[DATE_TYPE] = [BETWEEN_OP];
AVAILABLE_OPS[EMAIL_TYPE] = [EQ_OP, CONTAINS_OP];
// AVAILABLE_OPS[ENUM_TYPE] = [EQ_OP];
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
  // 'tag_review.status': Feature.tag_review_status,
  // 'explainer': Feature.explainer_links,

  // 'browsers.ff.view': Feature.ff_views,
  // 'browsers.safari.view': Feature.safari_views,
  // 'browsers.webdev.view': Feature.web_dev_views,
  // 'browsers.ff.view.url': Feature.ff_views_link,
  // 'browsers.safari.view.url': Feature.safari_views_link,
  // 'browsers.webdev.url.url': Feature.web_dev_views_link,

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
    const searchBoxEl = this.shadowRoot.querySelector('#searchbox');
    const queryTerms = [searchBoxEl.value.trim()];
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
      iron-icon {
        --iron-icon-height: 18px;
        --iron-icon-width: 18px;
      }
      button.searchbutton {
        padding: 2px 8px;
        font-size: inherit;
      }
      .primary iron-icon {
        color: white;
      }
      #searchbar, #filterwidgets {
       padding: 4px;
       margin: 4px;
       background: #eee;
       border-radius: 8px;
       width: var(--max-content-width);
      }
      #searchbar {
       display: flex;
      }
      #searchbar button, #searchbar button iron-icon {
       background: transparent;
       color: #444;
       border: none;
      }
      #searchbar input {
       flex: 1;
       border: none;
       background: transparent;
      }
      .filterrow {
        display: flex;
      }
      .filterrow * {
        margin: 6px 3px;
      }
      .cond-field-menu {
        width: 160px;
      }
      .cond-op-menu {
        width: 80px;
      }
      .filterrow label {
        padding-right: 4px;
        align-self: center;
      }
      .filterrow input {
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

  renderSearchBox() {
    return html`
      <div id="searchbar">
       <button class="searchbutton primary"
               @click="${this.handleSearchClick}">
        <iron-icon icon="chromestatus:search"></iron-icon>
       </button>
       <input id="searchbox" type="search" placeholder="Search" size=60
              @keyup="${this.handleSearchKey}">
       <button id="showfilters" @click="${this.toggleFilters}">
        <iron-icon icon="chromestatus:filter-list-from-gmail"></iron-icon>
       </button>
      </div>
    `;
  }

  handleChangeField(fieldName, index) {
    // Reset values and operator
    const newCond = {
      fieldName: fieldName,
      op: this.findAvailableOps(fieldName)[0],
    };
    this.replaceCond(newCond, index);
  }

  renderFilterFieldMenu(fieldName, index) {
    return html`
      <select class="cond-field-menu"
              @change="${(e) => this.handleChangeField(e.target.value, index)}">
       ${QUERIABLE_FIELDS.map((item) => html`
        <option value="${item.name}"
          ?selected=${fieldName == item.name}
        >${item.display}</option>
         `)}
      </select>
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
      <select class="cond-op-menu"
              @change="${(e) => this.handleChangeOp(e.target.value, index)}">
       ${operatorOptions.map(opOption => html`
          <option
            value="${opOption}"
            ?selected=${cond.op == opOption}
          >${opOption}</option>
        `)}
      </select>
    `;
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
      return html`
        <input type="${inputType}" value="${cond.value || ''}"
               @change="${(e) => this.handleChangeValue(e.target.value, index)}">
        `;
    }

    if (cond.op == BETWEEN_OP) {
      return html`
        <label>Min:</label>
        <input type="${inputType}" value="${cond.low}"
               @change="${(e) => this.handleChangeLow(e.target.value, index)}">
        <label>Max:</label>
        <input type="${inputType}" value="${cond.high}"
               @change="${(e) => this.handleChangeHigh(e.target.value, index)}">
        `;
    }

    if (cond.op == CONTAINS_OP) {
      return html`
        <input value="${cond.value}"
               @change="${(e) => this.handleChangeValue(e.target.value, index)}">
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
      <button class="cond-delete"
              @click="${() => this.handleDeleteCond(index)}"
      ><iron-icon icon="chromestatus:close"></iron-icon></button>
     </div>
    `;
  }

  renderBlankCondition() {
    return html`
     <div class="filterrow">
      <select id="choose_field" class="cond-field-menu"
              @change="${this.addFilterCondition}">
       <option disabled selected value="choose"
         >Select field name</option>
       ${QUERIABLE_FIELDS.map((item) => html`
        <option value="${item.name}">${item.display}</option>
         `)}
      </select>
     </div>
    `;
  }

  addFilterCondition(event) {
    const fieldName = event.target.value;
    const newCond = {
      fieldName: fieldName,
      op: this.findAvailableOps(fieldName)[0],
    };
    const newFilterConditions = [...this.filterConditions, newCond];
    this.filterConditions = newFilterConditions;
    this.shadowRoot.querySelector('#choose_field').value = 'choose';
  }


  renderFilterWidgets() {
    return html`
      <div id="filterwidgets">
       ${this.filterConditions.map((cond, index) =>
      this.renderFilterRow(cond, index))}
       ${this.renderBlankCondition()}

       <div>
        <button class="searchbutton primary" @click="${this.handleFilterClick}">
          Search
        </button>
       </div>
      </div>
    `;
  }

  render() {
    return html`
      ${this.renderSearchBox()}
      ${this.showFilters ? this.renderFilterWidgets() : nothing}
    `;
  }
}


customElements.define('chromedash-feature-filter', ChromedashFeatureFilter);
