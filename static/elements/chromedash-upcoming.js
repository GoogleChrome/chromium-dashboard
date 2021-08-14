import {LitElement, html} from 'lit-element';
import '@polymer/iron-icon';
import style from '../css/elements/chromedash-upcoming.css';

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
const REMOVED_STATUS = ['Removed'];
const DEPRECATED_STATUS = ['Deprecated', 'No longer pursuing'];
const ORIGIN_TRIAL = ['Origin trial'];
const BROWSER_INTERVENTION = ['Browser Intervention'];
const SHOW_DATES = true;

class ChromedashUpcoming extends LitElement {
  static styles = style;

  static get properties() {
    return {
      // Assigned in upcoming-page.js,
      channels: {attribute: false},
      showShippingType: {attribute: false},
      signedIn: {type: Boolean},
      loginUrl: {type: String},
      starredFeatures: {type: Object}, // will contain a set of starred features
      cardWidth: {type: Number}, // width of each milestone card
      lastFutureFetchedOn: {type: Number}, // milestone number rendering of which caused fetching of next milestones
      lastPastFetchedOn: {type: Number}, // milestone number rendering of which caused fetching of previous milestones
      lastMilestoneVisible: {type: Number}, // milestone number visible on screen to the user
      futureMilestoneArray: {type: Array}, // array to store the milestone numbers fetched after dev channel
      pastMilestoneArray: {type: Array}, // array to store the milestone numbers fetched before stable channel
      milestoneInfo: {type: Object}, // object to store milestone details (features version etc.) fetched after dev channel
      highlightFeature: {type: Number}, // feature to highlight
      jumpSlideWidth: {type: Number}, // left margin value
      isChromeOneFetched: {type: Boolean}, // is the first release of Chrome fetched
    };
  }

  set lastFutureFetchedOn(val) {
    let oldVal = this._lastFutureFetchedOn;
    this._lastFutureFetchedOn = val;
    this.fetchNextBatch().then(()=>{
      this.requestUpdate('lastFutureFetchedOn', oldVal);
    }).catch(() => {
      alert('Some error occurred. Please refresh the page or try again later.');
    });
  }

  set lastPastFetchedOn(val) {
    let oldVal = this._lastPastFetchedOn;
    this._lastPastFetchedOn = val;
    if (!this.isChromeOneFetched) {
      this.fetchPreviousBatch().then(()=>{
        this.requestUpdate('lastPastFetchedOn', oldVal);
      }).catch(() => {
        alert('Some error occurred. Please refresh the page or try again later.');
      });
    }
  }

  get lastFutureFetchedOn() {
    return this._lastFutureFetchedOn;
  }

  get lastPastFetchedOn() {
    return this._lastPastFetchedOn;
  }

  constructor() {
    super();
    this.cardWidth = this.computeWidthOfCard();
    this.starredFeatures = new Set();
    this.futureMilestoneArray = [];
    this.pastMilestoneArray = [];
    this.milestoneInfo = {};
    this.jumpSlideWidth = 0;
  }

  async fetchNextBatch() {
    const isFetchedFirstTime = this._lastFutureFetchedOn == this.channels['beta'].version;

    let nextMilestones;
    let milestoneNumsArray = [];
    const cardsToFetchInAdvance = 3; // number of milestones to fetch while fetching for the first time

    // promise to fetch next milestones
    // if fetching first time, fetch next cardsToFetchInAdvance milestones, else fetch only the next milestone.
    if (isFetchedFirstTime) {
      nextMilestones = window.csClient.getSpecifiedChannels(this._lastFutureFetchedOn+1+1,
        this._lastFutureFetchedOn+1+cardsToFetchInAdvance);
      for (let i = 1; i <= cardsToFetchInAdvance; i++) {
        milestoneNumsArray.push(this._lastFutureFetchedOn+1+i);
      }
    } else {
      nextMilestones = window.csClient.
        getSpecifiedChannels(this._lastFutureFetchedOn+cardsToFetchInAdvance+1,
          this._lastFutureFetchedOn+cardsToFetchInAdvance+1);
      milestoneNumsArray.push(this._lastFutureFetchedOn+cardsToFetchInAdvance+1);
    }

    // promise to fetch features in next milestones
    let milestoneFeaturePromise = {};
    milestoneNumsArray.forEach((milestoneNum) => {
      milestoneFeaturePromise[milestoneNum] = window.csClient.getFeaturesInMilestone(milestoneNum);
    });

    let newMilestonesInfo;
    let milestoneFeatures = {};

    try {
      newMilestonesInfo = await nextMilestones;
      for (let milestoneNum of milestoneNumsArray) {
        milestoneFeatures[milestoneNum] = await milestoneFeaturePromise[milestoneNum];
      }
    } catch (err) {
      throw (new Error('Unable to load Features'));
    }

    // add some details to milestone information fetched
    milestoneNumsArray.forEach((milestoneNum) => {
      newMilestonesInfo[milestoneNum].version = milestoneNum;
      newMilestonesInfo[milestoneNum].features = milestoneFeatures[milestoneNum];
    });

    // update the properties to render the latest milestone cards
    this.milestoneInfo = Object.assign({}, this.milestoneInfo, newMilestonesInfo);
    this.futureMilestoneArray = [...this.futureMilestoneArray, ...milestoneNumsArray];
  }

