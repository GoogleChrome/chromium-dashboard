import {LitElement, html} from 'https://unpkg.com/@polymer/lit-element@latest/lit-element.js?module';
import 'https://unpkg.com/@polymer/iron-list/iron-list.js?module';
import './chromedash-feature.js';

class ChromedashFeaturelist extends LitElement {
  static get properties() {
    return {
      whitelisted: {type: Boolean}, // From attribute
      features: {type: Array, reflect: true}, // Directly edited and accessed in template/features.html
      metadataEl: {type: Object}, // The metadata component element. Directly edited in template/features.html
      searchEl: {type: Object}, // The search input element. Directly edited in template/features.html
      filtered: {type: Array},
      _firstLoad: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.features = [];
    this.filtered = [];
    this.whitelisted = false;
    this._firstLoad = true;
    // True when the user has physically scrolled the list for the first time.
    this._hasScrolledList = false;
  }

  updated(changedProperties) {
    const filteredOldValue = changedProperties.get('filtered');
    if (filteredOldValue) {
      this._filteredChanged(this.filtered, filteredOldValue);
    }
  }

  connectedCallback() {
    this._fireEvent('featurelist-ready');
    window.addEventListener('scroll', this._onScrollList.bind(this));
  }

  disconnectedCallback() {
    window.removeEventListener('scroll', this._onScrollList.bind(this));
  }

  _fireEvent(eventName, detail) {
    let event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  _getSearchStrRegExp(searchStr) {
    return new RegExp(
      // Case-insensitive match on literal string; escape characters that
      // have special meaning in regular expressions.
      searchStr.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, '\\$&'), 'i');
  }

  _pathToPropertyVal(propPath, feature) {
    return propPath.split('.').reduce((obj, key) => {
      return obj[key];
    }, feature);
  }

  _lt(propPath, value, feature) {
    return this._pathToPropertyVal(propPath, feature) < value;
  }
  _lte(propPath, value, feature) {
    return this._pathToPropertyVal(propPath, feature) <= value;
  }
  _gt(propPath, value, feature) {
    return this._pathToPropertyVal(propPath, feature) > value;
  }
  _gte(propPath, value, feature) {
    return this._pathToPropertyVal(propPath, feature) >= value;
  }
  _eq(propPath, value, feature) {
    return this._pathToPropertyVal(propPath, feature) === value;
  }
  _false() {
    return false;
  }

  _getOperatorFilter(args /* [propPath, operator, valueStr] */) {
    const value = parseFloat(args[2]);
    if (isNaN(value)) return this._false;

    switch (args[1].trim()) {
      case '<':
        return this._lt.bind(this, args[0], value);
        break;
      case '<=':
        return this._lte.bind(this, args[0], value);
        break;
      case '>':
        return this._gt.bind(this, args[0], value);
        break;
      case '>=':
        return this._gte.bind(this, args[0], value);
        break;
      case '=': // Support both '=' and '=='.
      case '==':
        return this._eq.bind(this, args[0], value);
        break;
      default:
        return this._false;
    }
  }

  _filterProperty(propPath, regExp, feature) {
    const value = this._pathToPropertyVal(propPath, feature);

    // Null or missing values never match.
    if (value === null || typeof value === 'undefined') {
      return false;
    }

    // Allow for enums that store string in "text" property.
    return (value.text || value).toString().match(regExp) !== null;
  }

  _getPropertyFilter(args /* [propPath, searchStr] */) {
    return this._filterProperty.bind(
      this, args[0], this._getSearchStrRegExp(args[1]));
  }

  _filterKeyword(regExp, feature) {
    return (feature.name + '\n' + feature.summary + '\n' + feature.comments)
      .match(regExp) !== null;
  }

  _getKeywordFilter(keyword) {
    return this._filterKeyword.bind(
      this, this._getSearchStrRegExp(keyword));
  }

  // Directly called from template/features.html
  filter(val) {
    // Clear filter if there's no search or if called directly.
    if (!val) {
      if (history && history.replaceState) {
        history.replaceState('', document.title, location.pathname + location.search);
      } else {
        location.hash = '';
      }
      this.filtered = this.features;
    } else {
      val = val.trim();
      if (history && history.replaceState) {
        history.replaceState({id: null}, document.title,
          '/features#' + encodeURIComponent(val));
      }

      const blinkComponent = val.match(/^component:\s?(.*)/);
      if (blinkComponent) {
        const componentName = blinkComponent[1].trim();
        const results = this.features;
        this.filtered = results.filter(feature => (
          feature.browsers.chrome.blink_components.includes(componentName)
        ));
        this._fireEvent('filtered', {count: this.filtered.length});
        return;
      }

      const regExp = /"([^"]*)"/g;
      const start = 0;
      const parts = [];
      let match;
      while ((match = regExp.exec(val)) !== null) {
        if (start - (regExp.lastIndex - match[0].length) > 0) {
          parts.push(val.substring(start, regExp.lastIndex -
                                   match[0].length));
        }
        parts.push(match[1]);
      }
      const matchLen = match ? match[0].length : 0;
      if (start - (regExp.lastIndex - matchLen) > 0) {
        parts.push(val.substring(start, regExp.lastIndex -
                                 matchLen));
      }

      // Match words separated by whitespace and/or ":" and/or ordered
      // comparison operator.
      const wordRegExp = /("([^"]+)"|([^:<>= \f\n\r\t\v\u00a0\u1680\u180e\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+))([:<>= \f\n\r\t\v\u00a0\u1680\u180e\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+)?/g;
      // Array of matches, each an array of the form:
      // [ full match, quoted-string-or-word, contents-of-quoted-string,
      //   word, separator ].
      const reMatches = [];
      while ((match = wordRegExp.exec(val)) !== null) {
        reMatches.push(match);
      }

