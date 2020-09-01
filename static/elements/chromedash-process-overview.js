import {LitElement, html} from 'lit-element';
import {nothing} from 'lit-html';
import '@polymer/iron-icon';
import './chromedash-callout';
import './chromedash-color-status';

import style from '../css/elements/chromedash-process-overview.css';

class ChromedashProcessOverview extends LitElement {
  static styles = style;

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
    let stageOrder = this.process.stages.map(s => s.outgoing_stage);
    let viewedOutgoingStageIndex = stageOrder.indexOf(stage.outgoing_stage);
    let featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedOutgoingStageIndex < featureStageIndex);
  }

  /* A stage is "startable" if its incoming stage is the stage that the
     feature is on or has already passed, but its outgoing stage has
     not alrady been passed. */
  isStartableStage(stage) {
    if (this.inFinalStage(stage)) {
      return false;
    }
    let stageOrder = this.process.stages.map(s => s.outgoing_stage);
    let viewedIncomingStageIndex = stageOrder.indexOf(stage.incoming_stage);
    let viewedOutgoingStageIndex = stageOrder.indexOf(stage.outgoing_stage);
    let featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedIncomingStageIndex <= featureStageIndex &&
            viewedOutgoingStageIndex > featureStageIndex);
  }

  /* A stage is "future" if the feature has not yet reached its incoming stage. */
  isFutureStage(stage) {
    if (this.inFinalStage(stage)) {
      return false;
    }
    let stageOrder = this.process.stages.map(s => s.outgoing_stage);
    let viewedIncomingStageIndex = stageOrder.indexOf(stage.incoming_stage);
    let featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedIncomingStageIndex > featureStageIndex);
  }

  renderAction(action) {
    const label = action[0];
    const url = action[1].replace('{feature_id}', this.feature.id);
    return html`
      <li>
        <a href=${url} target="_blank">${label}</a>
      </li>`;
  }

  renderActions(stage) {
    return stage.actions.map(act => this.renderAction(act));
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
    let featureId = this.feature.id;
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
                     class="button primary">Update</a></div>
                   <ol>${this.renderActions(stage)}</ol>` :
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
