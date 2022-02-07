import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import './chromedash-callout';
import SHARED_STYLES from '../css/shared.css';

class ChromedashProcessOverview extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      process: {type: Array},
      progress: {type: Object},
      dismissedCues: {type: Object},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.process = [];
    this.progress = {};
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
    `];
  }

  inFinalStage(stage) {
    const FINAL_STAGES = ['Shipped', 'Removed', 'Parked'];
    return (FINAL_STAGES.includes(this.feature.intent_stage) &&
            !FINAL_STAGES.includes(stage)); ;
  }

  /* A stage is "prior" if it would set a intent_stage that this feature
     has already passed. */
  isPriorStage(stage) {
    // if (this.inFinalStage(stage)) {
    //   return true;
    // }
    const stageOrder = this.process.stages.map(s => s.outgoing_stage);
    const viewedOutgoingStageIndex = stageOrder.indexOf(stage.outgoing_stage);
    const featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedOutgoingStageIndex < featureStageIndex);
  }

  /* A stage is "startable" if its incoming stage is the stage that the
     feature is on or has already passed, but its outgoing stage has
     not alrady been passed. */
  isStartableStage(stage) {
    if (this.inFinalStage(stage)) {
      return false;
    }
    const stageOrder = this.process.stages.map(s => s.outgoing_stage);
    const viewedIncomingStageIndex = stageOrder.indexOf(stage.incoming_stage);
    const viewedOutgoingStageIndex = stageOrder.indexOf(stage.outgoing_stage);
    const featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedIncomingStageIndex <= featureStageIndex &&
            viewedOutgoingStageIndex > featureStageIndex);
  }

  /* A stage is "future" if the feature has not yet reached its incoming stage. */
  isFutureStage(stage) {
    if (this.inFinalStage(stage)) {
      return false;
    }
    const stageOrder = this.process.stages.map(s => s.outgoing_stage);
    const viewedIncomingStageIndex = stageOrder.indexOf(stage.incoming_stage);
    const featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedIncomingStageIndex > featureStageIndex);
  }

  renderAction(action, stage) {
    const label = action[0];
    const url = (action[1].replace('{feature_id}', this.feature.id)
      .replace('{outgoing_stage}', stage.outgoing_stage));
    return html`
      <li>
        <a href=${url} target="_blank">${label}</a>
      </li>`;
  }

  renderActions(stage) {
    if (stage.actions) {
      return html`
        <ol>
         ${stage.actions.map(act => this.renderAction(act, stage))}
        </ol>`;
    } else {
      return nothing;
    }
  }

  renderProgressItem(item) {
    if (!this.progress.hasOwnProperty(item)) {
      return html`<div class="pending">${item}</div>`;
    }

    if (this.progress[item].startsWith('http://') ||
        this.progress[item].startsWith('https://')) {
      return html`<div class="done"><a target="_blank"
        href="${this.progress[item]}"
        >${item}</a></div>`;
    }

    return html`<div class="done">${item}</div>`;
  }


  render() {
    const featureId = this.feature.id;
    return html`
     <div style="position: relative">
     <table>
       <tr>
         <th style="width: 30em;">Stage</th>
         <th style="width: 25em" id="progress-header">Progress</th>
         <th style="width: 12em"></th>
       </tr>

       ${this.process.stages.map(stage => html`
         <tr class="${this.feature.intent_stage_int == stage.outgoing_stage ?
                      'active' : ''}">
           <td>
             <div><b>${stage.name}</b></div>
             <div>${stage.description}</div>
           </td>
           <td>
             ${stage.progress_items.map(item => this.renderProgressItem(item))}
           </td>
           <td>
            ${this.feature.intent_stage_int == stage.outgoing_stage ?
              html`<div><a
                     href="/guide/stage/${featureId}/${stage.outgoing_stage}"
                     class="button primary">Update</a></div>` :
              nothing }
            ${this.isPriorStage(stage) ?
              html`<a href="/guide/stage/${featureId}/${stage.outgoing_stage}"
                   >Revisit</a>` :
              nothing }
            ${this.isStartableStage(stage) ?
              html`<a href="/guide/stage/${featureId}/${stage.outgoing_stage}"
                      class="button primary">Start</a>` :
              nothing }
            ${this.isFutureStage(stage) ?
              html`<a href="/guide/stage/${featureId}/${stage.outgoing_stage}"
                   >Preview</a>` :
              nothing }

            ${this.renderActions(stage)}
           </td>
         </tr>
       `)}
       <tr>
         <td><b>Final review</b></td>
         <td></td>
         <td>
          <a href="/guide/editall/${featureId}">Edit all fields</a>
         </td>
       </tr>
     </table>

    ${Object.keys(this.progress).length ? html`
      <chromedash-callout
        cue="progress-checkmarks" targetid="progress-header" signedin
        .dismissedCues=${this.dismissedCues}>
          Progress checkmarks appear in this column as you fill in
          fields of the feature entry.  However, you may start the next
          stage regardless of checkmarks.
      </chromedash-callout>` :
      nothing }

    </div>
    `;
  }
}

customElements.define('chromedash-process-overview', ChromedashProcessOverview);
