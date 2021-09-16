// Start fetching right away.
const channelsArray = ['stable', 'beta', 'dev'];

const channelsPromise = window.csClient.getChannels();

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

  const upcomingEl = document.querySelector('chromedash-upcoming');
  channelsArray.forEach((channel) => {
    channels[channel].features = features[channel];
  });

  upcomingEl.channels = channels;
  upcomingEl.lastFutureFetchedOn = channels[channelsArray[1]].version;
  upcomingEl.lastPastFetchedOn = channels[channelsArray[1]].version;
  let cardsDisplayed = upcomingEl.computeItems();
  upcomingEl.lastMilestoneVisible = channels[channelsArray[cardsDisplayed-1]].version;

  window.csClient.getStars().then((starredFeatureIds) => {
    upcomingEl.starredFeatures = new Set(starredFeatureIds);
  });
}

// Slide to newer or older version
function move(e) {
  const container = document.querySelector('chromedash-upcoming');
  const divWidth = container.shadowRoot
    .querySelector('chromedash-upcoming-milestone-card').cardWidth;
  const margin = 8;
  const change = divWidth + margin * 2;
  container.classList.add('animate');

  if (container.lastFutureFetchedOn) {
    if (e.target.id == 'next-button') {
      container.jumpSlideWidth -= change; // move to newer version
      container.style.marginLeft = container.jumpSlideWidth + 'px';
      container.lastMilestoneVisible += 1;
    } else {
      if (container.jumpSlideWidth < 0) {
        container.jumpSlideWidth += change; // move to older version
        container.style.marginLeft = container.jumpSlideWidth + 'px';
        container.lastMilestoneVisible -= 1;
      }
    }

    // Fetch when second last card is displayed
    if (container.lastMilestoneVisible - container.lastFutureFetchedOn > 1) {
      container.lastFutureFetchedOn += 1;
    }

    if (container.lastPastFetchedOn - container.lastMilestoneVisible == 0) {
      container.lastPastFetchedOn -= 1;
    }
  }
}

// event listeners for timeline control
document.getElementById('previous-button').addEventListener('click', move);
document.getElementById('next-button').addEventListener('click', move);

init();
