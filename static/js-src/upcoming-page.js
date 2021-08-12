// Start fetching right away.
const channelsArray = ['stable', 'beta', 'dev'];

const channelsPromise = window.csClient.getChannels();

let jumpSlideWidth = 0;
let cardsToFetchInAdvance;


document.querySelector('.show-blink-checkbox').addEventListener('change', e => {
  e.stopPropagation();
  document.querySelector('chromedash-upcoming').showShippingType = e.target.checked;
});

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
    channels[channel].features = upcomingEl.mapFeaturesToShippingType(features[channel]);
  });


  upcomingEl.channels = channels;
  upcomingEl.lastFetchedOn = channels[channelsArray[1]].version;
  let cardsDisplayed = upcomingEl.computeItems();
  upcomingEl.lastMilestoneVisible = channels[channelsArray[cardsDisplayed-1]].version;
  cardsToFetchInAdvance = upcomingEl.cardsToFetchInAdvance;

  window.csClient.getStars().then((starredFeatureIds) => {
    upcomingEl.starredFeatures = new Set(starredFeatureIds);
  });
}

// Slide to newer or older version
function move(e) {
  let container = document.querySelector('chromedash-upcoming');
  let divWidth = container.shadowRoot.querySelector('chromedash-upcoming-milestone-card').cardWidth;
  let margin = 8;
  let change = divWidth+margin*2;

  if (container.lastFetchedOn) {
    if (e.target.id == 'next-button') {
      jumpSlideWidth -= change; // move to newer version
      container.style.marginLeft = jumpSlideWidth + 'px';
      container.lastMilestoneVisible += 1;
    } else {
      if (jumpSlideWidth < 0) {
        jumpSlideWidth += change; // move to older version
        container.style.marginLeft = jumpSlideWidth + 'px';
        container.lastMilestoneVisible -= 1;
      }
    }

    // Fetch when second last card is displayed
    if (container.lastMilestoneVisible - container.lastFetchedOn == cardsToFetchInAdvance) {
      container.lastFetchedOn += cardsToFetchInAdvance;
    }
  }
}

// event listeners for timeline control
document.getElementById('previous-button').addEventListener('click', move);
document.getElementById('next-button').addEventListener('click', move);

init();
