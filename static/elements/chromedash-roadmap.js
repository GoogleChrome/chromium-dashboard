import {LitElement, html} from 'lit';
import {showToastMessage} from './utils.js';
import '@polymer/iron-icon';
import {ROADMAP_CSS} from '../sass/elements/chromedash-roadmap-css.js';

const TEMPLATE_CONTENT = {
  stable_minus_one: {
    channelLabel: 'Released',
    h1Class: '',
    downloadUrl: '#',
    downloadTitle: '',
    dateText: 'was',
    featureHeader: 'Features in this release',
  },
  stable: {
    channelLabel: 'Stable',
    h1Class: '',
    downloadUrl: 'https://www.google.com/chrome/',
    downloadTitle: 'Download Chrome Stable',
    dateText: 'was',
    featureHeader: 'Features in this release',
  },
  beta: {
    channelLabel: 'Next up',
    h1Class: 'chrome_version--beta',
    downloadUrl: 'https://www.google.com/chrome/beta/',
    downloadTitle: 'Download Chrome Beta',
    dateText: 'between',
    featureHeader: 'Features planned in this release',
  },
  dev: {
    channelLabel: 'Dev',
    h1Class: 'chrome_version--dev',
    downloadUrl: 'https://www.google.com/chrome/dev',
    downloadTitle: 'Download Chrome Dev',
    dateText: 'coming',
    featureHeader: 'Features planned in this release',
  },
  dev_plus_one: {
    channelLabel: 'Later',
    h1Class: 'chrome_version--dev_plus_one',
    downloadUrl: '#',
    downloadTitle: '',
    dateText: 'coming',
    featureHeader: 'Features planned in this release',
  },
};
const DEFAULT_CHANNEL_TYPES = ['stable', 'beta', 'dev'];
const SHOW_DATES = true;
const compareFeatures = (a, b) => a.name.localeCompare(b.name, 'fr', {ignorePunctuation: true}); // comparator for sorting milestone features

class ChromedashRoadmap extends LitElement {
  static styles = ROADMAP_CSS;

  static get properties() {
    return {
      channels: {attribute: false},
      signedIn: {type: Boolean},
      starredFeatures: {type: Object}, // will contain a set of starred features
      columnNumber: {type: Number},
      cardWidth: {type: Number}, // width of each milestone card
      lastFutureFetchedOn: {type: Number}, // milestone number rendering of which caused fetching of next milestones
      lastPastFetchedOn: {type: Number}, // milestone number rendering of which caused fetching of previous milestones
      lastMilestoneVisible: {type: Number}, // milestone number visible on screen to the user
      futureMilestoneArray: {type: Array}, // array to store the milestone numbers fetched after dev channel
      pastMilestoneArray: {type: Array}, // array to store the milestone numbers fetched before stable channel
      milestoneInfo: {type: Object}, // object to store milestone details (features version etc.) fetched after dev channel
      highlightFeature: {type: Number}, // feature to highlight
      cardOffset: {type: Number}, // left margin value
    };
  }

  constructor() {
    super();
    this.columnNumber = 0;
    this.cardWidth = 0;
    this.starredFeatures = new Set();
    this.futureMilestoneArray = [];
    this.pastMilestoneArray = [];
    this.milestoneInfo = {};
    this.cardOffset = 0;
  }

