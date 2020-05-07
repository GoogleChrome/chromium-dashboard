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
      revisit: {type: String},
      start: {type: String},
      preview: {type: String},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.process = [];
    this.progress = [];
    this.revisit = 'Revisit';
    this.start = 'Start';
    this.preview = 'Preview';
  }

  render() {
    let featureId = this.feature.id;
    return html`
     <table cellspacing=0>
       <tr>
         <th width="100">Stage</th>
         <th width="200">Progres</th>
         <th width="80"></th>
       </tr>

       ${this.process.map(stage => html`
         <tr class="${this.feature.intent_stage_int == stage.incoming_stage ? 'active' : ''}">
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
            ${this.feature.intent_stage_int > stage.incoming_stage ?
              html`<a href="/guide/stage/${featureId}/${stage.incoming_stage}">${this.revisit}</a>` :
              nothing }
            ${this.feature.intent_stage_int == stage.incoming_stage ?
              html`<a href="/guide/stage/${featureId}/${stage.incoming_stage}" class="buttonify">${this.start}</a>` :
              nothing }
            ${this.feature.intent_stage_int < stage.incoming_stage ?
              html`<a href="/guide/stage/${featureId}/${stage.incoming_stage}">${this.preview}</a>` :
              nothing }
           </td>
       `)}
     </table>
    `;
  }
}

customElements.define('chromedash-process-overview', ChromedashProcessOverview);
