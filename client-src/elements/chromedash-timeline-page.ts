import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import './chromedash-timeline.js';
import {showToastMessage} from './utils.js';
import {property} from 'lit/decorators.js';
import {Property} from './datatypes.js';

export class ChromedashTimelinePage extends LitElement {
  @property({type: String})
  type = '';

  @property({type: String})
  view = '';

  @property({attribute: false})
  props: Property[] = [];

  @property({attribute: false})
  selectedBucketId = '1';

  static get styles() {
    return [...SHARED_STYLES, css``];
  }

  connectedCallback() {
    super.connectedCallback();

    let endpoint = `/data/blink/${this.type}props`;

    // [DEV] Change to true to use the staging server endpoint for development
    const devMode = false;
    if (devMode) endpoint = 'https://cr-status-staging.appspot.com' + endpoint;
    const options: RequestInit = {credentials: 'omit'};

    fetch(endpoint, options)
      .then(res => res.json())
      .then(props => {
        this.props = props;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  renderSubheader() {
    const typeText = this.type == 'css' ? 'CSS' : 'HTML & JavaScript';
    const viewText = this.view == 'animated' ? 'animated' : 'all';
    const propText = this.type == 'css' ? 'properties' : 'features';
    const subTitleText = `${typeText} usage metrics > ${viewText} ${propText} > timeline`;
    return html`
      <div id="subheader">
        <h2 id="breadcrumbs">
          <a href="/metrics/${this.type}/${this.view}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon> </a
          >${subTitleText}
        </h2>
      </div>
    `;
  }

  renderDataPanel() {
    return html`
      <chromedash-timeline
        .type=${this.type}
        .view=${this.view}
        .props=${this.props}
        .selectedBucketId=${this.selectedBucketId}
      >
      </chromedash-timeline>
    `;
  }

  render() {
    return html` ${this.renderSubheader()} ${this.renderDataPanel()} `;
  }
}

customElements.define('chromedash-timeline-page', ChromedashTimelinePage);
