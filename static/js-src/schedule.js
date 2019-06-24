// Start fetching right away.
const url = location.hostname == 'localhost' ?
  'https://www.chromestatus.com/features.json' : '/features.json';
const featuresPromise = fetch(url).then((res) => res.json());

document.querySelector('paper-toggle-button').addEventListener('change', e => {
  e.stopPropagation();
  // document.querySelectorAll('.release').forEach(release => {
  //   release.classList.toggle('no-components', e.target.checked);
  // });
});

document.addEventListener('WebComponentsReady', function() {
  const header = document.querySelector('app-header-layout app-header');
  if (header) {
    header.fixed = false;
  }
});

async function init() {
  document.body.classList.remove('loading');

  // Wait for Polymer to be setup before setting features on template.
  // This prevents race conditions whereby when opening a new tab, Chrome
  // returns features from the cache and beats Polymer being ready.
  const target = document.querySelector('#releases-section');
  const mutationObserverPromise = new Promise(resolve => {
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.addedNodes.length && target.querySelector('.releases')) {
          observer.disconnect();
          resolve();
        }
      });
    });
    observer.observe(target, {childList: true});
  });

  const timeoutPromise = new Promise(resolve => setTimeout(resolve, 5000));

  // Race fetching features from network and timeout. If MO observer check fails
  // for some reason, manually set features after 5s.
  await Promise.race([mutationObserverPromise, timeoutPromise]);

  // Prepare data for chromedash-schedule
  const features = await featuresPromise;
  ['stable', 'beta', 'dev'].forEach((channel) => {
    CHANNELS[channel].components = mapFeaturesToComponents(features.filter(f =>
      f.browsers.chrome.status.milestone_str === CHANNELS[channel].version));
  });

  const scheduleEl = document.querySelector('chromedash-schedule');
  scheduleEl.channels = CHANNELS;

  // Show push notification icons if the browser supports the feature.
  if (window.PushNotifier && PushNotifier.SUPPORTS_NOTIFICATIONS) {
    // document.querySelector('.releases').classList.add('supports-push-notifications');
    initNotifications(features);
  }
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

async function initNotifications(allFeatures) {
  await loadFirebaseSDKLibs(); // Lazy load Firebase messaging SDK.

  PushNotifications.init(); // init Firebase messaging.

  // If use already granted the notification permission, update state of the
  // push icon for each feature the user is subscribed to.
  const subscribedFeatures = await PushNotifications.getAllSubscribedFeatures();
  allFeatures.forEach((feature) => {
    if (subscribedFeatures.includes(String(feature.id))) {
      // f.receivePush = true;
      const iconEl = document.querySelector(`[data-feature-id="${feature.id}"] .pushicon`);
      if (iconEl) {
        iconEl.icon = 'chromestatus:notifications';
      }
    }
  });
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
