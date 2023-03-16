import {LitElement, css, html, nothing} from 'lit';
import './chromedash-feature-detail';
import './chromedash-gantt';
import {openApprovalsDialog} from './chromedash-approvals-dialog';
import {autolink, renderHTMLIf, showToastMessage,
  renderAbsoluteDate, renderRelativeDate,
} from './utils.js';
import {SHARED_STYLES} from '../sass/shared-css.js';

const INACTIVE_STATES = [
  'No longer pursuing',
  'Deprecated',
  'Removed'];


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

        #updated {
          color: var(--unimportant-text-color);
          border-top: var(--default-border);
          padding: var(--content-padding-quarter) 0 0 var(--content-padding);
        }

        li {
          list-style: none;
        }

        #consensus li {
          display: flex;
        }
        #consensus li label {
          width: 125px;
        }

        sl-skeleton {
          margin-bottom: 1em;
          width: 60%;
        }

        sl-skeleton:nth-of-type(even) {
          width: 50%;
        }

        h3 sl-skeleton {
          width: 30%;
          height: 1.5em;
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
      gates: {type: Array},
      comments: {type: Array},
      process: {type: Object},
      dismissedCues: {type: Array},
      contextLink: {type: String},
      appTitle: {type: String},
      starred: {type: Boolean},
      loading: {attribute: false},
      selectedGateId: {type: Number},
      rawQuery: {type: Object},
    };
  }

  constructor() {
    super();
    this.user = {};
    this.featureId = 0;
    this.feature = {};
    this.gates = [];
    this.comments = {};
    this.process = {};
    this.dismissedCues = [];
    this.contextLink = '';
    this.appTitle = '';
    this.starred = false;
    this.loading = true;
    this.selectedGateId = 0;
    this.rawQuery = {};
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
  }

  isFeatureLoaded() {
    return this.feature && Object.keys(this.feature).length !== 0;
  }

  fetchData() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getGates(this.featureId),
      window.csClient.getComments(this.featureId, null, false),
      window.csClient.getFeatureProcess(this.featureId),
      window.csClient.getDismissedCues(),
      window.csClient.getStars(),
    ]).then(([feature, gatesRes, commentRes, process, dismissedCues, starredFeatures]) => {
      this.feature = feature;
      this.gates = gatesRes.gates;
      this.comments = commentRes.comments;
      this.process = process;
      this.dismissedCues = dismissedCues;

      if (starredFeatures.includes(this.featureId)) {
        this.starred = true;
      }
      if (this.feature.name) {
        document.title = `${this.feature.name} - ${this.appTitle}`;
      }
      this.loading = false;
    }).catch((error) => {
      if (error instanceof FeatureNotFoundError) {
        this.loading = false;
      } else {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      }
    });
  }

  refetch() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getGates(this.featureId),
      window.csClient.getComments(this.featureId, null, false),
    ]).then(([feature, gatesRes, commentRes]) => {
      this.feature = feature;
      this.gates = gatesRes.gates;
      this.comments = commentRes.comments;
      this.loading = false;
    }).catch((error) => {
      if (error instanceof FeatureNotFoundError) {
        this.loading = false;
      } else {
        showToastMessage('Some errors occurred. Please refresh the page or try again later.');
      }
    });
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.title = this.appTitle;
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

  /* Open the specific approvals dialog when the user clicks on a gate chip. */
  // TODO(jrobbins): Make it specific.
  handleOpenApprovals(e) {
    e.preventDefault();
    // open old approvals dialog.
    // TODO(jrobbins): Phase this out after approvals column is done.
    openApprovalsDialog(this.user, e.detail.feature);
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

  featureIsInactive() {
    const status = this.feature && this.feature.browsers.chrome.status.text;
    return INACTIVE_STATES.includes(status);
  }

  userCanEdit() {
    return (this.user &&
            (this.user.can_edit_all ||
             this.user.editable_features.includes(this.featureId)));
  }

  renderSubHeader() {
    const canEdit = this.userCanEdit();

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
          ${renderHTMLIf(canEdit && !this.feature.is_enterprise_feature, html`
            <span class="tooltip" title="Edit this feature">
              <a href="/guide/edit/${this.featureId}" class="editfeature" data-tooltip>
                <iron-icon icon="chromestatus:create"></iron-icon>
              </a>
            </span>
          `)}
        </div>
        <h2 id="breadcrumbs">
          <a href="${this.contextLink}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
          </a>
          <a href="/feature/${this.featureId}">
            Feature: ${this.feature.name}
          </a>
          ${this.featureIsInactive() ?
            html`(${this.feature.browsers.chrome.status.text})` :
            nothing}
        </h2>
      </div>
    `;
  }

  renderFeatureContent() {
    return html`
      ${this.feature.unlisted ? html`
        <section id="access">
        <p><b>This feature is only shown in the feature list
        to users with access to edit this feature.</b></p>
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
          <h3>Demos and samples</h3>
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

  renderEnterpriseFeatureStatus() {
    return html`
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
    `;
  }

  renderUpdated() {
    return html`
      <section id="updated">
          Last updated on
          ${renderAbsoluteDate(this.feature.updated?.when, true)}
          ${renderRelativeDate(this.feature.updated?.when)}
      </section>
    `;
  }

  renderFeatureDetails() {
    return html`
      <chromedash-feature-detail
        .loading=${this.loading}
        .user=${this.user}
        ?canEdit=${this.userCanEdit()}
        .feature=${this.feature}
        .gates=${this.gates}
        .comments=${this.comments}
        .process=${this.process}
        .dismissedCues=${this.dismissedCues}
        .rawQuery=${this.rawQuery}
        @open-approvals-event=${this.handleOpenApprovals}
        selectedGateId=${this.selectedGateId}
       >
      </chromedash-feature-detail>
    `;
  }

  render() {
    // TODO: create another element - chromedash-feature-highlights
    // for all the content of the <div id="feature"> part of the page
    // If loading, only render the skeletons.
    if (this.loading) {
      return this.renderSkeletons();
    }
    // If after loading, the feature did not load, render nothing.
    if (!this.isFeatureLoaded()) {
      return html `Feature not found.`;
    }
    // At this point, the feature has loaded successfully, render the components.
    return html`
      ${this.renderSubHeader()}
      <div id="feature">
        ${this.renderFeatureContent()}
        ${this.feature.is_enterprise_feature ?
            this.renderEnterpriseFeatureStatus() :
            this.renderFeatureStatus()}
        ${this.renderUpdated()}
      </div>
      ${this.renderFeatureDetails()}
    `;
  }
}

customElements.define('chromedash-feature-page', ChromedashFeaturePage);
