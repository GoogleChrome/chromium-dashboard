import {LitElement, css, html} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {createRef, ref} from 'lit/directives/ref.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User} from '../js-src/cs-client';
import './chromedash-roadmap';
import {ChromedashRoadmap} from './chromedash-roadmap';

@customElement('chromedash-roadmap-page')
export class ChromedashRoadmapPage extends LitElement {
  sectionRef = createRef<HTMLElement>();
  roadmapRef = createRef<ChromedashRoadmap>();

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .animate {
          transition: margin 0.4s ease;
        }

        #releases-section {
          overflow: hidden;
        }

        .timeline-controls {
          text-align: center;
          padding-bottom: var(--content-padding);
        }
      `,
    ];
  }

  @property({type: Object, attribute: false})
  user!: User;
  @state()
  cardWidth = 0;
  @state()
  numColumns = 0;
  @state()
  viewOffset = 0;

  boundHandleResize = this.handleResize.bind(this);

  connectedCallback() {
    super.connectedCallback();
    window.addEventListener('resize', this.boundHandleResize);
  }

  disconnectedCallback() {
    window.removeEventListener('resize', this.boundHandleResize);
    super.disconnectedCallback();
  }

  firstUpdated() {
    this.handleResize();
  }

  handleResize() {
    const containerWidth = this.sectionRef.value!.offsetWidth;
    const margin = 16;

    let numColumns = 3;
    if (containerWidth < 768) {
      numColumns = 1;
    } else if (containerWidth < 1152) {
      numColumns = 2;
    }
    this.numColumns = numColumns;
    if (containerWidth) {
      this.cardWidth = containerWidth / numColumns - margin;
    }

    this.updateRoadmapMargin(false);
  }

  handleMove(e) {
    const roadmap = this.roadmapRef.value;
    if (!roadmap?.lastFutureFetchedOn) return;

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
    if (!roadmap) return;
    if (animated) {
      roadmap.classList.add('animate');
    } else {
      roadmap.classList.remove('animate');
    }
    const margin = 16;
    roadmap.style.marginLeft =
      this.viewOffset * (this.cardWidth + margin) + 'px';
    roadmap.style.left = roadmap.cardOffset * (this.cardWidth + margin) + 'px';
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
          <button
            id="previous-button"
            aria-label="Button to move to previous release"
            @click=${this.handleMove}
          >
            Previous
          </button>
          <button
            id="next-button"
            aria-label="Button to move to later release"
            @click=${this.handleMove}
          >
            Next
          </button>
        </div>
        <chromedash-roadmap
          ${ref(this.roadmapRef)}
          class="animate"
          aria-label="List of milestone releases"
          .numColumns=${this.numColumns}
          .cardWidth=${this.cardWidth}
          ?signedIn=${Boolean(this.user)}
        >
        </chromedash-roadmap>
      </section>
    `;
  }
}
