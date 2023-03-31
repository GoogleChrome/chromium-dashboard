import {LitElement, css, html, nothing} from 'lit';
import './chromedash-callout';
import {
  openPreflightDialog,
  somePendingPrereqs,
} from './chromedash-preflight-dialog';
import {findProcessStage} from './utils';
import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashProcessOverview extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      process: {type: Object},
      progress: {type: Object},
      dismissedCues: {type: Array},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.process = {};
    this.progress = {};
    this.dismissedCues = [];
    this.sameTypeRendered = 0;
  }

  static prereqsId = 0;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host {
        display: block;
        position: relative;
        box-sizing: border-box;
        /* Don't do this, since it interferes with dialog placement.
        contain: content;  */
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

      .missing-prereqs-list {
        padding-bottom: 1em;
      }

      .missing-prereqs-list li {
        list-style: circle;
        margin-left: 2em;
      }

      .edit-progress-item {
        visibility: hidden;
        margin-left: var(--content-padding-half);
      }

      .active .edit-progress-item,
      .missing-prereqs .edit-progress-item,
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

  renderAction(action, stage, feStage) {
    const label = action.name;
    const url = action.url
      .replace('{feature_id}', this.feature.id)
      .replace('{outgoing_stage}', stage.outgoing_stage);

    const checkCompletion = () => {
      if (somePendingPrereqs(action, this.progress)) {
        // Open the dialog.
        openPreflightDialog(
          this.feature, this.progress, this.process, action, stage, feStage);
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

  renderActions(stage, feStage) {
    if (stage.actions) {
      return html`
        <ol>
         ${stage.actions.map(act => this.renderAction(act, stage, feStage))}
        </ol>`;
    } else {
      return nothing;
    }
  }

  renderEditLink(stage, feStage, item) {
    const featureId = this.feature.id;
    let editEl = nothing;
    if (item.field) {
      editEl = html`
        <a class="edit-progress-item"
           href="/guide/stage/${featureId}/${stage.outgoing_stage}/${feStage.id}#id_${item.field}">
          Edit
        </a>
      `;
    }
    return editEl;
  }

  renderProgressItem(stage, feStage, item) {
    const editEl = this.renderEditLink(stage, feStage, item);

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

  renderProcessStage(featureId, feStage) {
    const processStage = findProcessStage(feStage, this.process);
    if (processStage === null) return nothing;

    const isActive = (this.feature.active_stage_id === feStage.id);

    // Choose button based on active stage.
    const buttonHref = `/guide/stage/${featureId}/${processStage.outgoing_stage}/${feStage.id}`;
    let button = html`<a href="${buttonHref}">Edit</a>`;
    if (this.feature.is_enterprise_feature) {
      button = html`<a href="${buttonHref}" class="button primary">Edit</a>`;
    } else if (isActive) {
      button = html`<a href="${buttonHref}" class="button primary">Update</a>`;
    } else if (this.isPriorStage(processStage)) {
      button = html`<a href="${buttonHref}">Revisit</a>`;
    } else if (this.isStartableStage(processStage)) {
      button = html`<a href="${buttonHref}" class="button primary">Start</a>`;
    } else if (this.isFutureStage(processStage)) {
      button = html`<a href="${buttonHref}">Preview</a>`;
    }

    // Add a number differentiation if this stage type is the same as another stage.
    let numberDifferentiation = '';
    if (this.previousStageTypeRendered === feStage.stage_type) {
      this.sameTypeRendered += 1;
      numberDifferentiation = ` ${this.sameTypeRendered}`;
    } else {
      this.previousStageTypeRendered = feStage.stage_type;
      this.sameTypeRendered = 1;
    }
    let sectionName = `${processStage.name}${numberDifferentiation}`;
    if (feStage.display_name) {
      sectionName = `${feStage.display_name} (${processStage.name})`;
    }

    return html`
      <tr class="${isActive ?
                    'active' : ''}">
        <td>
          <div><b>${sectionName}</b></div>
          <div>${processStage.description}</div>
        </td>
        <td>
          ${processStage.progress_items.map(item =>
                      this.renderProgressItem(processStage, feStage, item))}
        </td>
        <td>
          ${button}
          ${this.renderActions(processStage, feStage)}
        </td>
      </tr>`;
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
       ${this.feature.stages.map(feStage => this.renderProcessStage(this.feature.id, feStage))}
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
