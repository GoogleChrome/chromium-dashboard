// Start fetching right away.
const urlFeatures = '/api/v0/features';
const urlChannels = '/api/v0/channels';

const featuresPromise = fetch(urlFeatures)
  .then((res) => res.text())
  .then((res) => JSON.parse(res.substring(5))); // Ignore XSSI prefix

const channelsPromise = fetch(urlChannels)
  .then((res) => res.text())
  .then((res) => JSON.parse(res.substring(5)));

document.querySelector('.show-blink-checkbox').addEventListener('change', e => {
  e.stopPropagation();
  document.querySelector('chromedash-schedule').showBlink = e.target.checked;
});

const header = document.querySelector('app-header-layout app-header');
if (header) {
  header.fixed = false;
}

async function init() {
  document.body.classList.remove('loading');

  // Prepare data for chromedash-schedule
  const features = await featuresPromise;
  const CHANNELS = await channelsPromise;

  ['stable', 'beta', 'dev'].forEach((channel) => {
    CHANNELS[channel].components = mapFeaturesToComponents(features.filter(f =>
      f.browsers.chrome.status.milestone_str === CHANNELS[channel].version));
  });

  const scheduleEl = document.querySelector('chromedash-schedule');
  scheduleEl.channels = CHANNELS;

  window.csClient.getStars().then((starredFeatureIds) => {
    scheduleEl.starredFeatures = new Set(starredFeatureIds);
  });
}

function mapFeaturesToComponents(features) {
  let set = new Set();
  features.forEach(f => set.add(...f.browsers.chrome.blink_components));

  const featuresMappedToComponents = {};
  features.forEach(f => {
    const components = f.browsers.chrome.blink_components;
    components.forEach(component => {
      if (!featuresMappedToComponents[component]) {
        featuresMappedToComponents[component] = [];
      }
      featuresMappedToComponents[component].push(f);
    });
  });

  for (let [, feautreList] of Object.entries(featuresMappedToComponents)) {
    sortFeaturesByName(feautreList);
  }

  return featuresMappedToComponents;
}


/**
 *  @param {!Array<!Object>} features
 */
function sortFeaturesByName(features) {
  features.sort((a, b) => {
    a = a.name.toLowerCase();
    b = b.name.toLowerCase();
    if (a < b) {
      return -1;
    }
    if (a > b) {
      return 1;
    }
    return 0;
  });
}

init();
