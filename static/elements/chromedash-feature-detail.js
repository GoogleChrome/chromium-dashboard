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
      }
    `];
  }

  renderField(fieldDef) {
    const fieldId = fieldDef[0];
    const fieldDisplayName = fieldDef[1];
    // const fieldType = fieldDef[2];
    const value = this.feature[fieldId];
    if (value) {
      return html`
     <div style="padding: 16px;">
       <label id=${fieldId}>${fieldDisplayName}</label>
       <span>${value}</span>
     <div>
    `;
    } else {
      return nothing;
    }
  }

  renderStage(stage) {
    let fields = this.fieldDefs[stage.outgoing_stage];
    return html`
     <section class="card">
      <h3>${stage.name}</h3>
      ${fields.map(fieldDef => this.renderField(fieldDef))}
     </section>
    `;
  }

  render() {
    // let featureId = this.feature.id;
    return html`
       ${this.process.stages.map(stage => html`
            ${this.renderStage(stage)}
       `)}
    `;
  }
}

customElements.define('chromedash-feature-detail', ChromedashFeatureDetail);
