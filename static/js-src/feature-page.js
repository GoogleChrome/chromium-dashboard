// Event handler. Used in feature.html template.
const subscribeToFeature = (featureId) => { // eslint-disable-line no-unused-vars
  const iconEl = document.querySelector('.pushicon');
  if (iconEl.icon === 'chromestatus:notifications') {
    iconEl.icon = 'chromestatus:notifications-off';
    PushNotifications.unsubscribeFromFeature(featureId);
  } else {
    iconEl.icon = 'chromestatus:notifications';
    PushNotifications.subscribeToFeature(featureId);
  }
};

// Event handler. Used in feature.html template.
const shareFeature = () => { // eslint-disable-line no-unused-vars
  if (navigator.share) {
    const url = '/feature/' + FEATURE_ID;
    navigator.share({
      title: FEATURE_NAME,
      text: FEATUER_SUMMARY,
      url: url,
    }).then(() => {
      ga('send', 'social',
        {
          'socialNetwork': 'web',
          'socialAction': 'share',
          'socialTarget': url,
        });
    });
  }
};

// Remove loading spinner at page load.
document.body.classList.remove('loading');

// Unhide "Web Share" feature if browser supports it.
if (navigator.share) {
  Array.from(document.querySelectorAll('.no-web-share')).forEach((el) => {
    el.classList.remove('no-web-share');
  });
}

// Unhide notification features if browser supports it.
if (PushNotifier.SUPPORTS_NOTIFICATIONS) {
  document.querySelector('.push-notifications').removeAttribute('hidden');

  // Lazy load Firebase messaging SDK.
  loadFirebaseSDKLibs().then(() => {
    PushNotifications.init(); // init Firebase messaging.

    // If use already granted the notification permission, update state of the
    // push icon for each feature the user is subscribed to.
    if (PushNotifier.GRANTED_ACCESS) {
      PushNotifications.getAllSubscribedFeatures().then((subscribedFeatures) => {
        const iconEl = document.querySelector('.pushicon');
        if (subscribedFeatures.includes(FEATURE_ID)) {
          iconEl.icon = 'chromestatus:notifications';
        } else {
          iconEl.icon = 'chromestatus:notifications-off';
        }
      });
    }
  });
}

if (SHOW_TOAST) {
  setTimeout(() => {
    const toastEl = document.querySelector('chromedash-toast');
    toastEl.showMessage('Your feature was saved! It may take a few minutes to ' +
                      'show up in the main list.', null, null, -1);
  }, 500);
}
