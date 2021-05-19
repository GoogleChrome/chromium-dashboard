(function(exports) {
// Event handler. Used in feature.html template.
const subscribeToFeature = (featureId) => {
  const iconEl = document.querySelector('.pushicon');
  if (iconEl.icon === 'chromestatus:star') {
    window.csClient.setStar(featureId, false).then(() => {
      iconEl.icon = 'chromestatus:star-border';
    });
  } else {
    window.csClient.setStar(featureId, true).then(() => {
      iconEl.icon = 'chromestatus:star';
    });
  }
};

// Event handler. Used in feature.html template.
const shareFeature = () => {
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

// Show the star icon if the user has starred this feature.
window.csClient.getStars().then((subscribedFeatures) => {
  const iconEl = document.querySelector('.pushicon');
  if (subscribedFeatures.includes(Number(FEATURE_ID))) {
    iconEl.icon = 'chromestatus:star';
  } else {
    iconEl.icon = 'chromestatus:star-border';
  }
});

const starWhenSignedOutEl = document.querySelector('#star-when-signed-out');
if (starWhenSignedOutEl) {
  starWhenSignedOutEl.addEventListener('click', function(e) {
    window.promptSignIn(e);
  });
}

if (SHOW_TOAST) {
  setTimeout(() => {
    const toastEl = document.querySelector('chromedash-toast');
    toastEl.showMessage('Your feature was saved! It may take a few minutes to ' +
                      'show up in the main list.', null, null, -1);
  }, 500);
}

// Open an accordion that was bookmarked open
if (location.hash) {
  const targetId = decodeURIComponent(location.hash.substr(1));
  const targetEl = document.getElementById(targetId);
  if (targetEl && targetEl.tagName == 'CHROMEDASH-ACCORDION') {
    targetEl.opened = true;
  }
}


exports.subscribeToFeature = subscribeToFeature;
exports.shareFeature = shareFeature;
})(window);
