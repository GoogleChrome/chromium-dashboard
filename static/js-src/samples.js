const KEY_CODE_ESC = 27;

const searchEl = document.querySelector('.search input');
const numSamplesEl = document.querySelector('.num-features');
const categoryMenuEl = document.querySelector('#papermenu');
const samplePanelEl = document.querySelector('chromedash-sample-panel');

// Set search box to URL deep link.
if (location.hash) {
  searchEl.value = decodeURIComponent(location.hash.substr(1));
}

samplePanelEl.addEventListener('update-length', (e) => {
  numSamplesEl.textContent = e.detail.length;
});

// Fire of samples.json XHR right away so data can populate faster.
const url = location.hostname == 'localhost' ?
  'https://www.chromestatus.com/samples.json' : '/samples.json';
fetch(url).then((res) => res.json()).then(function(features) {
  const re = /github.com\/GoogleChrome\/samples\/tree\/gh-pages\/(.*)/i;
  features.forEach((feature) => {
    feature.sample_links = feature.sample_links.map(function(link) {
      return link.replace(re, 'googlechrome.github.io/samples/$1');
    });
  });

  samplePanelEl.features = features;
  samplePanelEl.filtered = features;

  numSamplesEl.textContent = features.length;

  document.body.classList.remove('loading');

  samplePanelEl.filter(searchEl.value);
}).catch((error) => {
  console.error(error);
  throw new Error('Samples XHR failed with status ' + e.message);
});

// Clear input when user clicks the 'x' button.
searchEl.addEventListener('search', () => {
  samplePanelEl.filter(null);
});

searchEl.addEventListener('keyup', (e) => {
  if (!e.target.value && e.keyCode != KEY_CODE_ESC) {
    samplePanelEl.filter(null);
  } else {
    samplePanelEl.filter(e.target.value);
  }
});

categoryMenuEl.addEventListener('transitionend', () => {
  // TODO(yangguang): Look into this. selectedItem doesn't exist
  // samplePanelEl.selectedCategory = this.selectedItem;
  samplePanelEl._onSelectCategory();
});
