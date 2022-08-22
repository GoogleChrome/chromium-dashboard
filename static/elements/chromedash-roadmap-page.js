import {LitElement, css, html} from 'lit';
import {ref, createRef} from 'lit/directives/ref.js';
import './chromedash-roadmap';
import {showToastMessage} from './utils';
import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashRoadmapPage extends LitElement {
  sectionRef = createRef();
  roadmapRef = createRef();

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .animate {
          transition: margin .4s ease;
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
      numColumns: {type: Number},
      viewOffset: {type: Number},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.cardWidth = 0;
    this.numColumns = 0;
    this.viewOffset = 0;
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
    window.csClient.getPermissions().then((user) => {
      this.user = user;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  handleResize() {
    const containerWidth = this.sectionRef.value.offsetWidth;
    const margin = 16;

    let numColumns = 3;
    if (window.matchMedia('(max-width: 768px)').matches) {
      numColumns = 1;
    } else if (window.matchMedia('(max-width: 1152px)').matches) {
      numColumns = 2;
    }
    this.numColumns = numColumns;
    this.cardWidth = (containerWidth/numColumns) - margin;

    this.updateRoadmapMargin(false);
  };

  handleMove(e) {
    const roadmap = this.roadmapRef.value;
    if (!roadmap.lastFutureFetchedOn) return;

    if (e.target.id == 'next-button') {
      this.viewOffset -= 1; // move to newer version
      roadmap.lastMilestoneVisible += 1;
      this.updateRoadmapMargin(true);
    } else {
      this.viewOffset += 1; // move to older version
      roadmap.lastMilestoneVisible -= 1;
      this.updateRoadmapMargin(true);
    }

    // Fetch when second last card is displayed
    if (roadmap.lastMilestoneVisible - roadmap.lastFutureFetchedOn > 1) {
      roadmap.fetchNextBatch(roadmap.lastFutureFetchedOn + 1);
    } else if (roadmap.lastMilestoneVisible - roadmap.lastPastFetchedOn <= 0) {
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
    roadmap.style.marginLeft = this.viewOffset*(this.cardWidth + margin) + 'px';
    roadmap.style.left = roadmap.cardOffset*(this.cardWidth + margin) + 'px';
  }


  render() {
    return html`
      <div id="subheader">
        <div>
          <h3>Roadmap</h3>
        </div>
      </div>
      <section id="releases-section" ${ref(this.sectionRef)}>
        <div class="timeline-controls">
          <button id="previous-button" aria-label="Button to move to previous release" @click=${this.handleMove}>Previous</button>
          <button id="next-button" aria-label="Button to move to later release" @click=${this.handleMove}>Next</button>
        </div>
        <chromedash-roadmap
          ${ref(this.roadmapRef)}
          class="animate"
          aria-label="List of milestone releases"
          .numColumns=${this.numColumns}
          .cardWidth=${this.cardWidth}
          ?signedIn=${Boolean(this.user)}>
        </chromedash-roadmap>
      </section>
    `;
  }
}

customElements.define('chromedash-roadmap-page', ChromedashRoadmapPage);
