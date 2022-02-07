// Start fetching right away.
const channelsArray = ['stable', 'beta', 'dev'];

const channelsPromise = window.csClient.getChannels();

const header = document.querySelector('app-header-layout app-header');
if (header) {
  header.fixed = false;
}

async function init() {
  // Prepare data for chromedash-roadmap
  const channels = await channelsPromise;
  const featuresPromise = {};

  channelsArray.forEach((channel) => {
    featuresPromise[channel] = window.csClient.getFeaturesInMilestone(channels[channel].version);
  });

  const features = {};

  for (const channel of channelsArray) {
    features[channel] = await featuresPromise[channel];
  }

  // Remove the loading sign once the data has been fetched from the APIs
  document.body.classList.remove('loading');

  const roadmapEl = document.querySelector('chromedash-roadmap');
  channelsArray.forEach((channel) => {
    channels[channel].features = features[channel];
  });

  roadmapEl.channels = channels;
  roadmapEl.lastFutureFetchedOn = channels[channelsArray[1]].version;
  roadmapEl.lastPastFetchedOn = channels[channelsArray[1]].version;
  const cardsDisplayed = roadmapEl.computeItems();
  roadmapEl.lastMilestoneVisible = channels[channelsArray[cardsDisplayed-1]].version;

  window.csClient.getStars().then((starredFeatureIds) => {
    roadmapEl.starredFeatures = new Set(starredFeatureIds);
  });
}

// Slide to newer or older version
function move(e) {
  const container = document.querySelector('chromedash-roadmap');
  const divWidth = container.shadowRoot
    .querySelector('chromedash-roadmap-milestone-card').cardWidth;
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
