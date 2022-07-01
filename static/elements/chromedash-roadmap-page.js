import {LitElement, css, html} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import './chromedash-roadmap';
import {showToastMessage} from './utils';

import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashRoadmapPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .animate {
          transition: margin .4s ease;
        }

        #subheader {
          max-width: 100%;
          justify-content: center;
        }

        #releases-section {
          overflow: hidden;
        }

        .timeline-controls {
          text-align: center;
          padding-bottom: var(--content-padding);
        }
    `];
  }

  static get properties() {
    return {
      user: {type: Object},
      cardWidth: {type: Number},
      columnNumber: {type: Number},
      roadmapRef: {type: Element},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.cardWidth = 0;
    this.columnNumber = 0;
    this.roadmapRef = createRef();
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
    window.addEventListener('resize', () => this.handleResize());
  }

  disconnectedCallback() {
    window.removeEventListener('resize', () => this.handleResize());
    super.disconnectedCallback();
  }

  firstUpdated() {
    this.handleResize();
  }

  fetchData() {
    this.loading = true;
    window.csClient.getPermissions().then((user) => {
      this.user = user;
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  handleResize() {
    const cardContainer = this.shadowRoot.querySelector('#releases-section');
    const containerWidth = cardContainer.offsetWidth;
    const margin = 16;

    let columnNumber = 3;
    if (window.matchMedia('(max-width: 768px)').matches) {
      columnNumber = 1;
    } else if (window.matchMedia('(max-width: 1152px)').matches) {
      columnNumber = 2;
    }
    this.columnNumber = columnNumber;
    this.cardWidth = (containerWidth/columnNumber) - margin;

    this.updateRoadmapMargin(false);
  };

  handleMove(e) {
    const roadmap = this.roadmapRef.value;
    if (!roadmap.lastFutureFetchedOn) return;

    if (e.target.id == 'next-button') {
      roadmap.cardOffset -= 1; // move to newer version
      roadmap.lastMilestoneVisible += 1;
      this.updateRoadmapMargin(true);
    } else if (roadmap.cardOffset < 0) {
      roadmap.cardOffset += 1; // move to older version
      roadmap.lastMilestoneVisible -= 1;
      this.updateRoadmapMargin(true);
    }

    // Fetch when second last card is displayed
    if (roadmap.lastMilestoneVisible - roadmap.lastFutureFetchedOn > 1) {
      roadmap.fetchNextBatch(roadmap.lastFutureFetchedOn + 1);
    }
    if (roadmap.lastPastFetchedOn - roadmap.lastMilestoneVisible == 0) {
      roadmap.fetchPreviousBatch(roadmap.lastPastFetchedOn - 1);
    }
  }

  updateRoadmapMargin(animated) {
    const roadmap = this.roadmapRef.value;
    if (animated) {
      roadmap.classList.add('animate');
    } else {
      roadmap.classList.remove('animate');
    }
    const margin = 16;
    roadmap.style.marginLeft = roadmap.cardOffset*(this.cardWidth + margin) + 'px';
  }


  render() {
    return html`
      <div id="subheader">
        <div style="flex:1">
          <h3>Roadmap</h3>
        </div>
      </div>
      <section id="releases-section">
        <div class="timeline-controls">
          <button id="previous-button" aria-label="Button to move to previous release" @click=${this.handleMove}>Previous</button>
          <button id="next-button" aria-label="Button to move to later release" @click=${this.handleMove}>Next</button>
        </div>
        <chromedash-roadmap
          ${ref(this.roadmapRef)}
          class="animate"
          aria-label="List of milestone releases"
          .columnNumber=${this.columnNumber}
          .cardWidth=${this.cardWidth}
          ?signedIn=${Boolean(this.user)}>
        </chromedash-roadmap>
        <div class="timeline-controls"></div>
      </section>
    `;
  }
}

customElements.define('chromedash-roadmap-page', ChromedashRoadmapPage);