      // Query parts of the form: "name : value".
      const propertyQueries = [];
      // Query parts of the form: "name = value", "name < value", etc.
      const operatorQueries = [];
      // Other words in the query (not matching forms above).
      const keywordQueries = [];

      // Accumulate keyword and property queries.
      for (let i = 0; i < reMatches.length; i++) {
        match = reMatches[i];
        const part = match[2] || match[3];
        const sep = match[4];
        const nextPart = i < reMatches.length - 1 ?
          (reMatches[i + 1][2] || reMatches[i + 1][3]) : null;
        if (sep && sep.trim().match(/^:$/) !== null && nextPart !== null) {
          // Separator is ":", and there exists a right-hand-side.
          // Store property query: "propertyName : propertyValue".
          propertyQueries.push([part, nextPart]);
          i++;
        } else if (sep && sep.trim().match(/^(<=|>=|==|<|>|=)$/) !== null &&
            nextPart !== null) {
          // Separator is an ordered comparison operator and there exists a
          // right-hand-side.
          // Store operator query "name <<operator>> value".
          operatorQueries.push([part, sep, nextPart]);
          i++;
        } else {
          // No special operator found. Store non-separator part as keyword
          // query.
          keywordQueries.push(part);
        }
      }

      // Construct a list filter for each query part, and store them all in
      // a list.
      const filters = propertyQueries.map(this._getPropertyFilter.bind(this))
        .concat(operatorQueries.map(this._getOperatorFilter.bind(this)))
        .concat(keywordQueries.map(this._getKeywordFilter.bind(this)));

