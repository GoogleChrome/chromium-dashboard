import {LitElement, html} from 'lit-element';
import '@polymer/iron-icon';
import style from '../css/elements/chromedash-upcoming.css';

const TEMPLATE_CONTENT = {
  stable: {
    channelLabel: 'Stable',
    h1Class: '',
    downloadUrl: 'https://www.google.com/chrome/browser/desktop/index.html',
    downloadTitle: 'Download Chrome stable',
    dateText: 'was',
    featureHeader: 'Features in this release',
  },
  beta: {
    channelLabel: 'Next up',
    h1Class: 'chrome_version--beta',
    downloadUrl: 'https://www.google.com/chrome/browser/beta.html',
    downloadTitle: 'Download Chrome Beta',
    dateText: 'between',
    featureHeader: 'Features planned in this release',
  },
  dev: {
    channelLabel: 'Dev',
    h1Class: 'chrome_version--dev',
    downloadUrl: 'https://www.google.com/chrome/browser/canary.html',
    downloadTitle: 'Download Chrome Canary',
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
      showBlink: {attribute: false},
      signedIn: {type: Boolean},
      loginUrl: {type: String},
      starredFeatures: {type: Object}, // will contain a set of starred features
    };
  }

  constructor() {
    super();
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


  render() {
    if (!this.channels) {
      return html``;
    }

    return html`
      ${['stable', 'beta', 'dev'].map((type) => html`
        <chromedash-upcoming-milestone-card
          .channel=${this.channels[type]}
          .templateContent=${TEMPLATE_CONTENT[type]}
          showdates='${SHOW_DATES}'
          .removedStatus='${REMOVED_STATUS}'
          .deprecatedStatus='${DEPRECATED_STATUS}'
          .starredFeatures='${[...this.starredFeatures]}'
          ?signedin=${this.signedIn}
          ?showblink=${this.showBlink}
          @star-toggle-event=${this.handleStarToggle}
        >
        </chromedash-upcoming-milestone-card>        
      `)}
    `;
  }
}

customElements.define('chromedash-upcoming', ChromedashUpcoming);
