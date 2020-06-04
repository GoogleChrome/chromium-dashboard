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

  render() {
    let featureId = this.feature.id;
    return html`
     <table>
       <tr>
         <th style="width: 100px;">Stage</th>
         <th style="width: 200px">Progress</th>
         <th style="width: 80px"></th>
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
                     href="/guide/stage/${featureId}/${stage.incoming_stage}"
                     class="button primary">Update</a></div>
                   <!-- TODO(jrobbins): Preview email and other actions -->` :
              nothing }
            ${this.feature.intent_stage_int > stage.incoming_stage &&
              this.feature.intent_stage_int != stage.outgoing_stage ?
              html`<a href="/guide/stage/${featureId}/${stage.incoming_stage}"
                   >Revisit</a>` :
              nothing }
            ${this.feature.intent_stage_int == stage.incoming_stage ?
              html`<a href="/guide/stage/${featureId}/${stage.incoming_stage}"
                      class="button primary">Start</a>` :
              nothing }
            ${this.feature.intent_stage_int < stage.incoming_stage ?
              html`<a href="/guide/stage/${featureId}/${stage.incoming_stage}"
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
