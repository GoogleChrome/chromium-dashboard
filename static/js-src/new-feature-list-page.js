const newFeaturesEl = document.querySelector('chromedash-new-feature-list');

window.csClient.getStars().then((starredFeatureIds) => {
  newFeaturesEl.starredFeatures = new Set(starredFeatureIds);
});

document.body.classList.remove('loading');
