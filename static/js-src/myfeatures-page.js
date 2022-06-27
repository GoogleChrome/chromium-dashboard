const myFeaturesEl = document.querySelector('chromedash-myfeatures-page');

window.csClient.getStars().then((starredFeatureIds) => {
  myFeaturesEl.starredFeatures = new Set(starredFeatureIds);
});

document.body.classList.remove('loading');
