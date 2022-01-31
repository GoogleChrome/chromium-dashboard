import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';
import SHARED_STYLES from '../css/shared.css';

class ChromedashSamplePanel extends LitElement {
  static get properties() {
    return {
      categories: {attribute: false}, // Edited in static/js/samples.js
      features: {attribute: false}, // Edited in static/js/samples.js
      filtered: {attribute: false}, // Edited in static/js/samples.js
    };
  }

  static get styles() {
    return [
      SHARED_STYLES,
      css`
      :host {
        display: block;
        position: relative;
        max-width: 750px;
      }

      ul {
        padding: 0;
      }

      li {
        margin-bottom: var(--content-padding);
        line-height: 1.4;
        list-style: none;
      }

      .card {
        background: #fff;
        padding: var(--content-padding);
        box-shadow: var(--card-box-shadow);
      }
      .card iron-icon {
        flex-shrink: 0;
      }

      .feature-name {
        font-weight: 400;
        display: flex;
        justify-content: space-between;
        margin: 0;
      }

      .sample_links {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .milestone {
        font-size: 16px;
        white-space: nowrap;
      }

      .summary {
        margin: var(--content-padding) 0;
      }

      .demo-links {
        margin-right: var(--content-padding);
        font-weight: 400;
        display: flex;
        flex-wrap: wrap;
      }

      .demo-link {
        background-color: var(--table-alternate-background);
        margin: var(--content-padding-half) var(--content-padding-half) 0 0;
        display: block;
        padding: var(--content-padding-half);
        text-transform: uppercase;
      }
      .demo-link:hover {
        text-decoration: none;
      }
    `];
  }

  connectedCallback() {
    super.connectedCallback();
    this._loadData();
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  async _loadData() {
    // Fire of samples.json XHR right away so data can populate faster.
    const url = '/samples.json';
    this.features = await (await fetch(url)).json();
    this.features.forEach((feature) => {
      feature.resources.samples = feature.resources.samples.map((link) => {
        return link.replace(/github.com\/GoogleChrome\/samples\/tree\/gh-pages\/(.*)/i, 'googlechrome.github.io/samples/$1');
      });
    });

    this.filtered = this.features;
    this.filter(this.searchEl ? this.searchEl.value : '');
    this._fireEvent('update-length', {length: this.filtered.length});
  }

  _computeIcon(el) {
    return 'chromestatus:' + (el ? el.dataset.category : '');
  }

  _computeIconId(categoryStr) {
    return 'chromestatus:' + this.categories[categoryStr];
  }

  _computeFeatureLink(id) {
    return '/features/' + id;
  }

  _filterOnOperation(features, operator, version) {
    return features.filter((feature) => {
      const platformMilestones = [
        parseInt(feature.shipped_milestone),
        parseInt(feature.shipped_android_milestone),
        parseInt(feature.shipped_ios_milestone),
        parseInt(feature.shipped_webview_milestone),
      ];
      for (let i = 0, milestone; milestone = platformMilestones[i]; ++i) {
        if (matchesMilestone_(milestone, operator, version)) {
          return true; // Only one of the platforms needs to match.
        }
      }
    });
  }

  filter(query, category) {
    let features = this.features;

    if (!features) {
      return;
    }

    if (!query && !category) {
      if (history && history.replaceState) {
        history.replaceState('', document.title, location.pathname + location.search);
      } else {
        location.hash = '';
      }
      this.filtered = features;
      this._fireEvent('update-length', {length: this.filtered.length});

      return;
    }

    if (query) {
      if (history && history.replaceState) {
        // TODO debounce this 500ms
        history.replaceState({}, document.title, '/samples#' + query);
      }

      // Returns operator and version query e.g. ["<=25", "<=", "25"].
      const operatorMatch = /^([<>=]=?)\s*([0-9]+)/.exec(query);
      if (operatorMatch) {
        features = this._filterOnOperation(features, operatorMatch[1], operatorMatch[2]);
      } else {
        const regex = new RegExp(query, 'i');
        features = features.filter((feature) => {
          return regex.test(feature.name) || regex.test(feature.summary);
        });
      }
    }

    // Further refine list based on selected category in menu.
    if (category) {
      const regex = new RegExp(category, 'i');
      features = features.filter((feature) => {
        return regex.test(feature.category);
      });
    }

    this.filtered = features;

    this._fireEvent('update-length', {length: this.filtered.length});
  }

  render() {
    if (!this.filtered) {
      return nothing;
    }
    return html`
      <ul>
        ${this.filtered.map((feature) => html`
          <li>
            <div class="card">
              <h3 class="feature-name">
                <a href="${this._computeFeatureLink(feature.id)}">${feature.name}</a>
                <span class="milestone" ?hidden="${!feature.shipped_milestone}">Chrome <span>${feature.shipped_milestone}</span></span>
              </h3>
              <div class="summary">${feature.summary}</div>
              <div class="sample_links">
                <div class="demo-links layout horizontal center">
                  ${feature.resources.samples.map((link) => html`
                    <a href="${link}" target="_blank" class="demo-link">
                      <iron-icon icon="chromestatus:open-in-browser"></iron-icon> View Demo
                    </a>
                    `)}
                </div>
                <iron-icon icon="${this._computeIconId(feature.category)}"
                           title="${feature.category}"></iron-icon>
              </div>
            </div>
          </li>
          `)}
      </ul>
    `;
  }
}

customElements.define('chromedash-sample-panel', ChromedashSamplePanel);

function matchesMilestone_(milestone, operator, version) {
  switch (operator) {
    case '<':
      return milestone < version;
      break;
    case '<=':
      return milestone <= version;
      break;
    case '>':
      return milestone > version;
      break;
    case '>=':
      return milestone >= version;
      break;
    case '=': // Support both '=' and '=='.
    case '==':
      return milestone == version;
      break;
    default:
      return false;
  }
}
