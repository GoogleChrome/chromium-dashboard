import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import './chromedash-callout';
import './chromedash-dialog';
import SHARED_STYLES from '../css/shared.css';

class ChromedashProcessOverview extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      process: {type: Array},
      progress: {type: Object},
      dismissedCues: {type: Object},
      pendingItems: {type: Array},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.process = [];
    this.progress = {};
    this.dismissedCues = {};
    this.pendingItems = [];
    this.item_stage_map = null; // null means uninitialized.
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

      ol.missingPrereqs li {
        list-style: circle;
        margin-left: 2em;
      }

      .edit-progress-item {
        visibility: hidden;
        margin-left: var(--content-padding-half);
      }

      .pending:hover .edit-progress-item,
      .done:hover .edit-progress-item {
        visibility: visible;
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
    const label = action.name;
    const checkCompletion = () => {
      const url = action.url
        .replace('{feature_id}', this.feature.id)
        .replace('{outgoing_stage}', stage.outgoing_stage);
      const pendingItemsNames = action.prerequisites.filter(
        itemName => {
          return !this.progress.hasOwnProperty(itemName);
        });
      const pendingItems = pendingItemsNames.map(name => {
        // return {name, field, stage} for the named item.
        return this.item_stage_map[name];
      });
      if (pendingItems.length > 0) {
        pendingItems.continueUrl = url;
        console.info('url', url);
        this.pendingItems = pendingItems; // Note: one assignment to this.pendingItems.
        // Open the dialog.
        this.shadowRoot.querySelector('chromedash-dialog').open();
        return;
      } else {
        // Act like user clicked left button to go to the draft email window.
        const draftWindow = window.open(url, '_blank');
        draftWindow.focus();
      }
    };
    return html`
      <li>
        <a @click=${checkCompletion}>${label}</a>
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

  renderEditLink(stage, item) {
    const featureId = this.feature.id;
    let editEl = nothing;
    if (item.field) {
      editEl = html`
        <a class="edit-progress-item"
           href="/guide/stage/${featureId}/${stage.outgoing_stage}#id_${item.field}">
          Edit
        </a>
      `;
    }
    return editEl;
  }

  renderProgressItem(stage, item) {
    const editEl = this.renderEditLink(stage, item);

    if (!this.progress.hasOwnProperty(item.name)) {
      return html`
        <div class="pending">
          ${item.name}
          ${editEl}
        </div>`;
    }

    const progressValue = this.progress[item.name];
    if (progressValue.startsWith('http://') ||
        progressValue.startsWith('https://')) {
      return html`
        <div class="done">
          <a target="_blank" href="${progressValue}">
            ${item.name}
          </a>
          ${editEl}
        </div>`;
    }

    return html`
      <div class="done">
        ${item.name}
        ${editEl}
      </div>`;
  }


  render() {
    if (this.process && this.item_stage_map == null) {
      // We will need to find the stages of prerequisites for actions of each stage.
      // So we will loop over all progress items of all stages
      // one time to rebuild this map at the start of each full page render.
      this.item_stage_map = {};
      this.process.stages.forEach(
        stage => stage.progress_items.forEach(
          item => {
            this.item_stage_map[item.name] = {...item, stage: stage};
          },
        ));
    }

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
             ${stage.progress_items.map(item =>
                        this.renderProgressItem(stage, item))}
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

    <chromedash-dialog heading="Missing Prerequisites">
      <ol class="missingPrereqs">
        ${this.pendingItems.map((item) =>
        html`<li class="pending">
          ${item.stage.name}:
          ${item.name} ${this.renderEditLink(item.stage, item)}</li>`)}
      </ol>
      <a href="${this.pendingItems.continueUrl}" target="_blank" class="button secondary">Proceed</a>
    </chromedash-dialog>
    `;
  }
}

customElements.define('chromedash-process-overview', ChromedashProcessOverview);
