import {LitElement, css, html, nothing} from 'lit';
import './chromedash-feature-detail';
import './chromedash-gantt';
import {openApprovalsDialog} from './chromedash-approvals-dialog';
import {autolink, showToastMessage} from './utils.js';

import {SHARED_STYLES} from '../sass/shared-css.js';

export class ChromedashFeaturePage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #feature {
          background: var(--card-background);
          border-radius: var(--default-border-radius);
          border: var(--card-border);
          box-shadow: var(--card-box-shadow);

          box-sizing: border-box;
          word-wrap: break-word;
          margin-bottom: var(--content-padding);
          max-width: var(--max-content-width);
        }
        #feature ul {
          list-style-position: inside;
          list-style: none;
        }
        section {
          margin-bottom: 1em;
        }
        section h3 {
          margin: 24px 0 12px;
        }
        section label {
          font-weight: 500;
          margin-right: 5px;
        }

        #consensus li {
          display: flex;
        }
        #consensus li label {
          width: 125px;
        }

        @media only screen and (max-width: 700px) {
          #feature {
            border-radius: 0 !important;
            margin: 7px initial !important;
          }
        }

        @media only screen and (min-width: 701px) {
          #feature {
            padding: 30px 40px;
          }
        }
    `];
  }

  static get properties() {
    return {
      user: {type: Object},
      featureId: {type: Number},
      feature: {type: Object},
      process: {type: Object},
      fieldDefs: {type: Object},
      dismissedCues: {type: Array},
      contextLink: {type: String},
      starred: {type: Boolean},
      loading: {attribute: false},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.featureId = 0;
    this.feature = {};
    this.process = {};
    this.fieldDefs = {};
    this.dismissedCues = [];
    this.contextLink = '';
    this.starred = false;
    this.loading = true;
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getPermissions(),
      window.csClient.getFeature(this.featureId),
      window.csClient.getFeatureProcess(this.featureId),
      window.csClient.getFieldDefs(),
      window.csClient.getDismissedCues(),
      window.csClient.getStars(),
    ]).then(([user, feature, process, fieldDefs, dismissedCues, starredFeatures]) => {
      this.user = user;
      this.feature = feature;
      this.process = process;
      this.fieldDefs = fieldDefs;
      this.dismissedCues = dismissedCues;

      if (starredFeatures.includes(this.featureId)) {
        this.starred = true;
      }
      this.loading = false;

      // TODO(kevinshen56714): Remove this once SPA index page is set up.
      // Has to include this for now to remove the spinner at _base.html.
      document.body.classList.remove('loading');
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  handleStarClick(e) {
    e.preventDefault();
    window.csClient.setStar(this.featureId, !this.starred).then(() => {
      this.starred = !this.starred;
    });
  }

  handleShareClick(e) {
    e.preventDefault();
    if (navigator.share) {
      const url = '/feature/' + this.featureId;
      navigator.share({
        title: this.feature.name,
        text: this.feature.summary,
        url: url,
      }).then(() => {
        ga('send', 'social',
          {
            'socialNetwork': 'web',
            'socialAction': 'share',
            'socialTarget': url,
          });
      });
    }
  }

  handleCopyLinkClick(e) {
    e.preventDefault();
    const url = e.currentTarget.href;
    navigator.clipboard.writeText(url).then(() => {
      showToastMessage('Link copied');
    });
  }

  handleApprovalClick(e) {
    e.preventDefault();
    openApprovalsDialog(this.user.email, this.feature);
  }

  renderSkeletonSection() {
    return html`
      <section>
        <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
        <p>
          <sl-skeleton effect="sheen"></sl-skeleton>
          <sl-skeleton effect="sheen"></sl-skeleton>
        </p>
      </section>
    `;
  }

  renderSkeletons() {
    return html`
      <div id="feature" style="margin-top: 65px;">
        ${this.renderSkeletonSection()}
        ${this.renderSkeletonSection()}
        ${this.renderSkeletonSection()}
        ${this.renderSkeletonSection()}
      </div>
   `;
  }

  renderSubHeader() {
    return html`
      <div id="subheader" style="display:block">
        <div class="tooltips" style="float:right">
          ${this.user ? html`
            <span class="tooltip" title="Receive an email notification when there are updates">
              <a href="#" data-tooltip id="star-when-signed-in" @click=${this.handleStarClick}>
                <iron-icon icon=${this.starred ? 'chromestatus:star' : 'chromestatus:star-border'} class="pushicon"></iron-icon>
              </a>
            </span>
          `: nothing}
          <span class="tooltip" title="File a bug against this feature">
            <a href=${this.feature.new_crbug_url} class="newbug" data-tooltip target="_blank" rel="noopener">
              <iron-icon icon="chromestatus:bug-report"></iron-icon>
            </a>
          </span>
          <span class="tooltip ${navigator.share ? '' : 'no-web-share'}" title="Share this feature">
            <a href="#" data-tooltip id="share-feature" @click=${this.handleShareClick}>
              <iron-icon icon="chromestatus:share"></iron-icon>
            </a>
          </span>
          <span class="tooltip copy-to-clipboard" title="Copy link to clipboard">
            <a href="/feature/${this.featureId}" data-tooltip id="copy-link" @click=${this.handleCopyLinkClick}>
              <iron-icon icon="chromestatus:link"></iron-icon>
            </a>
          </span>
          ${this.user && this.user.can_approve ? html`
            <span class="tooltip" title="Review approvals">
              <a href="#" id="approvals-icon" data-tooltip @click=${this.handleApprovalClick}>
                <iron-icon icon="chromestatus:approval"></iron-icon>
              </a>
            </span>
          `: nothing}
          ${this.user && this.user.can_edit ? html`
            <span class="tooltip" title="Edit this feature">
              <a href="/guide/edit/${this.featureId}" class="editfeature" data-tooltip>
                <iron-icon icon="chromestatus:create"></iron-icon>
              </a>
            </span>
          `: nothing}
        </div>
        <h2 id="breadcrumbs">
          <a href="${this.contextLink}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
          </a>
          <a href="/feature/${this.featureId}">
            Feature: ${this.feature.name}
          </a>
          (${this.feature.browsers.chrome.status.text})
        </h2>
      </div>
    `;
  }

  renderFeatureContent() {
    return html`
      ${this.feature.unlisted ? html`
        <section id="access">
        <p><b>This feature is only shown in the feature list to users with
        edit access.</b></p>
        </section>
      `: nothing}

      ${this.feature.summary ? html`
        <section id="summary">
          <p class="preformatted">${autolink(this.feature.summary)}</p>
        </section>
      `: nothing}

      ${this.feature.motivation ? html`
        <section id="motivation">
          <h3>Motivation</h3>
          <p class="preformatted">${autolink(this.feature.motivation)}</p>
        </section>
      `: nothing}

      ${this.feature.resources && this.feature.resources.samples ? html`
        <section id="demo">
          <h3>${this.feature.resources.samples.length == 1 ? 'Demo' : 'Demos'}</h3>
          <ul>
            ${this.feature.resources.samples.map((sampleLink) => html`
              <li><a href="${sampleLink}">${sampleLink}</a></li>
            `)}
          </ul>
        </section>
      `: nothing}

      ${this.feature.resources && this.feature.resources.docs ? html`
        <section id="documentation">
          <h3>Documentation</h3>
          <ul>
            ${this.feature.resources.docs.map((docLink) => html`
              <li><a href="${docLink}">${docLink}</a></li>
            `)}
          </ul>
        </section>
      `: nothing}

      ${this.feature.standards.spec ? html`
        <section id="specification">
          <h3>Specification</h3>
          <p><a href=${this.feature.standards.spec} target="_blank" rel="noopener">
            Specification link
          </a></p>
          <br>
          <p>
            <label>Status:</label>
            ${this.feature.standards.maturity.text}
          </p>
        </section>
      `: nothing}
    `;
  }

  renderFeatureStatus() {
    return html`
      <section id="status">
        <h3>Status in Chromium</h3>
        ${this.feature.browsers.chrome.blink_components ? html`
          <p>
            <label>Blink components:</label>
            ${this.feature.browsers.chrome.blink_components.map((c) => html`
              <a href="https://bugs.chromium.org/p/chromium/issues/list?q=component:${c}"
               target="_blank" rel="noopener">${c}</a>
            `)}
          </p>
        `: nothing}
        <br>
        <p>
          <label>Implementation status:</label>
          <b>${this.feature.browsers.chrome.status.text}</b>
          ${this.feature.browsers.chrome.bug ? html`
            (<a href=${this.feature.browsers.chrome.bug} target="_blank" rel="noopener">tracking bug</a>)
          `: nothing}
          <chromedash-gantt .feature=${this.feature}></chromedash-gantt>
        </p>
      </section>

      <section id="consensus">
        <h3>Consensus &amp; Standardization</h3>
        <div style="font-size:smaller;">After a feature ships in Chrome, the values listed here are not guaranteed to be up to date.</div>
        <br>
        <ul>
          ${this.feature.browsers.ff.view.val ? html`
            <li>
              <label>Firefox:</label>
              ${this.feature.browsers.ff.view.url ? html`
                <a href=${this.feature.browsers.ff.view.url}>${this.feature.browsers.ff.view.text}</a>
              `: html`
                ${this.feature.browsers.ff.view.text}
              `}
            </li>
          `: nothing}
          ${this.feature.browsers.safari.view.val ? html`
            <li>
              <label>Safari:</label>
              ${this.feature.browsers.safari.view.url ? html`
                <a href=${this.feature.browsers.safari.view.url}>${this.feature.browsers.safari.view.text}</a>
              `: html`
                ${this.feature.browsers.safari.view.text}
              `}
            </li>
          `: nothing}
          <li><label>Web Developers:</label> ${this.feature.browsers.webdev.view.text}</li>
        </ul>
      </section>

      ${this.feature.browsers.chrome.owners ? html`
        <section id="owner">
          <h3>${this.feature.browsers.chrome.owners.length == 1 ? 'Owner' : 'Owners'}</h3>
          <ul>
            ${this.feature.browsers.chrome.owners.map((owner) => html`
              <li><a href="mailto:${owner}">${owner}</a></li>
            `)}
          </ul>
        </section>
      `: nothing}

      ${this.feature.intent_to_implement_url ? html`
        <section id="intent_to_implement_url">
          <h3>Intent to Prototype url</h3>
          <a href=${this.feature.intent_to_implement_url }>Intent to Prototype thread</a>
        </section>
      `: nothing}

      ${this.feature.comments ? html`
        <section id="comments">
          <h3>Comments</h3>
          <p class="preformatted">${autolink(this.feature.comments)}</p>
        </section>
      `: nothing}

      ${this.feature.tags ? html`
        <section id="tags">
          <h3>Search tags</h3>
            ${this.feature.tags.map((tag) => html`
              <a href="/features#tags:${tag}">${tag}</a><span
                class="conditional-comma">, </span>
            `)}
        </section>
      `: nothing}

      <section id="updated">
        <p><span>Last updated on ${this.feature.updated_display}</span></p>
      </section>
    `;
  }

  renderFeatureDetails() {
    return html`
      <sl-details
        id="details"
        summary="Additional fields by process phase">
        <chromedash-feature-detail
          .feature=${this.feature}
          .process=${this.process}
          .fieldDefs=${this.fieldDefs}
          .dismissedCues=${this.dismissedCues}>
        </chromedash-feature-detail>
      </sl-details>
    `;
  }

  render() {
    // TODO: Create precomiled main, forms, and guide css files,
    // and import them instead of inlining them here
    // TODO: create another element - chromedash-feature-highlights
    // for all the content of the <div id="feature"> part of the page
    return html`
      <link rel="stylesheet" href="/static/css/main.css">
      <link rel="stylesheet" href="/static/css/forms.css">
      <link rel="stylesheet" href="/static/css/guide.css">
      ${this.loading ?
        this.renderSkeletons() :
        html`
          ${this.renderSubHeader()}
          <div id="feature">
            ${this.renderFeatureContent()}
            ${this.renderFeatureStatus()}
          </div>
          ${this.renderFeatureDetails()}
      `}
    `;
  }
}

customElements.define('chromedash-feature-page', ChromedashFeaturePage);