  // Fetch 1 earlier released milestone
  async fetchPreviousBatch() {
    // Chrome 1 is the first release. Hence, do not fetch if already fetched Chrome 1.
    if (this._lastPastFetchedOn - 2 < 2) {
      this.isChromeOneFetched = true;
    }

    let nextMilestones = window.csClient.getSpecifiedChannels(this._lastPastFetchedOn - 2,
      this._lastPastFetchedOn - 2);

    let milestoneNumsArray = [];
    milestoneNumsArray.push(this._lastPastFetchedOn - 2);

    // promise to fetch features in the earlier released milestone
    let milestoneFeaturePromise = {};
    milestoneNumsArray.forEach((milestoneNum) => {
      milestoneFeaturePromise[milestoneNum] = window.csClient.getFeaturesInMilestone(milestoneNum);
    });

    let newMilestonesInfo;
    let milestoneFeatures = {};

    try {
      newMilestonesInfo = await nextMilestones;
      for (let milestoneNum of milestoneNumsArray) {
        milestoneFeatures[milestoneNum] = await milestoneFeaturePromise[milestoneNum];
      }
    } catch (err) {
      throw (new Error('Unable to load Features'));
    }

    // add some details to milestone information fetched
    milestoneNumsArray.forEach((milestoneNum) => {
      newMilestonesInfo[milestoneNum].version = milestoneNum;
      newMilestonesInfo[milestoneNum].features = milestoneFeatures[milestoneNum];
    });

    // update the properties to render the newly fetched milestones
    this.milestoneInfo = Object.assign({}, this.milestoneInfo, newMilestonesInfo);
    this.pastMilestoneArray = [...milestoneNumsArray, ...this.pastMilestoneArray];

    // add the newly fetched milestone to the starting of the list and adjust the margin
    // without animation so that user does not get disturbed
    const container = document.querySelector('chromedash-upcoming');
    const divWidth = container.cardWidth;
    const margin = 8;
    const change = divWidth + margin * 2;
    this.jumpSlideWidth -= change;
    container.classList.remove('animate');
    container.style.marginLeft = this.jumpSlideWidth + 'px';
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
        alert('Unable to star the Feature. Please Try Again.');
      });
  }

  handleHighlightEvent(e) {
    this.highlightFeature = e.detail.feature;
  }

  computeWidthOfCard() {
    let cardContainer = document.querySelector('#releases-section');
    let containerWidth = cardContainer.offsetWidth;
    let items = this.computeItems();
    let margin=16;
    let val = (containerWidth/items)-margin;
    return val;
  };

  computeItems() {
    if (window.matchMedia('(max-width: 768px)').matches) {
      return 1;
    } else if (window.matchMedia('(max-width: 992px)').matches) {
      return 2;
    } else {
      return 3;
    }
  }

  render() {
    if (!this.channels) {
      return html``;
    }

    return html`
        ${this.pastMilestoneArray.map((milestone) => html`
        <chromedash-upcoming-milestone-card
          .channel=${this.milestoneInfo[milestone]}
          .templateContent=${TEMPLATE_CONTENT['stable_minus_one']}
          ?showdates=${SHOW_DATES}
          .removedStatus=${REMOVED_STATUS}
          .deprecatedStatus=${DEPRECATED_STATUS}
          .originTrialStatus=${ORIGIN_TRIAL}
          .browserInterventionStatus=${BROWSER_INTERVENTION}
          .starredFeatures=${this.starredFeatures}
          .cardWidth=${this.cardWidth}
          .highlightFeature=${this.highlightFeature}
          ?signedin=${this.signedIn}
          ?showShippingType=${this.showShippingType}
          @star-toggle-event=${this.handleStarToggle}
          @highlight-feature-event=${this.handleHighlightEvent}
        >
        </chromedash-upcoming-milestone-card>        
      `)}

      ${['stable', 'beta', 'dev'].map((type) => html`
        <chromedash-upcoming-milestone-card
          .channel=${this.channels[type]}
          .templateContent=${TEMPLATE_CONTENT[type]}
          ?showdates=${SHOW_DATES}
          .removedStatus=${REMOVED_STATUS}
          .deprecatedStatus=${DEPRECATED_STATUS}
          .originTrialStatus=${ORIGIN_TRIAL}
          .browserInterventionStatus=${BROWSER_INTERVENTION}
          .starredFeatures=${this.starredFeatures}
          .cardWidth=${this.cardWidth}
          .highlightFeature=${this.highlightFeature}
          ?signedin=${this.signedIn}
          ?showShippingType=${this.showShippingType}
          @star-toggle-event=${this.handleStarToggle}
          @highlight-feature-event=${this.handleHighlightEvent}
        >
        </chromedash-upcoming-milestone-card>        
      `)}

      ${this.futureMilestoneArray.map((milestone) => html`
        <chromedash-upcoming-milestone-card
          .channel=${this.milestoneInfo[milestone]}
          .templateContent=${TEMPLATE_CONTENT['dev_plus_one']}
          ?showdates=${SHOW_DATES}
          .removedStatus=${REMOVED_STATUS}
          .deprecatedStatus=${DEPRECATED_STATUS}
          .originTrialStatus=${ORIGIN_TRIAL}
          .browserInterventionStatus=${BROWSER_INTERVENTION}
          .starredFeatures=${this.starredFeatures}
          .cardWidth=${this.cardWidth}
          .highlightFeature=${this.highlightFeature}
          ?signedin=${this.signedIn}
          ?showShippingType=${this.showShippingType}
          @star-toggle-event=${this.handleStarToggle}
          @highlight-feature-event=${this.handleHighlightEvent}
        >
        </chromedash-upcoming-milestone-card>        
      `)}
    `;
  }
}

customElements.define('chromedash-upcoming', ChromedashUpcoming);