  connectedCallback() {
    super.connectedCallback();

    Promise.all([
      window.csClient.getChannels(),
      window.csClient.getStars(),
    ]).then(([channels, starredFeatures]) => {
      this.fetchFirstBatch(channels);
      this.starredFeatures = new Set(starredFeatures);
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  fetchFirstBatch(channels) {
    const promises = DEFAULT_CHANNEL_TYPES.map((channelType) =>
      window.csClient.getFeaturesInMilestone(channels[channelType].version),
    );
    Promise.all(promises).then((allRes) => {
      allRes.map((res, idx)=> {
        Object.keys(res).forEach(status => {
          res[status].sort(compareFeatures);
        });
        channels[DEFAULT_CHANNEL_TYPES[idx]].features = res;
      });

      this.channels = channels;
      this.fetchNextBatch(channels[DEFAULT_CHANNEL_TYPES[1]].version, true);
      this.fetchPreviousBatch(channels[DEFAULT_CHANNEL_TYPES[1]].version);
      this.lastMilestoneVisible = channels[DEFAULT_CHANNEL_TYPES[this.columnNumber-1]].version;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    });
  }

  fetchNextBatch(nextVersion, isFetchedFirstTime=false) {
    const fetchInAdvance = 3; // number of milestones to fetch while fetching for the first time
    const fetchStart = isFetchedFirstTime ? nextVersion + 2 : nextVersion + fetchInAdvance + 1;
    const fetchEnd = nextVersion + fetchInAdvance + 1;
    const versions = [...Array(fetchEnd - fetchStart + 1).keys()].map(x => x + fetchStart);

    // Promises to get the info and features of specified milestone versions
    const milestonePromise = window.csClient.getSpecifiedChannels(fetchStart, fetchEnd);
    const featurePromises = versions.map((ver) => window.csClient.getFeaturesInMilestone(ver));

    // Fetch milestones object first
    milestonePromise.then((newMilestonesInfo) => {
      // Then fetch features for each milestone
      Promise.all(featurePromises).then((allRes) => {
        allRes.map((res, idx)=> {
          Object.keys(res).forEach(status => {
            res[status].sort(compareFeatures);
          });
          // attach each milestone's feature response to the milestone object
          const version = versions[idx];
          newMilestonesInfo[version].features = res;
          newMilestonesInfo[version].version = version;

          // update the properties to render the latest milestone cards
          this.milestoneInfo = Object.assign({}, this.milestoneInfo, newMilestonesInfo);
          this.futureMilestoneArray = [...this.futureMilestoneArray, ...versions];
          this.lastFutureFetchedOn = nextVersion;
        });
      });
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  fetchPreviousBatch(version) {
    const versionToFetch = version - 2;
    // Chrome 1 is the first release. Hence, do not fetch if already fetched Chrome 1.
    if (versionToFetch < 2) return;

    // Promises to get the info and features of specified milestone versions
    const milestonePromise = window.csClient.getSpecifiedChannels(versionToFetch, versionToFetch);
    const featurePromise = window.csClient.getFeaturesInMilestone(versionToFetch);

    Promise.all([milestonePromise, featurePromise]).then(([newMilestonesInfo, features])=> {
      // sort the feature lists
      Object.keys(features).forEach(status => {
        features[status].sort(compareFeatures);
      });
      // attach the milestone's feature response to the milestone object
      newMilestonesInfo[versionToFetch].features = features;
      newMilestonesInfo[versionToFetch].version = versionToFetch;

      // update the properties to render the newly fetched milestones
      this.milestoneInfo = Object.assign({}, this.milestoneInfo, newMilestonesInfo);
      this.pastMilestoneArray = [versionToFetch, ...this.pastMilestoneArray];
      this.lastPastFetchedOn = version;

      // add the newly fetched milestone to the starting of the list and adjust the margin
      // without animation so that user does not get disturbed
      const margin = 16;
      this.cardOffset -= 1;
      this.classList.remove('animate');
      this.style.marginLeft = this.cardOffset*(this.cardWidth + margin) + 'px';
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  // Handles the Star-Toggle event fired by any one of the child components
  handleStarToggle(e) {
    const newStarredFeatures = new Set(this.starredFeatures);
    window.csClient.setStar(e.detail.feature, e.detail.doStar)
      .then(() => {
        if (e.detail.doStar) {
          newStarredFeatures.add(e.detail.feature);
        } else {
          newStarredFeatures.delete(e.detail.feature);
        }
        this.starredFeatures = newStarredFeatures;
      })
      .catch(() => {
        showToastMessage('Unable to star the Feature. Please Try Again.');
      });
  }

  handleHighlightEvent(e) {
    this.highlightFeature = e.detail.feature;
  }

  render() {
    if (!this.channels) {
      return html``;
    }

    return html`
      ${this.pastMilestoneArray.map((milestone) => html`
        <chromedash-roadmap-milestone-card
          style="width:${this.cardWidth}px;"
          .channel=${this.milestoneInfo[milestone]}
          .templateContent=${TEMPLATE_CONTENT['stable_minus_one']}
          ?showdates=${SHOW_DATES}
          .starredFeatures=${this.starredFeatures}
          .highlightFeature=${this.highlightFeature}
          ?signedin=${this.signedIn}
          @star-toggle-event=${this.handleStarToggle}
          @highlight-feature-event=${this.handleHighlightEvent}
        >
        </chromedash-roadmap-milestone-card>
      `)}

      ${DEFAULT_CHANNEL_TYPES.map((type) => html`
        <chromedash-roadmap-milestone-card
          style="width:${this.cardWidth}px;"
          .channel=${this.channels[type]}
          .templateContent=${TEMPLATE_CONTENT[type]}
          ?showdates=${SHOW_DATES}
          .starredFeatures=${this.starredFeatures}
          .highlightFeature=${this.highlightFeature}
          ?signedin=${this.signedIn}
          @star-toggle-event=${this.handleStarToggle}
          @highlight-feature-event=${this.handleHighlightEvent}
        >
        </chromedash-roadmap-milestone-card>
      `)}

      ${this.futureMilestoneArray.map((milestone) => html`
        <chromedash-roadmap-milestone-card
          style="width:${this.cardWidth}px;"
          .channel=${this.milestoneInfo[milestone]}
          .templateContent=${TEMPLATE_CONTENT['dev_plus_one']}
          ?showdates=${SHOW_DATES}
          .starredFeatures=${this.starredFeatures}
          .highlightFeature=${this.highlightFeature}
          ?signedin=${this.signedIn}
          @star-toggle-event=${this.handleStarToggle}
          @highlight-feature-event=${this.handleHighlightEvent}
        >
        </chromedash-roadmap-milestone-card>
      `)}
    `;
  }
}

customElements.define('chromedash-roadmap', ChromedashRoadmap);
