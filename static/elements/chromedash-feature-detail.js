import {LitElement, css, html} from 'lit-element';
import {nothing} from 'lit-html';
import '@polymer/iron-icon';
import './chromedash-callout';
import SHARED_STYLES from '../css/shared.css';

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
      SHARED_STYLES,
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
      ff_views: 'browsers.ff.views.text',
      ff_views_link: 'browsers.ff.views.url',
      safari_views: 'browsers.safari.views.text',
      safari_views_link: 'browsers.safari.views.url',
      webdev_views: 'browsers.webdev.views.text',
      webdev_views_link: 'browsers.webdev.views.url',
    };
    if (fieldIdMapping[fieldId]) {
      value = this.feature;
      console.log(fieldIdMapping[fieldId]);
      for (let step of fieldIdMapping[fieldId].split('.')) {
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
    if (value.length > 30 || value.includes('\n')) {
      return html`<span class="longtext">${value}</span>`;
    }
    return html`<span class="text">${value}</span>`;
  }

  renderUrl(value) {
    if (value.startsWith('http')) {
      return html`
        <a href=${value} target="_blank" class="url"
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
