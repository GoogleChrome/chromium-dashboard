const featureListEl = document.querySelector('chromedash-featurelist');
const chromeMetadataEl = document.querySelector('chromedash-metadata');
const searchEl = document.querySelector('.search input');
const legendEl = document.querySelector('chromedash-legend');

/**
 * Simple debouncer to handle text input.  Don't try to hit the server
 * until the user has stopped typing for a few seconds.  E.g.,
 * var debouncedKeyHandler = debounce(keyHandler);
 * el.addEventListener('keyup', debouncedKeyHandler);
 * @param {function} func Function to call after a delay.
 * @param {number} threshold_ms Milliseconds to wait before calling.
 * @return {function} A new function that can be used as an event handler.
 */
function debounce(func, threshold_ms = 300) {
  let timeout;
  return function(...args) {
    let context = this; // eslint-disable-line no-invalid-this
    let later = () => {
      func.apply(context, args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, threshold_ms);
  };
}

// Set search box to URL deep link.
if (location.hash) {
  searchEl.value = decodeURIComponent(location.hash.substr(1));
}

chromeMetadataEl.addEventListener('query-changed', (e) => {
  const value = e.detail.version;
  const isMilestone = value.match(/^[0-9]+$/);
  searchEl.value = isMilestone ? 'milestone=' + value :
    'browsers.chrome.status:"' + value + '"';
  featureListEl.filter(searchEl.value, true);
});

// Clear input when user clicks the 'x' button.
searchEl.addEventListener('search', (e) => {
  if (!e.target.value) {
    featureListEl.filter('', true);
    chromeMetadataEl.selected = null;
  }
});

searchEl.addEventListener('input', debounce((e) => {
  featureListEl.filter(e.target.value);
  chromeMetadataEl.selected = null;
}));

featureListEl.addEventListener('filtered', (e) => {
  document.querySelector('.num-features').textContent = e.detail.count;
});

featureListEl.addEventListener('has-scroll-list', () => {
  const headerEl = document.querySelector('app-header-layout app-header');
  headerEl.fixed = false;
});

featureListEl.addEventListener('filter-category', (e) => {
  e.stopPropagation();
  searchEl.value = 'category: ' + e.detail.val;
  featureListEl.filter(searchEl.value, true);
});

featureListEl.addEventListener('filter-owner', (e) => {
  e.stopPropagation();
  searchEl.value = 'browsers.chrome.owners: ' + e.detail.val;
  featureListEl.filter(searchEl.value, true);
});

featureListEl.addEventListener('filter-component', (e) => {
  e.stopPropagation();
  searchEl.value = 'component: ' + e.detail.val;
  featureListEl.filter(searchEl.value, true);
});

window.addEventListener('popstate', (e) => {
  if (e.state && e.state.id) {
    featureListEl.scrollToId(e.state.id);
  } else if (e.state && e.state.query) {
    featureListEl.filter(e.state.query);
  }
});

featureListEl.addEventListener('app-ready', () => {
  document.body.classList.remove('loading');

  StarService.getStars().then((starredFeatureIds) => {
    featureListEl.starredFeatures = new Set(starredFeatureIds);
  });
});

legendEl.views = VIEWS;

document.querySelector('.legend-button').addEventListener('click', (e) => {
  e.preventDefault();
  legendEl.toggle();
});
