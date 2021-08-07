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
      cardWidth: {type: Number},
      lastMilestoneFetched: {type: Number},
    };
  }

  set lastMilestoneFetched(val) {
    let oldVal = this._lastMilestoneFetched;
    this._lastMilestoneFetched = val;
    this.fetchNextBatch();
    this.requestUpdate('prop', oldVal);
  }

  constructor() {
    super();
    this.cardWidth = this.computeWidthofCard();
    this.starredFeatures = new Set();
  }

  async fetchNextBatch() {
    const nextMilestones = window.csClient.getSpecifiedChannels(this._lastMilestoneFetched+1,
      this._lastMilestoneFetched+3);
    let milestoneArray = [this._lastMilestoneFetched+1,
      this._lastMilestoneFetched+2, this._lastMilestoneFetched+3];
    let milestoneFeaturePromise = {};

    milestoneArray.forEach((milestone) => {
      milestoneFeaturePromise[milestone] = window.csClient.getFeaturesInMilestone(milestone);
    });

    const milestoneFeatures = {};
    let milestoneInfo = await nextMilestones;
    for (let milestone of milestoneArray) {
      milestoneFeatures[milestone] = await milestoneFeaturePromise[milestone];
    }

    milestoneArray.forEach((milestone) => {
      milestoneInfo[milestone].version = milestone;
      milestoneInfo[milestone].components =
          this.mapFeaturesToShippingType(milestoneFeatures[milestone]);

      let node = document.createElement('chromedash-upcoming-milestone-card');
      node.channel = milestoneInfo[milestone];
      node.templateContent=TEMPLATE_CONTENT['dev_plus_one'];
      SHOW_DATES ? node.setAttribute('showdates', 'showdates') : '';
      node.removedStatus=REMOVED_STATUS;
      node.deprecatedStatus=DEPRECATED_STATUS;
      node.starredFeatures=this.starredFeatures;
      node.cardWidth=this.cardWidth;
      this.signedIn ? node.setAttribute('signedin', 'signedin') : '';
      this.showShippingType ? node.setAttribute('showShippingType', 'showShippingType'): '';
      node.addEventListener('star-toggle-event', this.handleStarToggle);
      document.querySelector('chromedash-upcoming').shadowRoot.appendChild(node);
    });
  }

  mapFeaturesToShippingType(features) {
    const featuresMappedToShippingType = {};
    features.forEach(f => {
      const component = f.browsers.chrome.status.text;
      if (!featuresMappedToShippingType[component]) {
        featuresMappedToShippingType[component] = [];
      }
      featuresMappedToShippingType[component].push(f);
    });

    for (let [, feautreList] of Object.entries(featuresMappedToShippingType)) {
      this.sortFeaturesByName(feautreList);
    }

    return featuresMappedToShippingType;
  }


  sortFeaturesByName(features) {
    features.sort((a, b) => {
      a = a.name.toLowerCase();
      b = b.name.toLowerCase();
      if (a < b) {
        return -1;
      }
      if (a > b) {
        return 1;
      }
      return 0;
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
        alert('Unable to star the Feature. Please Try Again.');
      });
  }

  computeWidthofCard() {
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
      ${['stable', 'beta', 'dev', 'dev_plus_one'].map((type) => html`
        <chromedash-upcoming-milestone-card
          .channel=${this.channels[type]}
          .templateContent=${TEMPLATE_CONTENT[type]}
          ?showdates=${SHOW_DATES}
          .removedStatus=${REMOVED_STATUS}
          .deprecatedStatus=${DEPRECATED_STATUS}
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
