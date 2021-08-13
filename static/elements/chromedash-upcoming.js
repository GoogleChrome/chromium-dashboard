import {LitElement, html} from 'lit-element';
import '@polymer/iron-icon';
import style from '../css/elements/chromedash-upcoming.css';

const TEMPLATE_CONTENT = {
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
const CARDS_TO_FETCH_IN_ADVANCE = 3;

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
      lastFetchedOn: {type: Number}, // milestone number rendering of which caused fetching of next milestones
      lastMilestoneVisible: {type: Number}, // milestone number visible on screen to the user
      milestoneArray: {type: Array}, // array to store the milestone numbers fetched after dev channel
      milestoneInfo: {type: Object}, // object to store milestone details (features version etc.) fetched after dev channel
      cardsToFetchInAdvance: {type: Number}, // number of milestones to fetch in advance
    };
  }

  set lastFetchedOn(val) {
    let oldVal = this._lastFetchedOn;
    this._lastFetchedOn = val;
    this.fetchNextBatch().then(()=>{
      this.requestUpdate('lastFetchedOn', oldVal);
    }).catch(() => {
      alert('Some error occurred. Please refresh the page or try again later.');
    });
  }

  get lastFetchedOn() {
    return this._lastFetchedOn;
  }

  constructor() {
    super();
    this.cardWidth = this.computeWidthOfCard();
    this.starredFeatures = new Set();
    this.milestoneArray = [];
    this.milestoneInfo = {};
    this.cardsToFetchInAdvance = CARDS_TO_FETCH_IN_ADVANCE;
  }

  async fetchNextBatch() {
    // promise to fetch next milestones
    const nextMilestones = window.csClient.getSpecifiedChannels(this._lastFetchedOn+1+1,
      this._lastFetchedOn+1+this.cardsToFetchInAdvance);

    let milestoneNumsArray = [];
    for (let i = 1; i <= this.cardsToFetchInAdvance; i++) {
      milestoneNumsArray.push(this._lastFetchedOn+1+i);
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
    this.milestoneArray = [...this.milestoneArray, ...milestoneNumsArray];
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
          ?signedin=${this.signedIn}
          ?showShippingType=${this.showShippingType}
          @star-toggle-event=${this.handleStarToggle}
        >
        </chromedash-upcoming-milestone-card>        
      `)}

      ${this.milestoneArray.map((milestone) => html`
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
          ?signedin=${this.signedIn}
          ?showShippingType=${this.showShippingType}
          @star-toggle-event=${this.handleStarToggle}
        >
        </chromedash-upcoming-milestone-card>        
      `)}
    `;
  }
}

customElements.define('chromedash-upcoming', ChromedashUpcoming);
