const KEY_CODE_ESC = 27;

const searchEl = document.querySelector('.search input');
const numSamplesEl = document.querySelector('.num-features');
const categoryMenuEl = document.querySelector('#papermenu');
const samplePanelEl = document.querySelector('chromedash-sample-panel');
let previousSelectedCategory = null;

samplePanelEl.categories = CATEGORIES;
samplePanelEl.searchEl = searchEl;
samplePanelEl.categoryMenuEl = categoryMenuEl;

// Set search box to URL deep link.
if (location.hash) {
  searchEl.value = decodeURIComponent(location.hash.substr(1));
}

samplePanelEl.addEventListener('update-length', (e) => {
  // chromedash-sample-panel fires update-length after init.
  document.body.classList.remove('loading');

  numSamplesEl.textContent = e.detail.length;
});

// Clear input when user clicks the 'x' button.
searchEl.addEventListener('search', () => {
  samplePanelEl.filter(null, previousSelectedCategory);
});

searchEl.addEventListener('keyup', (e) => {
  if (!e.target.value && e.keyCode != KEY_CODE_ESC) {
    samplePanelEl.filter(null, previousSelectedCategory);
  } else {
    samplePanelEl.filter(e.target.value, previousSelectedCategory);
  }
});

categoryMenuEl.addEventListener('transitionend', (e) => {
  const selectedCategory = e.currentTarget.selectedItem.textContent.trim();

  // Clicking selected item to de-select
  if (selectedCategory && selectedCategory === previousSelectedCategory) {
    previousSelectedCategory = null;
    categoryMenuEl.selected = null;
    samplePanelEl.filter(searchEl.value.trim());
  } else {
    samplePanelEl.filter(searchEl.value.trim(), selectedCategory);
    previousSelectedCategory = selectedCategory;
  }
});
