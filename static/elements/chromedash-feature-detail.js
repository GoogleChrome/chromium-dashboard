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
        madgin: 1em 0;
      }

      .card {
        background: var(--card-background);
        border: var(--card-border);
        box-shadow:  var(--card-box-shadow);
        max-width: 760px;
        margin-top: 1em;
        padding: 16px;
      }
      .card h3 {
        margin-top: 4px;
      }

      table {
        border-spacing: 0;
        width: 100%;
      }

      th {
        text-align: left;
        padding: var(--content-padding-half);
        background: var(--table-header-background);
      }

      td {
        padding: var(--content-padding-half) var(--content-padding) var(--content-padding) var(--content-padding-half);
        vertical-align: top;
        border-bottom: var(--table-divider);
        background: var(--table-row-background);
      }

      tr.active td {
        background: var(--light-accent-color);
      }

      td div.done:before {
        content: "\\2713";
        position: absolute;
        left: 0;
      }

      td div.pending:before {
        content: "\\25cb";
        position: absolute;
        left: 0;
      }

      td div.done, td div.pending {
        position: relative;
        padding-left: 1.2em;
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
        padding: var(--content-padding);
      }
      .value-item:nth-of-type(odd) {
        background: var(--table-alternate-background);
      }

      .longtext {
        display: block;
        white-space: pre-wrap;
        padding: var(--content-padding-half);
      }

    `];
  }

  isDefinedValue(value) {
    return !(value === undefined || value === null || value.length == 0);
  }

  getFieldValue(fieldDef) {
    const fieldId = fieldDef[0];
    let value = this.feature[fieldId];
    if (value && value.text) {
      value = value.text;
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
     <div>
    `;
    } else {
      return nothing;
    }
  }

  renderStage(stage) {
    let fields = this.fieldDefs[stage.outgoing_stage];
    if (fields === undefined || fields.length == 0) {
      return nothing;
    }
    let valuesPart = html`<p>No relevant fields have been filled in.</p>`;
    if (fields.some(fieldDef => this.hasFieldValue(fieldDef))) {
      valuesPart = fields.map(fieldDef => this.renderField(fieldDef));
    }
    return html`
      <section class="card">
       <h3>${stage.name}</h3>
       ${valuesPart}
      </section>
    `;
  }

  render() {
    return html`
       ${this.process.stages.map(stage => html`
            ${this.renderStage(stage)}
       `)}
    `;
  }
}

customElements.define('chromedash-feature-detail', ChromedashFeatureDetail);
