import {LitElement, html} from 'lit';
import {FEATURELIST_CSS} from '../css/elements/chromedash-featurelist-css.js';
import {Metric} from '../js-src/metric.js';
import './chromedash-feature';

const MAX_FEATURES_SHOWN = 500;

class ChromedashFeaturelist extends LitElement {
  static styles = FEATURELIST_CSS;

  static get properties() {
    return {
      user: {type: Object},
      isSiteEditor: {type: Boolean},
      signedInUser: {type: String},
      editableFeatures: {type: Object},
      features: {attribute: false}, // Directly edited and accessed in template/features.html
      metadataEl: {attribute: false}, // The metadata component element. Directly edited in template/features.html
      searchEl: {attribute: false}, // The search input element. Directly edited in template/features.html
      filtered: {attribute: false},
      openFeatures: {attribute: false},
      starredFeatures: {attribute: false},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.features = [];
    this.editableFeatures = [];
    this.filtered = [];
    this.metadataEl = document.querySelector('chromedash-metadata');
    this.searchEl = document.querySelector('.search input');
    this.isSiteEditor = false;
    this.signedInUser = '';
    this._hasInitialized = false; // Used to check initialization code.
    this._hasScrolledByUser = false; // Used to set the app header state.
    /* When scrollTo(), we also expand the feature. This is the id of the feature. */
    this.openFeatures = new Set();
    this.starredFeatures = new Set();

    this._featuresUnveilMetric = new Metric('features_unveil');
    this._featuresFetchMetric = new Metric('features_loaded');
    this._featuresUnveilMetric.start();
    this._featuresFetchMetric.start();

    /* The running context `this` inside `renderItem` is `lit-virtualizer`
     * rather than `chromedash-featurelist`, so all function calls inside need
     * to be bound to `this`. */
    this._onFeatureToggledBound = this._onFeatureToggled.bind(this);
    this._onStarToggledBound = this._onStarToggled.bind(this);

    this._loadData();
  }

  async _loadData() {
    const featureUrl = '/features_v2.json';

    try {
      const features = await (await fetch(featureUrl)).json();
      this._featuresFetchMetric
        .end()
        .log()
        .sendToAnalytics('features', 'loaded');

      features.map(feature => {
        feature.receivePush = false;
        if (feature.is_released) {
          feature.milestone = feature.milestone || Infinity;
        }
      });
      this.features = features;

      this.searchEl.disabled = false;
      this.filter(this.searchEl.value);
      this._initialize();
    } catch (error) {
      document.getElementById('content').classList.add('error');
      console.error(error);
      throw new Error('Failed to fetch features');
    }
  }

  _fireEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {detail});
    this.dispatchEvent(event);
  }

  _getSearchStrRegExp(searchStr) {
    return new RegExp(
      // Case-insensitive match on literal string; escape characters that
      // have special meaning in regular expressions.
      searchStr.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, '\\$&'),
      'i'
    );
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

  _setOpenFeatures(featureId, open) {
    const newOpen = new Set(this.openFeatures);
    if (open) {
      newOpen.add(featureId);
    } else {
      newOpen.delete(featureId);
    }
    this.openFeatures = newOpen;
  }

  _onFeatureToggled(e) {
    const feature = e.detail.feature;
    const open = e.detail.open;
    this._setOpenFeatures(feature.id, open);
  }

  _onStarToggled(e) {
    const feature = e.detail.feature;
    const starred = e.detail.starred;

    const newStarredFeatures = new Set(this.starredFeatures);
    if (starred) {
      newStarredFeatures.add(feature.id);
    } else {
      newStarredFeatures.delete(feature.id);
    }
    this.starredFeatures = newStarredFeatures;
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
      this,
      args[0],
      this._getSearchStrRegExp(args[1])
    );
  }

  _filterKeyword(regExp, feature) {
    return (
      (
        feature.name +
        '\n' +
        feature.summary +
        '\n' +
        feature.comments +
        '\n' +
        feature.tags
      ).match(regExp) !== null
    );
  }

  _getKeywordFilter(keyword) {
    return this._filterKeyword.bind(this, this._getSearchStrRegExp(keyword));
  }

  // Directly called from template/features.html
  filter(val, shouldPushState) {
    this.searchEl.value = val;
    const pushOrReplaceState =
      history &&
      (shouldPushState
        ? history.pushState.bind(history)
        : history.replaceState.bind(history));
    // Clear filter if there's no search or if called directly.
    if (!val) {
      if (pushOrReplaceState) {
        pushOrReplaceState(
          {query: ''},
          document.title,
          location.pathname + location.search
        );
      } else {
        location.hash = '';
      }
      this.filtered = this.features;
    } else {
      val = val.trim();
      if (pushOrReplaceState) {
        pushOrReplaceState(
          {query: val},
          document.title,
          '/features#' + encodeURIComponent(val)
        );
      }

      const blinkComponent = val.match(/^component:\s?(.*)/);
      if (blinkComponent) {
        const componentName = blinkComponent[1].trim();
        this.filtered = this.features.filter(feature =>
          feature.browsers.chrome.blink_components.includes(componentName)
        );
        this._fireEvent('filtered', {count: this.filtered.length});
        return;
      }

      const regExp = /"([^"]*)"/g;
      const start = 0;
      const parts = [];
      let match;
      while ((match = regExp.exec(val)) !== null) {
        if (start - (regExp.lastIndex - match[0].length) > 0) {
          parts.push(val.substring(start, regExp.lastIndex - match[0].length));
        }
        parts.push(match[1]);
      }
      const matchLen = match ? match[0].length : 0;
      if (start - (regExp.lastIndex - matchLen) > 0) {
        parts.push(val.substring(start, regExp.lastIndex - matchLen));
      }

      // Match words separated by whitespace and/or ":" and/or ordered
      // comparison operator.
      const wordRegExp =
        /("([^"]+)"|([^:<>= \f\n\r\t\v\u00a0\u1680\u180e\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+))([:<>= \f\n\r\t\v\u00a0\u1680\u180e\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+)?/g;
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
        const nextPart =
          i < reMatches.length - 1
            ? reMatches[i + 1][2] || reMatches[i + 1][3]
            : null;
        if (sep && sep.trim().match(/^:$/) !== null && nextPart !== null) {
          // Separator is ":", and there exists a right-hand-side.
          // Store property query: "propertyName : propertyValue".
          propertyQueries.push([part, nextPart]);
          i++;
        } else if (
          sep &&
          sep.trim().match(/^(<=|>=|==|<|>|=)$/) !== null &&
          nextPart !== null
        ) {
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
      const filters = propertyQueries
        .map(this._getPropertyFilter.bind(this))
        .concat(operatorQueries.map(this._getOperatorFilter.bind(this)))
        .concat(keywordQueries.map(this._getKeywordFilter.bind(this)));

      // Apply this.filtered = this.features filtered-by filters.
      if (filters.length === 0) {
        this.filtered = this.features;
      } else {
        let results = this.features;
        for (let i = 0; i < filters.length; i++) {
          results = results.filter(filters[i]);
        }
        this.filtered = results;
      }
    }

    this._fireEvent('filtered', {count: this.filtered.length});
  }

  // Directly called from template/features.html
  scrollToId(targetId) {
    if (!targetId) return;

    this._setOpenFeatures(targetId, true);

    const targetEl = this.shadowRoot.querySelector('#id-' + targetId);
    if (targetEl) {
      targetEl.scrollIntoView();
      const heightOfHeader = document
        .querySelector('.main-toolbar')
        .getBoundingClientRect().height;
      window.scrollBy(0, heightOfHeader * -1);
    }
  }

  _initialize() {
    this._featuresUnveilMetric
      .end()
      .log()
      .sendToAnalytics('features', 'unveil');
    this._fireEvent('app-ready');
    this._hasInitialized = true;
  }

  _computeSectionHidden(feature, features, filtered) {
    return filtered.length != features.length || !feature.first_of_section;
  }

  render() {
    // TODO: Avoid computing values in render().
    let filteredWithState = this.filtered.map(feature => {
      const editable =
        this.isSiteEditor ||
        (this.editableFeatures && this.editableFeatures.includes(feature.id));
      return {
        feature: feature,
        open: this.openFeatures.has(feature.id),
        starred: this.starredFeatures.has(feature.id),
        canEditFeature: editable,
      };
    });
    let numOverLimit = 0;
    if (filteredWithState.length > MAX_FEATURES_SHOWN) {
      numOverLimit = filteredWithState.length - MAX_FEATURES_SHOWN;
      filteredWithState = filteredWithState.slice(0, MAX_FEATURES_SHOWN);
    }
    return html`
      ${filteredWithState.map(
        item => html`
          <div class="item">
            <div
              ?hidden="${this._computeSectionHidden(
                item.feature,
                this.features,
                this.filtered
              )}"
              class="section-marker"
            >
              ${item.feature.browsers.chrome.status.text}
            </div>
            <chromedash-feature
              id="id-${item.feature.id}"
              tabindex="0"
              ?open="${item.open}"
              ?starred="${item.starred}"
              @feature-toggled="${this._onFeatureToggledBound}"
              @star-toggled="${this._onStarToggledBound}"
              .feature="${item.feature}"
              ?canEdit="${item.canEditFeature}"
              ?signedIn="${this.signedInUser != ''}"
            ></chromedash-feature>
          </div>
        `
      )}
      ${numOverLimit > 0
        ? html`<p>
            To see ${numOverLimit} earlier features, please enter a more
            specific query.
          </p>`
        : ''}
    `;
  }
}

customElements.define('chromedash-featurelist', ChromedashFeaturelist);
