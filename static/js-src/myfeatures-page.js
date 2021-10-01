const myFeaturesEl = document.querySelector('chromedash-myfeatures');

window.csClient.getStars().then((starredFeatureIds) => {
  myFeaturesEl.starredFeatures = new Set(starredFeatureIds);
});

document.body.classList.remove('loading');
