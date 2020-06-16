import {LitElement, html} from 'lit-element';
import {nothing} from 'lit-html';
import '@polymer/iron-icon';
import './chromedash-color-status';

import style from '../css/elements/chromedash-process-overview.css';

class ChromedashProcessOverview extends LitElement {
  static styles = style;

  static get properties() {
    return {
      feature: {type: Object},
      process: {type: Array},
      progress: {type: Array},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.process = [];
    this.progress = [];
  }

  inFinalStage() {
    return ['Shipped', 'Removed', 'Parked'].includes(
      this.feature.intent_stage);
  }

  /* A stage is "prior" if it would set a intent_stage that this feature
     has already passed. */
  isPriorStage(stage) {
    if (this.inFinalStage()) {
      return true;
    }
    let stageOrder = this.process.stages.map(s => s.outgoing_stage);
    let viewedOutgoingStageIndex = stageOrder.indexOf(stage.outgoing_stage);
    let featureStageIndex = stageOrder.indexOf(this.feature.intent_stage_int);
    return (viewedOutgoingStageIndex < featureStageIndex);
  }

  /* A stage is "startable" if its incoming stage is the stage that the
     feature is on or has already passed, but its outgoing stage has
     not alrady been passed. */
  isStartableStage(stage) {
    if (this.inFinalStage()) {
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
    if (this.inFinalStage()) {
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

  render() {
    let featureId = this.feature.id;
    return html`
     <table>
       <tr>
         <th style="width: 30em;">Stage</th>
         <th style="width: 25em">Progress</th>
         <th style="width: 12em"></th>
       </tr>

       ${this.process.stages.map(stage => html`
         <tr class="${this.feature.intent_stage_int == stage.outgoing_stage ?
                      'active' : ''}">
           <td>
             <div><b>${stage.name}</b></div>
             <div>${stage.description}</div>
           </td>
           <td>${stage.progress_items.map(item => html`
             <div class="${this.progress.includes(item) ? 'done' : 'pending'}">
                  ${item}</div>
           `)}
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
     </table>
    `;
  }
}

customElements.define('chromedash-process-overview', ChromedashProcessOverview);
