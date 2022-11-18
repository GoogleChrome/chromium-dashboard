import {LitElement, css, html, nothing} from 'lit';
import {DISPLAY_FIELDS_IN_STAGES} from './form-field-specs';
import '@polymer/iron-icon';
import './chromedash-activity-log';
import './chromedash-callout';
import {autolink} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

const LONG_TEXT = 60;


class ChromedashFeatureDetail extends LitElement {
  static get properties() {
    return {
      user: {type: Object},
      canEdit: {type: Boolean},
      feature: {type: Object},
      process: {type: Object},
      dismissedCues: {type: Array},
      anyCollapsed: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.canEdit = false;
    this.feature = {};
    this.process = {};
    this.dismissedCues = [];
    this.anyCollapsed = true;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: block;
        position: relative;
        box-sizing: border-box;
        contain: content;
        overflow: hidden;
        background: inherit;
      }

      h2 {
        display: flex;
      }
      h2 span {
        flex: 1;
      }

      sl-details {
        border: var(--card-border);
        box-shadow: var(--card-box-shadow);
        margin: var(--content-padding-half);
        border-radius: 4px;
      }

      sl-details {
        background: var(--card-background);
      }

      sl-details::part(base),
      sl-details::part(header) {
        background: transparent;
      }
      sl-details::part(header) {
        padding-bottom: 8px;
      }

      .description {
        padding: 8px 16px;
      }

      sl-details sl-button::part(base) {
        color: var(--sl-color-primary-600);
        border: 1px solid var(--sl-color-primary-600);
      }

      .card {
        background: var(--card-background);
        max-width: var(--max-content-width);
        margin-top: 1em;
        padding: 16px;
      }

      ol {
        list-style: none;
        padding: 0;
      }

      ol li {
        margin-top: .5em;
      }

      label {
        font-weight: bold;
        min-width: 300px;
        display: inline-block;
        width: 300px;
        vertical-align: top;
      }

      .inline-list {
        display: inline-block;
        padding: 0;
        margin: 0;
      }

      .value-item {
        padding: var(--content-padding-half);
      }
      .value-item:nth-of-type(odd) {
        background: var(--table-alternate-background);
      }

      .longtext {
        display: block;
        white-space: pre-wrap;
        padding: var(--content-padding-half);
      }

      .longurl {
        display: block;
        padding: var(--content-padding-half);
      }

      .active .card {
        border: var(--spot-card-border);
        box-shadow: var(--spot-card-box-shadow);
      }

    `];
  }

  isAnyCollapsed() {
    const sections = this.shadowRoot.querySelectorAll('sl-details');
    const open = this.shadowRoot.querySelectorAll('sl-details[open]');
    return open.length < sections.length;
  }

  updateCollapsed() {
    this.anyCollapsed = this.isAnyCollapsed();
  }

  toggleAll() {
    const shouldOpen = this.anyCollapsed;
    this.shadowRoot.querySelectorAll('sl-details').forEach((el) => {
      el.open = shouldOpen;
    });
  }

  renderControls() {
    const editAllButton = html`
      <sl-button variant="text"
           href="/guide/editall/${this.feature.id}">
         Edit all fields
      </sl-button>
    `;
    const toggleLabel = this.anyCollapsed ? 'Expand all' : 'Collapse all';
    return html`
      ${this.canEdit ? editAllButton : nothing}

      <sl-button variant="text"
        title="Expand or collapse all sections"
        @click=${this.toggleAll}>
        ${toggleLabel}
      </sl-button>
    `;
  }

  isDefinedValue(value) {
    return !(value === undefined || value === null || value.length == 0);
  }

  getFieldValue(fieldId) {
    let value = this.feature[fieldId];
    const fieldIdMapping = {
      spec_link: 'standards.spec',
      standard_maturity: 'standards.maturity.text',
      sample_links: 'resources.samples',
      docs_links: 'resources.docs',
      bug_url: 'browsers.chrome.bug',
      blink_components: 'browsers.chrome.blink_components',
      devrel: 'browsers.chrome.devrel',
      prefixed: 'browsers.chrome.prefixed',
      impl_status_chrome: 'browsers.chrome.status.text',
      shipped_milestone: 'browsers.chrome.desktop',
      shipped_android_milestone: 'browsers.chrome.android',
      shipped_webview_milestone: 'browsers.chrome.webview',
      shipped_ios_milestone: 'browsers.chrome.ios',
      ff_views: 'browsers.ff.view.text',
      ff_views_link: 'browsers.ff.view.url',
      safari_views: 'browsers.safari.view.text',
      safari_views_link: 'browsers.safari.view.url',
      webdev_views: 'browsers.webdev.view.text',
      webdev_views_link: 'browsers.webdev.view.url',
      other_views_notes: 'browsers.other.view.notes',
    };
    if (fieldIdMapping[fieldId]) {
      value = this.feature;
      for (const step of fieldIdMapping[fieldId].split('.')) {
        if (value) {
          value = value[step];
        }
      }
    }
    return value;
  }

  hasFieldValue(fieldId) {
    const value = this.getFieldValue(fieldId);
    return this.isDefinedValue(value);
  }

  renderText(value) {
    value = String(value);
    const markup = autolink(value);
    if (value.length > LONG_TEXT || value.includes('\n')) {
      return html`<span class="longtext">${markup}</span>`;
    }
    return html`<span class="text">${markup}</span>`;
  }

  renderUrl(value) {
    if (value.startsWith('http')) {
      return html`
        <a href=${value} target="_blank"
           class="url ${value.length > LONG_TEXT ? 'longurl' : ''}"
           >${value}</a>
      `;
    }
    return this.renderText(value);
  }

  renderValue(fieldType, value) {
    if (fieldType == 'checkbox') {
      return this.renderText(value ? 'True' : 'False');
    } else if (fieldType == 'url') {
      return this.renderUrl(value);
    } else if (fieldType == 'multi-url') {
      return html`
        <ul class='inline-list'>
          ${value.map(url => html`<li>${this.renderUrl(url)}</li>`)}
        </ul>
      `;
    }
    return this.renderText(value);
  }

  renderField(fieldDef) {
    const [fieldId, fieldDisplayName, fieldType] = fieldDef;
    const value = this.getFieldValue(fieldId);
    if (this.isDefinedValue(value)) {
      return html`
     <div class="value-item">
       <label id=${fieldId}>${fieldDisplayName}</label>
       ${this.renderValue(fieldType, value)}
     </div>
    `;
    } else {
      return nothing;
    }
  }

  renderSectionFields(fields) {
    if (fields.some(fieldDef => this.hasFieldValue(fieldDef[0]))) {
      return fields.map(fieldDef => this.renderField(fieldDef));
    } else {
      return html`<p>No relevant fields have been filled in.</p>`;
    }
  }

  renderSection(summary, content, isActive=false) {
    if (isActive) {
      summary += ' - Active';
    }
    return html`
      <sl-details summary=${summary}
        @sl-after-show=${this.updateCollapsed}
        @sl-after-hide=${this.updateCollapsed}
        ?open=${isActive}
        class=${isActive ? 'active' : ''}
      >
        ${content}
      </sl-details>
    `;
  }

  renderMetadataSection() {
    const fields = DISPLAY_FIELDS_IN_STAGES['Metadata'];
    if (fields === undefined || fields.length == 0) {
      return nothing;
    }
    const content = html`
      <section class="card">
        ${this.renderSectionFields(fields)}
      </section>
    `;
    return this.renderSection('Metadata', content);
  }

  renderStageSection(stage) {
    const fields = DISPLAY_FIELDS_IN_STAGES[stage.outgoing_stage];
    const isActive = (this.feature.intent_stage_int == stage.outgoing_stage);
    if (fields === undefined || fields.length == 0) {
      return nothing;
    }
    const editButton = html`
      <sl-button size="small" style="float:right"
           href="/guide/stage/${this.feature.id}/${stage.outgoing_stage}"
           >Edit fields</sl-button>
    `;
    const content = html`
      <p class="description">
        ${this.canEdit ? editButton : nothing}
        ${stage.description}
      </p>
      <section class="card">
        ${this.renderSectionFields(fields)}
      </section>
    `;
    return this.renderSection(stage.name, content, isActive);
  }

  renderActivitySection() {
    const summary = 'Comments & Activity';
    const content = html`
        <div style="padding-top: var(--content-padding)">
          <chromedash-activity-log
            .user=${this.user}
            .feature=${this.feature}
            .comments=${this.comments}
          ></chromedash-activity-log>
        </div>
    `;
    return this.renderSection(summary, content);
  }

  render() {
    return html`
      <h2>
        <span>Development stages</span>
        ${this.renderControls()}
      </h2>
      ${this.renderMetadataSection()}
      ${this.process.stages.map(stage => this.renderStageSection(stage))}
      ${this.renderActivitySection()}
    `;
  }
}

customElements.define('chromedash-feature-detail', ChromedashFeatureDetail);
