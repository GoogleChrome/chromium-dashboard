const featureListEl = document.querySelector('chromedash-featurelist');
const chromeMetadataEl = document.querySelector('chromedash-metadata');
const searchEl = document.querySelector('.search input');
// const overlayEl = document.querySelector('chromedash-legend');
// let overlayLoaded = false;

// Set search box to URL deep link.
if (location.hash) {
  searchEl.value = decodeURIComponent(location.hash.substr(1));
}

chromeMetadataEl.addEventListener('query-changed', (e) => {
  const value = e.detail.version;
  const isMilestone = value.match(/^[0-9]+$/);
  searchEl.value = isMilestone ? 'milestone=' + value :
    'browsers.chrome.status:"' + value + '"';
  featureListEl.filter(searchEl.value);
});

// Clear input when user clicks the 'x' button.
searchEl.addEventListener('search', (e) => {
  if (!e.target.value) {
    featureListEl.filter();
    chromeMetadataEl.selected = null;
  }
});

searchEl.addEventListener('input', (e) => {
  // TODO debounce 200ms here
  featureListEl.filter(e.target.value);
  chromeMetadataEl.selected = null;
});

featureListEl.addEventListener('filtered', (e) => {
  document.querySelector('.num-features').textContent = e.detail.count;
});

featureListEl.addEventListener('has-scroll-list', () => {
  const headerEl = document.querySelector('app-header-layout app-header');
  headerEl.fixed = false;
});

featureListEl.addEventListener('filter-category', (e) => {
  searchEl.value = 'category: ' + e.detail.val;
  featureListEl.filter(searchEl.value);
});

featureListEl.addEventListener('filter-owner', (e) => {
  searchEl.value = 'browsers.chrome.owners: ' + e.detail.val;
  featureListEl.filter(searchEl.value);
});

featureListEl.addEventListener('filter-component', (e) => {
  searchEl.value = 'component: ' + e.detail.val;
  featureListEl.filter(searchEl.value);
});

window.addEventListener('popstate', (e) => {
  if (e.state) {
    featureListEl.scrollToId(e.state.id);
  }
});

featureListEl.addEventListener('app-ready', () => {
  document.body.classList.remove('loading');

  // Want "Caching is complete" toast to be slightly delayed after page load.
  // To do that, wait to register SW until features have loaded.
  registerServiceWorker();

  // Lazy load Firebase messaging SDK after features list visible.
  loadFirebaseSDKLibs().then(() => {
    PushNotifications.init(); // init Firebase messaging.

    // If use already granted the notification permission, update state of the
    // push icon for each feature the user is subscribed to.
    if (PushNotifier.GRANTED_ACCESS) {
      PushNotifications.getAllSubscribedFeatures().then((subscribedFeatures) => {
        const iconEl = document.querySelector('#features-subscribe-button').firstElementChild;
        if (subscribedFeatures.includes(PushNotifier.ALL_FEATURES_TOPIC_ID)) {
          iconEl.icon = 'chromestatus:notifications';
        } else {
          iconEl.icon = 'chromestatus:notifications-off';
        }

        featureListEl.features.forEach((f, i) => {
          if (subscribedFeatures.includes(String(f.id))) {
            f.receivePush = true;
            featureListEl.notifyPath(['features', i, 'receivePush'], true);
            featureListEl.notifyPath(['filtered', i, 'receivePush'], true);
          }
        });
      });
    }
  });
});

if (PushNotifier.SUPPORTS_NOTIFICATIONS) {
  document.querySelector('#features-subscribe-button').addEventListener('click', (e) => {
    e.preventDefault();

    if (window.Notification && Notification.permission === 'denied') {
      alert('Notifications were previously denied. Please reset the browser permission.');
      return;
    }

    PushNotifications.getAllSubscribedFeatures().then(subscribedFeatures => {
      const iconEl = document.querySelector('#features-subscribe-button').firstElementChild;
      if (subscribedFeatures.includes(PushNotifier.ALL_FEATURES_TOPIC_ID)) {
        iconEl.icon = 'chromestatus:notifications-off';
        PushNotifications.unsubscribeFromFeature();
      } else {
        iconEl.icon = 'chromestatus:notifications';
        PushNotifications.subscribeToFeature();
      }
    });
  });
}

// TODO(yangguang): Look into the following code.
// // Handles lazy loading chromedash-legend and settings its properties only once.
// const helpOverlayLoadPromise = (overlay) => {
//   return new Promise((resolve, reject) => {
//     if (overlayLoaded) {
//       return resolve();
//     }

//     const url = '/static/elements/chromedash-legend{% if VULCANIZE %}.vulcanize{% endif %}.html';

//     Polymer.Base.importHref(url, () => {
//       overlayLoaded = true;
//       overlay.views = VIEWS; // set from server. Defined in features.html
//       overlay.hidden = false;
//       resolve();
//     }, (e) => {
//       reject(new Error('Error loading:' + url));
//     }, true);
//   });
// }


// document.querySelector('.legend').addEventListener('click', (e) => {
//   e.preventDefault();

//   helpOverlayLoadPromise(overlayEl).then(() => {
//     overlayEl.toggle();
//   });
// });

// Unhide notification features if browser supports it.
// if (PushNotifier.SUPPORTS_NOTIFICATIONS) {
//   Array.from($All('.no-push-notifications')).forEach(el => {
//     el.classList.remove('no-push-notifications');
//   });
// }
