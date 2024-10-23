import {LitElement, css, html} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {ifDefined} from 'lit/directives/if-defined.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Channels} from '../js-src/cs-client.js';

interface ImplStatus {
  key: number;
  val: string;
}

@customElement('chromedash-metadata')
class ChromedashMetadata extends LitElement {
  @property({type: Array})
  implStatuses: ImplStatus[] = [];
  @property({type: Object, attribute: false})
  status = {
    NO_ACTIVE_DEV: 1,
    PROPOSED: 2,
    IN_DEVELOPMENT: 3,
    BEHIND_A_FLAG: 4,
    ENABLED_BY_DEFAULT: 5,
    DEPRECATED: 6,
    REMOVED: 7,
    ORIGINTRIAL: 8,
    INTERVENTION: 9,
    ON_HOLD: 10,
    NO_LONGER_PURSUING: 1000,
  };
  @property({type: String, attribute: false})
  selected!: string;
  @state()
  _className: 'canaryisdev' | 'betaisdev' | undefined;
  @state()
  _fetchError!: boolean;
  @state()
  _channels: Channels = {};
  @state()
  _versions!: (string | number)[];

  static get styles() {
    return [
      ...SHARED_STYLES,
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

        .error {
          font-weight: 500;
          font-style: italic;
          margin: 100px 0 0 5px;
          color: var(--error-color);
        }
      `,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    fetch('/omaha_data')
      .then(res => res.json())
      .then(response => {
        this._processResponse(response);
      })
      .catch(() => {
        this._fetchError = true;
      });
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  _clickMilestone(e) {
    // Came from an internal click.
    this.selected = e.currentTarget.value;
    this._fireEvent('query-changed', {version: this.selected});
  }

  selectInVersionList(index) {
    (
      this.renderRoot.querySelector('#versionlist') as HTMLSelectElement
    ).selectedIndex = index; // log null
  }

  _processResponse(response) {
    // TODO(ericbidelman): Share this data across instances.
    const windowsVersions = response[0];
    for (let i = 0, el; (el = windowsVersions.versions[i]); ++i) {
      // Include previous version if current is foobar'd.
      this._channels[el.channel].version =
        parseInt(el.version) || parseInt(el.prev_version);
    }

    this._fireEvent('_channels-update', {
      lastStableRelease: this._channels.stable,
    });

    // Dev channel explicitly left out. Treat same as canary.
    this._versions = [
      this.implStatuses[this.status.PROPOSED - 1].val,
      this.implStatuses[this.status.IN_DEVELOPMENT - 1].val,
      this.implStatuses[this.status.DEPRECATED - 1].val,
      this._channels.canary.version,
      this._channels.dev.version,
      this._channels.beta.version,
      this._channels.stable.version,
    ];

    // Consolidate channels if they're the same.
    if (this._channels.canary == this._channels.dev) {
      this._versions.splice(4, 1);
      this._className = 'canaryisdev';
    } else if (this._channels.dev == this._channels.beta) {
      this._versions.splice(5, 1);
      this._className = 'betaisdev';
    }

    for (let i = this._channels.canary.version - 1; i >= 1; i--) {
      if (!this._versions.includes(i)) {
        this._versions.push(i);
      }
    }
    const noActiveDev = this.implStatuses[this.status.NO_ACTIVE_DEV - 1].val;
    this._versions.push(noActiveDev);
    const noLongerPursuing =
      this.implStatuses[this.implStatuses.length - 1].val;
    this._versions.push(noLongerPursuing);
    const behindAFlag = this.implStatuses[this.status.BEHIND_A_FLAG - 1].val;
    this._versions.push(behindAFlag);

    const enabledByDefault =
      this.implStatuses[this.status.ENABLED_BY_DEFAULT - 1].val;
    this._versions.push(enabledByDefault);
    const removed = this.implStatuses[this.status.REMOVED - 1].val;
    this._versions.push(removed);
    const originTrial = this.implStatuses[this.status.ORIGINTRIAL - 1].val;
    this._versions.push(originTrial);
    const intervention = this.implStatuses[this.status.INTERVENTION - 1].val;
    this._versions.push(intervention);
    const onHold = this.implStatuses[this.status.ON_HOLD - 1].val;
    this._versions.push(onHold);
  }

  render() {
    return html`
      <select
        id="versionlist"
        class="${ifDefined(this._className)}"
        @change="${this._clickMilestone}"
      >
        <option value="" disabled selected>Select Chrome Version/Status</option>
        ${this._versions.map((version, index) =>
          typeof this._className !== 'undefined'
            ? this._className == 'canaryisdev'
              ? html`<option value="${version}">
                  ${version}
                  ${index == 3
                    ? 'canary/dev'
                    : index == 4
                      ? 'beta'
                      : index == 5
                        ? 'stable'
                        : ''}
                </option>`
              : this._className == 'betaisdev'
                ? html`<option value="${version}">
                    ${version}
                    ${index == 3
                      ? 'canary'
                      : index == 4
                        ? 'dev/beta'
                        : index == 5
                          ? 'stable'
                          : ''}
                  </option>`
                : ''
            : html`<option value="${version}">
                ${version}
                ${index == 3
                  ? 'canary'
                  : index == 4
                    ? 'dev'
                    : index == 5
                      ? 'beta'
                      : index == 6
                        ? 'stable'
                        : ''}
              </option>`
        )}
      </select>
      <div ?hidden="${!this._fetchError}" class="error">
        Error fetching version information.
      </div>
    `;
  }
}
