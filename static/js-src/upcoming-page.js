// Start fetching right away.
const channelsArray = ['stable', 'beta', 'dev', 'dev_plus_one'];

const channelsPromise = window.csClient.getChannels();


document.querySelector('.show-blink-checkbox').addEventListener('change', e => {
  e.stopPropagation();
  document.querySelector('chromedash-upcoming').showShippingType = e.target.checked;
});

const header = document.querySelector('app-header-layout app-header');
if (header) {
  header.fixed = false;
}

async function init() {
  // Prepare data for chromedash-upcoming
  const channels = await channelsPromise;
  let featuresPromise = {};

  channelsArray.forEach((channel) => {
    featuresPromise[channel] = window.csClient.getFeaturesInMilestone(channels[channel].version);
  });

  const features = {};

  for (let channel of channelsArray) {
    features[channel] = await featuresPromise[channel];
  }

  // Remove the loading sign once the data has been fetched from the APIs
  document.body.classList.remove('loading');

  channelsArray.forEach((channel) => {
    channels[channel].components = mapFeaturesToShippingType(features[channel]);
  });

  const upcomingEl = document.querySelector('chromedash-upcoming');
  upcomingEl.channels = channels;

  window.csClient.getStars().then((starredFeatureIds) => {
    upcomingEl.starredFeatures = new Set(starredFeatureIds);
  });
}

function mapFeaturesToShippingType(features) {
  const featuresMappedToShippingType = {};
  features.forEach(f => {
    const component = f.browsers.chrome.status.text;
    if (!featuresMappedToShippingType[component]) {
      featuresMappedToShippingType[component] = [];
    }
    featuresMappedToShippingType[component].push(f);
  });

  for (let [, feautreList] of Object.entries(featuresMappedToShippingType)) {
    sortFeaturesByName(feautreList);
  }

  return featuresMappedToShippingType;
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
