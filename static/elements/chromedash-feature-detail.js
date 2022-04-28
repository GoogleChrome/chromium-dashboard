import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import './chromedash-callout';
import {autolink} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

const LONG_TEXT = 60;


class ChromedashFeatureDetail extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      process: {type: Array},
      fieldDefs: {type: Object},
      dismissedCues: {type: Object},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.process = [];
    this.fieldDefs = [];
    this.dismissedCues = {};
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

      .card {
        background: var(--card-background);
        border: var(--card-border);
        box-shadow: var(--card-box-shadow);
        max-width: var(--max-content-width);
        margin-top: 1em;
        padding: 16px;
      }
      .card h3 {
        margin-top: 4px;
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

      .active {
        border: var(--spot-card-border);
        box-shadow: var(--spot-card-box-shadow);
      }

      .active h3::after {
        content: "Active stage";
        float: right;
        color: var(--dark-spot-color);
      }

    `];
  }

  isDefinedValue(value) {
    return !(value === undefined || value === null || value.length == 0);
  }

  getFieldValue(fieldDef) {
    const fieldId = fieldDef[0];
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

  hasFieldValue(fieldDef) {
    const value = this.getFieldValue(fieldDef);
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
    if (fieldType == 'bool') {
      return this.renderText(value ? 'True' : 'False');
    } else if (fieldType == 'url') {
      return this.renderUrl(value);
    } else if (fieldType == 'urllist') {
      return html`
        <ul class='inline-list'>
          ${value.map(url => html`<li>${this.renderUrl(url)}</li>`)}
        </ul>
      `;
    }
    return this.renderText(value);
  }

  renderField(fieldDef) {
    const fieldId = fieldDef[0];
    const fieldDisplayName = fieldDef[1];
    const fieldType = fieldDef[2];
    const value = this.getFieldValue(fieldDef);
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

  renderStage(stage) {
    let fields = [];
    let stageName = undefined;
    let activeClass = '';
    if (typeof stage == 'string') {
      fields = this.fieldDefs[stage];
      stageName = stage;
    } else {
      fields = this.fieldDefs[stage.outgoing_stage];
      stageName = stage.name;
      if (this.feature.intent_stage_int == stage.outgoing_stage) {
        activeClass = 'active';
      }
    }
    if (fields === undefined || fields.length == 0) {
      return nothing;
    }
    let valuesPart = html`<p>No relevant fields have been filled in.</p>`;
    if (fields.some(fieldDef => this.hasFieldValue(fieldDef))) {
      valuesPart = fields.map(fieldDef => this.renderField(fieldDef));
    }
    return html`
      <section class="card ${activeClass}">
       <h3>${stageName}</h3>
       ${valuesPart}
      </section>
    `;
  }

  render() {
    return html`
       ${this.renderStage('Metadata')}
       ${this.process.stages.map(stage => html`
            ${this.renderStage(stage)}
       `)}
       ${this.renderStage('Misc')}
    `;
  }
}

customElements.define('chromedash-feature-detail', ChromedashFeatureDetail);