      // Apply this.filtered = this.features filtered-by filters.
      if (filters.length === 0) {
        this.filtered = this.features;
      } else {
        const results = this.features;
        for (let i = 0; i < filters.length; i++) {
          results = results.filter(filters[i]);
        }
        this.filtered = results;
      }
    }

    this._fireEvent('filtered', {count: this.filtered.length});
  }

  // Returns the index of the first feature of a given milestone string.
  firstOfMilestone(milestone, optStartFrom) {
    const start = optStartFrom != undefined ? optStartFrom : 0;
    for (let i = start, feature; feature = this.filtered[i]; ++i) {
      if (feature.first_of_milestone &&
          (milestone === feature.browsers.chrome.desktop ||
           milestone === feature.browsers.chrome.status.text)) {
        return i;
      }
    }
    return -1;
  }

  scrollToMilestone(milestone) {
    const idx = this.firstOfMilestone(milestone);
    if (idx !== -1) {
      this.$.ironlist.scrollToIndex(idx);
    }
  }

  // Directly called from template/features.html
  scrollToFeature(id) {
    if (!id) {
      return;
    }
    for (let i = 0, f; f = this.filtered[i]; ++i) {
      if (f.id == id) {
        this.set(['filtered', i, 'open'], true); // trigger feature panel open.
        this.$.ironlist.scrollToIndex(i);
        return;
      }
    }
  }

  _onScrollList() {
    if (this._firstLoad) {
      return;
    }
    if (!this._hasScrolledList) {
      this._hasScrolledList = true;
      this._fireEvent('has-scroll-list');
    }
    const feature = this.features[this.$.ironlist.firstVisibleIndex];
    this.metadataEl.selectMilestone(feature);
  }

  /* eslint no-unused-vars: ["error", { "args": "after-used" }] */
  _onFeatureToggled(e, detail) {
    const feature = detail.feature;
    const open = detail.open;

    // Height of item changed. See github.com/PolymerElements/iron-list/issues/13.
    // this.$.ironlist.updateSizeForItem(feature);
    this.$.ironlist._update(); // force entire list to update.

    if (history && history.replaceState) {
      if (open) {
        history.pushState({id: feature.id}, feature.name, '/features/' + feature.id);
      } else {
        const hash = this.searchEl.value ? '#' + this.searchEl.value : '';
        history.replaceState({id: null}, feature.name, '/features' + hash);
      }
    }
  }

  _deepLinkToFeature() {
    this._firstLoad = false;

    // TODO(ericbidelman): Originally introduced to fix a bug in ironlist.
    // Looks fixed now and removing this call helps page load perf!
    // this.$.ironlist._update(); // force update to list.

    // If there's an id in the URL, highlight and scroll to the feature.
    // Otherwise, go to the first "in development" feature.
    // TODO: really want this in ready(), but featureLiList and metadata may
    // not be set yet due to timing issues.
    const lastSlash = location.pathname.lastIndexOf('/');
    if (lastSlash > 0) {
      const id = parseInt(location.pathname.substring(lastSlash + 1));
      this.scrollToFeature(id);
    } else {
      const milestone = this.metadataEl.implStatuses[
        this.metadataEl.status.IN_DEVELOPMENT - 1].val;
      this.scrollToMilestone(milestone);
    }
  }

  _filteredChanged(newVal, oldVal) {
    if (oldVal === undefined || newVal.length === oldVal.length ||
        !this._firstLoad) {
      return;
    }

    this._fireEvent('app-ready');

    setTimeout(() => {
      this._deepLinkToFeature();
    }, 300);
  }

  _computeMilestoneHidden(feature, features, filtered) {
    return filtered.length != features.length || !feature.first_of_milestone;
  }

  _computeMilestoneString(str) {
    return isNaN(parseInt(str)) ? str : 'Chrome ' + str;
  }

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/elements/chromedash-featurelist.css">

      <div id="featurelist">
        <iron-list id="ironlist" scroll-target="document" items="${this.filtered}" as="feature">
          <template>
            <div class="item">
              <div ?hidden="${this._computeMilestoneHidden(feature, this.features, this.filtered)}"
                   class="milestone-marker">${this._computeMilestoneString(feature.browsers.chrome.status.milestone_str)}</div>
              <chromedash-feature id="${feature.id}" tabindex="0"
                   @feature-toggled="${this._onFeatureToggled}"
                   feature="${feature}" ?whitelisted="${this.whitelisted}"></chromedash-feature>
            </div>
          </template>
        </iron-list>
      </div>
    `;
  }
}

customElements.define('chromedash-featurelist', ChromedashFeaturelist);
