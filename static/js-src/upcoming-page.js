// Start fetching right away.
const channelsArray = ['stable', 'beta', 'dev', 'dev_plus_one'];

const channelsPromise = window.csClient.getChannels();
let jumpSlideWidth = 0;


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
  upcomingEl.lastMilestoneFetched = channels[channelsArray[2]].version;

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

// Slide to newer or older version
function move(e) {
  let container = document.querySelector('chromedash-upcoming');
  let divWidth = container.shadowRoot.querySelector('chromedash-upcoming-milestone-card').cardWidth;
  let margin = 8;
  let change = divWidth+margin*2;

  if (e.target.id=='next-button') {
    jumpSlideWidth-= change; // move to newer version
    container.style.marginLeft=jumpSlideWidth + 'px';
  } else {
    jumpSlideWidth+=change; // move to older version
    container.style.marginLeft=jumpSlideWidth + 'px';
  }
}

// event listeners for timeline control
document.getElementById('previous-button').addEventListener('click', move);
document.getElementById('next-button').addEventListener('click', move);

init();
