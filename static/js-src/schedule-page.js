// Start fetching right away.
const url = '/features.json';
const featuresPromise = fetch(url).then((res) => res.json());

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
  let columns = ['stable', 'beta', 'dev'];

  let gapMilestone = null;

  // If there is a gap between stable, beta, or dev then display "gap" column.
  if (CHANNELS['beta'].version > CHANNELS['stable'].version + 1) {
    gapMilestone = CHANNELS['stable'].version + 1;
    columns = ['stable', 'gap', 'beta'];
  } else if (CHANNELS['dev'].version > CHANNELS['beta'].version + 1) {
    gapMilestone = CHANNELS['beta'].version + 1;
    columns = ['stable', 'beta', 'gap'];
  }
  if (gapMilestone) {
    try {
      const gapInfo = await window.csClient.getSpecifiedChannels(
        gapMilestone, gapMilestone);
      CHANNELS['gap'] = gapInfo[gapMilestone];
    } catch (err) {
      throw (new Error('Unable to load schedule for ' + gapMilestone));
    }
  }
  console.log(CHANNELS);

  columns.forEach((channel) => {
    CHANNELS[channel].components = mapFeaturesToComponents(features.filter(f =>
      f.browsers.chrome.status.milestone_str === CHANNELS[channel].version));
  });

  const scheduleEl = document.querySelector('chromedash-schedule');
  scheduleEl.channels = CHANNELS;
  scheduleEl.columns = columns;

  window.csClient.getStars().then((starredFeatureIds) => {
    scheduleEl.starredFeatures = new Set(starredFeatureIds);
  });
}

function mapFeaturesToComponents(features) {
  const set = new Set();
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

  for (const [, feautreList] of Object.entries(featuresMappedToComponents)) {
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
