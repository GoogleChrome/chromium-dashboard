import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';
import 'https://unpkg.com/@polymer/iron-icon/iron-icon.js?module';

class ChromedashSamplePanel extends LitElement {
  static get properties() {
    return {
      categories: {type: Object}, // Edited in static/js/samples.js
      features: {type: Array}, // Edited in static/js/samples.js
      filtered: {type: Array}, // Edited in static/js/samples.js
      prevSelectedCategory: {type: Object},
    };
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
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

  _onSelectCategory() {
    // Enable toggling selected item until
    // https://github.com/PolymerElements/paper-menu/issues/50 is fixed.
    if (this.selectedCategory === this.prevSelectedCategory) {
      categoryMenuEl.selected = null;
      this.selectedCategory = null;
      this.prevSelectedCategory = null;
    } else {
      this.prevSelectedCategory = this.selectedCategory;
    }
    this.filter(searchEl.value);
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

  // TODO: move filtering into a behavior. Mostly duped from chromedash-featurelist.html.
  filter(val) {
    let features = this.features;

    if (!features) {
      return;
    }

    if (!val && !this.selectedCategory) {
      if (history && history.replaceState) {
        history.replaceState('', document.title, location.pathname + location.search);
      } else {
        location.hash = '';
      }
      this.filtered = features;
      this._fireEvent('update-length', {lenght: this.filtered.length});

      return;
    }

    if (val) {
      val = val.trim();

      if (history && history.replaceState) {
        // TODO debounce this 500ms
        history.replaceState({}, document.title, '/samples#' + val);
      }

      // Returns operator and version query e.g. ["<=25", "<=", "25"].
      const operatorMatch = /^([<>=]=?)\s*([0-9]+)/.exec(val);
      if (operatorMatch) {
        features = this._filterOnOperation(features, operatorMatch[1], operatorMatch[2]);
      } else {
        const regex = new RegExp(val, 'i');
        features = features.filter((feature) => {
          return regex.test(feature.name) || regex.test(feature.summary);
        });
      }
    }

    // Further refine list based on selected category in menu.
    if (this.selectedCategory) {
      const category = this.selectedCategory.textContent.trim();
      const regex = new RegExp(category, 'i');
      features = features.filter((feature) => {
        return regex.test(feature.category);
      });
    }

    this.filtered = features;

    this._fireEvent('update-length', {lenght: this.filtered.length});
  }

  render() {
    return html`
      <div id="sample-panel">
        <ul id="samplelist" class="card-content">
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
                    ${this.feature.sample_links.map((link) => html`
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
      </div>
    `;
  }
}

customElements.define('chromedash-sample-panel', ChromedashSamplePanel);

// TODO: move this into a behavior. It's duplicated from chromedash-featurelist.html.
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
