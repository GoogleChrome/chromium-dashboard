import {LitElement, css, html} from 'lit-element';
import {ifDefined} from 'lit-html/directives/if-defined.js';
import SHARED_STYLES from '../css/shared.css';

class ChromedashMetadata extends LitElement {
  static get properties() {
    return {
      implStatuses: {type: Array}, // Read in chromedash-featurelist.
      status: {attribute: false}, // Read in chromedash-featurelist.
      selected: {attribute: false}, // Directly edited in /templates/features.html
      _className: {attribute: false},
      _fetchError: {attribute: false},
      _channels: {attribute: false},
      _versions: {attribute: false},
    };
  }

  constructor() {
    super();
    this.implStatuses = [];
    this.status = {
      'NO_ACTIVE_DEV': 1,
      'PROPOSED': 2,
      'IN_DEVELOPMENT': 3,
      'BEHIND_A_FLAG': 4,
      'ENABLED_BY_DEFAULT': 5,
      'DEPRECATED': 6,
      'REMOVED': 7,
      'ORIGINTRIAL': 8,
      'INTERVENTION': 9,
      'ON_HOLD': 10,
      'NO_LONGER_PURSUING': 1000,
    };
    this._channels = {};
    this._versions = [];
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        display: block;
        contain: content;
      }

      #versionlist {
        background-color: inherit;
        color: var(--leftnav-link-color);
        padding: 0;
        margin: 0;
      }

      .canaryisdev li:nth-of-type(5)::after {
        content: 'canary/dev';
      }
      .canaryisdev li:nth-of-type(6)::after {
        content: 'beta';
      }
      .canaryisdev li:nth-of-type(7)::after {
        content: 'stable';
      }
      .canaryisdev li:nth-of-type(8)::after {
        content: '';
      }

      .betaisdev li:nth-of-type(5)::after {
        content: 'canary';
      }
      .betaisdev li:nth-of-type(6)::after {
        content: 'dev/beta';
      }
      .betaisdev li:nth-of-type(7)::after {
        content: 'stable';
      }
      .betaisdev li:nth-of-type(8)::after {
        content: '';
      }

      li {
          cursor: pointer;
          list-style: none;
          padding: var(--content-padding-quarter) 0;
      }

      li::before {
        content: '';
        margin-right: var(--content-padding-half);
        border-left: 2px solid transparent;
      }
      li::after {
        margin-left: var(--content-padding-half);
      }

      li:nth-of-type(4) {
        border-bottom: var(--leftnav-divider-border);
        padding-bottom: var(--content-padding-half);
        margin-bottom: var(--content-padding-half);
      }
      li:nth-of-type(5)::after {
        content: 'canary';
      }
      li:nth-of-type(6)::after {
        content: 'dev';
      }
      li:nth-of-type(7)::after {
        content: 'beta';
      }
      li:nth-of-type(8)::after {
        content: 'stable';
      }

      li[selected] {
        font-weight: 500;
        color: var(--leftnav-selected-color);
      }
      li[selected]::before {
        border-color: var(--leftnav-selected-color);
      }

      .error {
        font-weight: 500;
        font-style: italic;
        margin: 100px 0 0 5px;
        color: var(--error-color);
      }
    `];
  }

  connectedCallback() {
    super.connectedCallback();
    fetch('/omaha_data').then((res) => res.json()).then((response) => {
      this._processResponse(response);
    }).catch(() => {
      this._fetchError = true;
    });
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  _clickMilestone(e) {
    // Came from an internal click.
    this.selected = e.currentTarget.dataset.version;
    this._fireEvent('query-changed', {version: this.selected});
  }

  // Directly called in chromedash-featurelist
  selectMilestone(feature) {
    this.selected = feature.browsers.chrome.status.milestone_str;
  }

  _processResponse(response) {
    // TODO(ericbidelman): Share this data across instances.
    const windowsVersions = response[0];
    for (let i = 0, el; el = windowsVersions.versions[i]; ++i) {
      // Include previous version if current is foobar'd.
      this._channels[el.channel] = parseInt(el.version) || parseInt(el.prev_version);
    }

    this._fireEvent('_channels-update', {lastStableRelease: this._channels.stable});

    // Dev channel explicitly left out. Treat same as canary.
    this._versions = [
      this.implStatuses[this.status.NO_ACTIVE_DEV - 1].val,
      this.implStatuses[this.status.PROPOSED - 1].val,
      this.implStatuses[this.status.IN_DEVELOPMENT - 1].val,
      this.implStatuses[this.status.DEPRECATED - 1].val,
      this._channels.canary,
      this._channels.dev,
      this._channels.beta,
      this._channels.stable,
    ];

    // Consolidate channels if they're the same.
    if (this._channels.canary == this._channels.dev) {
      this._versions.splice(5, 1);
      this._className = 'canaryisdev';
    } else if (this._channels.dev == this._channels.beta) {
      this._versions.splice(6, 1);
      this._className = 'betaisdev';
    }

    for (let i = this._channels.stable - 1; i >= 1; i--) {
      this._versions.push(i);
    }
    const noLongerPursuing = this.implStatuses[this.implStatuses.length - 1].val;
    this._versions.push(noLongerPursuing);
  }

  render() {
    return html`
      <ul id="versionlist" class="${ifDefined(this._className)}">
        ${this._versions.map((version) => html`
          <li data-version="${version}" @click="${this._clickMilestone}"
              ?selected="${this.selected === version}">${version}</li>
          `)}
      </ul>
      <div ?hidden="${!this._fetchError}" class="error">Error fetching version information.</div>
    `;
  }
}

customElements.define('chromedash-metadata', ChromedashMetadata);
