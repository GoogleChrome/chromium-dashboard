import {LitElement, html} from 'lit-element';

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
      'IN_EXPERIMENTAL_FRAMEWORK': 8,
      'NO_LONGER_PURSUING': 1000,
    };
    this._channels = {};
    this._versions = [];
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

  // Directly called in chromedash-featurelist
  selectMilestone(e) {
    if (e.currentTarget.dataset.version) {
      // Came from an internal click.
      this.selected = e.currentTarget.dataset.version;
      this._fireEvent('query-changed', {version: this.selected});
    } else {
      // Called directly (from outside). e is a feature.
      this.selected = e.browsers.chrome.status.milestone_str;
    }
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
      this._channels.canary,
      this._channels.dev,
      this._channels.beta,
      this._channels.stable,
    ];

    // Consolidate channels if they're the same.
    if (this._channels.canary == this._channels.dev) {
      this._versions.splice(4, 1);
      this._className = 'canaryisdev';
    } else if (this._channels.dev == this._channels.beta) {
      this._versions.splice(5, 1);
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
      <link rel="stylesheet" href="/static/css/elements/chromedash-metadata.css">

      <ul id="versionlist" class="${this._className}">
        ${this._versions.map((version) => html`
          <li data-version="${version}" @click="${this.selectMilestone}"
              ?selected="${this.selected === version}">${version}</li>
          `)}
      </ul>
      <div ?hidden="${!this._fetchError}" class="error">Error fetching version information.</div>
    `;
  }
}

customElements.define('chromedash-metadata', ChromedashMetadata);
