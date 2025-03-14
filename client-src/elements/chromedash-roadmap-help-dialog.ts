import {LitElement, css, html} from 'lit';
import {customElement} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';

let roadmapHelpDialogEl;

export async function openRoadmapHelpDialog() {
  if (!roadmapHelpDialogEl) {
    roadmapHelpDialogEl = document.createElement(
      'chromedash-roadmap-help-dialog'
    );
    document.body.appendChild(roadmapHelpDialogEl);
    await roadmapHelpDialogEl.updateComplete;
  }
  roadmapHelpDialogEl.show();
}

@customElement('chromedash-roadmap-help-dialog')
export class ChromedashRoadmapHelpDialog extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #dialog-content {
          max-width: 60rem;
        }
        #legend li {
          padding: var(--content-padding-quarter);
          white-space: nowrap;
        }
        #legend span {
          display: inline-block;
          width: 8em;
        }

        #legend sl-icon {
          width: 26px;
          height: 18px;
        }
        sl-icon.not-started {
          color: var(--gate-preparing-icon-color);
        }
        sl-icon.in-progress {
          color: var(--gate-pending-icon-color);
        }
        sl-icon.needs-work {
          color: var(--gate-needs-work-icon-color);
        }
        sl-icon.approved {
          color: var(--gate-approved-icon-color);
        }
        sl-icon.denied {
          color: var(--gate-denied-icon-color);
        }
      `,
    ];
  }

  show() {
    this.renderRoot.querySelector('sl-dialog')?.show();
  }

  hide() {
    this.renderRoot.querySelector('sl-dialog')?.hide();
  }

  renderDialogContent() {
    return html`
      <div id="dialog-content">
        <ul id="legend">
          <li>
            <sl-icon
              library="material"
              class="approved"
              name="check_circle_filled_20px"
            ></sl-icon>
            <span>Approved</span>
            <td>Reviewers approved feature at this stage</td>
          </li>
          <li>
            <sl-icon
              library="material"
              class="not-started"
              name="arrow_circle_right_20px"
            ></sl-icon>
            <span>Not started</span>
            <td>Feature owners have not requested reviews yet</td>
          </li>
          <li>
            <sl-icon
              library="material"
              class="in-progress"
              name="pending_20px"
            ></sl-icon>
            <span>In-progress</span>
            <td>Not all reviews have finished</td>
          </li>
          <li>
            <sl-icon
              library="material"
              class="needs-work"
              name="autorenew_20px"
            ></sl-icon>
            <span>Needs work</span>
            <td>Reviewers have asked for changes</td>
          </li>
          <li>
            <sl-icon
              library="material"
              class="denied"
              name="block_20px"
            ></sl-icon>
            <span>Denied</span>
            <td>Reviewers suggested directional changes</td>
          </li>
        </ul>
      </div>
    `;
  }

  render() {
    return html`
      <sl-dialog label="Roadmap legend" style="--width:fit-content">
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}
