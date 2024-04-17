import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import './chromedash-feature-detail';
import {DETAILS_STYLES} from './chromedash-feature-detail';
import './chromedash-gantt';
import {enhanceUrl} from './chromedash-link';
import './chromedash-vendor-views';
import {
  autolink,
  renderAbsoluteDate,
  renderHTMLIf,
  renderRelativeDate,
  showToastMessage,
} from './utils.js';

const INACTIVE_STATES = ['No longer pursuing', 'Deprecated', 'Removed'];

export class ChromedashFeaturePage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...DETAILS_STYLES,
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

        li {
          list-style: none;
        }

        #consensus li {
          display: flex;
        }
        #consensus li label {
          width: 125px;
        }

        #history p {
          margin-top: var(--content-padding-half);
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

        sl-dropdown {
          float: right;
          margin-right: -16px;
          margin-top: -20px;
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
      `,
    ];
  }

  static get properties() {
    return {
      user: {attribute: false},
      paired_user: {attribute: false},
      featureId: {type: Number},
      feature: {type: Object},
      featureLinks: {type: Array},
      gates: {type: Array},
      comments: {type: Array},
      process: {type: Object},
      progress: {type: Object},
      dismissedCues: {type: Array},
      contextLink: {type: String},
      appTitle: {type: String},
      starred: {type: Boolean},
      loading: {attribute: false},
      selectedGateId: {type: Number},
    };
  }

  constructor() {
    super();
    this.user = null;
    this.featureId = 0;
    this.feature = {};
    this.featureLinks = [];
    this.gates = [];
    this.comments = {};
    this.process = {};
    this.progress = {};
    this.dismissedCues = [];
    this.contextLink = '';
    this.appTitle = '';
    this.starred = false;
    this.loading = true;
    this.selectedGateId = 0;
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
      window.csClient.getComments(this.featureId, null),
      window.csClient.getFeatureProcess(this.featureId),
      window.csClient.getDismissedCues(),
      window.csClient.getStars(),
      window.csClient.getFeatureProgress(this.featureId),
    ])
      .then(
        ([
          feature,
          gatesRes,
          commentRes,
          process,
          dismissedCues,
          starredFeatures,
          progress,
        ]) => {
          this.feature = feature;
          this.gates = gatesRes.gates;
          this.comments = commentRes.comments;
          this.process = process;
          this.dismissedCues = dismissedCues;
          this.progress = progress;
          if (starredFeatures.includes(this.featureId)) {
            this.starred = true;
          }
          if (this.feature.name) {
            document.title = `${this.feature.name} - ${this.appTitle}`;
          }
          this.loading = false;
        }
      )
      .catch(error => {
        if (error instanceof FeatureNotFoundError) {
          this.loading = false;
        } else {
          showToastMessage(
            'Some errors occurred. Please refresh the page or try again later.'
          );
        }
      });

    window.csClient.getFeatureLinks(this.featureId).then(featureLinks => {
      this.featureLinks = featureLinks?.data || [];
      if (featureLinks?.has_stale_links) {
        // delay 10 seconds to fetch server to get latest link information
        setTimeout(this.refetchFeatureLinks.bind(this), 10000);
      }
    });
  }

  async refetchFeatureLinks() {
    const featureLinks = await window.csClient.getFeatureLinks(
      this.featureId,
      false
    );
    this.featureLinks = featureLinks?.data || [];
  }

  refetch() {
    this.loading = true;
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getGates(this.featureId),
      window.csClient.getComments(this.featureId, null),
    ])
      .then(([feature, gatesRes, commentRes]) => {
        this.feature = feature;
        this.gates = gatesRes.gates;
        this.comments = commentRes.comments;
        this.loading = false;
      })
      .catch(error => {
        if (error instanceof FeatureNotFoundError) {
          this.loading = false;
        } else {
          showToastMessage(
            'Some errors occurred. Please refresh the page or try again later.'
          );
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
      navigator
        .share({
          title: this.feature.name,
          text: this.feature.summary,
          url: url,
        })
        .then(() => {
          ga('send', 'social', {
            socialNetwork: 'web',
            socialAction: 'share',
            socialTarget: url,
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

  canDeleteFeature() {
    return this.user?.is_admin || this.userCanEdit();
  }

  handleDeleteFeature() {
    if (!confirm('Delete feature?')) return;

    window.csClient.doDelete(`/features/${this.feature.id}`).then(resp => {
      if (resp.message === 'Done') {
        location.href = '/features';
      }
    });
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
        ${this.renderSkeletonSection()} ${this.renderSkeletonSection()}
        ${this.renderSkeletonSection()} ${this.renderSkeletonSection()}
      </div>
    `;
  }

  featureIsInactive() {
    const status = this.feature && this.feature.browsers.chrome.status.text;
    return INACTIVE_STATES.includes(status);
  }

  userCanEdit() {
    return (
      this.user &&
      (this.user.can_edit_all ||
        this.user.editable_features.includes(this.featureId))
    );
  }

  pairedUserCanEdit() {
    return (
      this.paired_user?.can_edit_all ||
      this.paired_user?.editable_features.includes(this.featureId)
    );
  }

  renderSubHeader() {
    const canEdit = this.userCanEdit();

    return html`
      <div id="subheader" style="display:block">
        <div class="tooltips" style="float:right">
          ${this.user
            ? html`
                <span
                  class="tooltip"
                  title="Receive an email notification when there are updates"
                >
                  <a
                    href="#"
                    data-tooltip
                    id="star-when-signed-in"
                    @click=${this.handleStarClick}
                  >
                    <iron-icon
                      icon=${this.starred
                        ? 'chromestatus:star'
                        : 'chromestatus:star-border'}
                      class="pushicon"
                    ></iron-icon>
                  </a>
                </span>
              `
            : nothing}
          <span class="tooltip" title="File a bug against this feature">
            <a
              href=${this.feature.new_crbug_url}
              class="newbug"
              data-tooltip
              target="_blank"
              rel="noopener"
            >
              <iron-icon icon="chromestatus:bug-report"></iron-icon>
            </a>
          </span>
          <span
            class="tooltip ${navigator.share ? '' : 'no-web-share'}"
            title="Share this feature"
          >
            <a
              href="#"
              data-tooltip
              id="share-feature"
              @click=${this.handleShareClick}
            >
              <iron-icon icon="chromestatus:share"></iron-icon>
            </a>
          </span>
          <span
            class="tooltip copy-to-clipboard"
            title="Copy link to clipboard"
          >
            <a
              href="/feature/${this.featureId}"
              data-tooltip
              id="copy-link"
              @click=${this.handleCopyLinkClick}
            >
              <iron-icon icon="chromestatus:link"></iron-icon>
            </a>
          </span>
          ${renderHTMLIf(
            canEdit && !this.feature.is_enterprise_feature,
            html`
              <span class="tooltip" title="Edit this feature">
                <a
                  href="/guide/edit/${this.featureId}"
                  class="editfeature"
                  data-tooltip
                >
                  <iron-icon icon="chromestatus:create"></iron-icon>
                </a>
              </span>
            `
          )}
        </div>
        <h2 id="breadcrumbs">
          <a href="${this.contextLink}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
          </a>
          <a href="/feature/${this.featureId}">
            Feature: ${this.feature.name}
          </a>
          ${this.featureIsInactive()
            ? html`(${this.feature.browsers.chrome.status.text})`
            : nothing}
        </h2>
      </div>
    `;
  }

  renderWarnings() {
    const warnings = [];
    if (this.feature.deleted) {
      warnings.push(html`
        <div id="deleted" class="warning">
          This feature is marked as deleted. It does not appear in feature lists
          and is only viewable by users who can edit it.
        </div>
      `);
    }
    if (this.feature.unlisted) {
      warnings.push(html`
        <div id="access" class="warning">
          This feature is only shown in the feature list to users with access to
          edit this feature.
        </div>
      `);
    }
    if (!this.userCanEdit() && this.pairedUserCanEdit()) {
      warnings.push(html`
        <div id="switch_to_edit" class="warning">
          User ${this.user.email} cannot edit this feature or request reviews.
          But, ${this.paired_user.email} can do that.
          <br />
          To switch users: sign out and then sign in again.
        </div>
      `);
    }
    if (
      this.user?.approvable_gate_types.length == 0 &&
      this.paired_user?.approvable_gate_types.length > 0
    ) {
      warnings.push(html`
        <div id="switch_to_review" class="warning">
          User ${this.user.email} cannot review this feature. But,
          ${this.paired_user.email} can do that.
          <br />
          To switch users: sign out and then sign in again.
        </div>
      `);
    }
    return warnings;
  }

  renderEnterpriseFeatureContent() {
    return html`
      ${this.feature.summary
        ? html`
            <section id="summary">
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.summary,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
    `;
  }

  renderFeatureContent() {
    return html`
      ${this.feature.summary
        ? html`
            <section id="summary">
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.summary,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
      ${this.feature.motivation
        ? html`
            <section id="motivation">
              <h3>Motivation</h3>
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.motivation,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
      ${this.feature.resources?.samples?.length
        ? html`
            <section id="demo">
              <h3>Demos and samples</h3>
              <ul>
                ${this.feature.resources.samples.map(
                  sampleLink => html`
                    <li>${enhanceUrl(sampleLink, this.featureLinks)}</li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
      ${this.feature.resources?.docs?.length
        ? html`
            <section id="documentation">
              <h3>Documentation</h3>
              <ul>
                ${this.feature.resources.docs.map(
                  docLink => html`
                    <li>${enhanceUrl(docLink, this.featureLinks)}</li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
      ${this.feature.standards.spec
        ? html`
            <section id="specification">
              <h3>Specification</h3>
              <p>
                ${enhanceUrl(this.feature.standards.spec, this.featureLinks)}
              </p>
              <p>Spec status: ${this.feature.standards.maturity.text}</p>
            </section>
          `
        : this.feature.explainer_links?.length
          ? html`
              <section id="specification">
                <h3>Explainer(s)</h3>
                ${this.feature.explainer_links?.map(
                  link => html`<p>${enhanceUrl(link, this.featureLinks)}</p>`
                )}
              </section>
            `
          : nothing}
    `;
  }

  renderEnterpriseFeatureStatus() {
    return html`
      ${this.feature.browsers.chrome.owners
        ? html`
            <section id="owner">
              <h3>
                ${this.feature.browsers.chrome.owners.length == 1
                  ? 'Owner'
                  : 'Owners'}
              </h3>
              <ul>
                ${this.feature.browsers.chrome.owners.map(
                  owner => html`
                    <li><a href="mailto:${owner}">${owner}</a></li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
    `;
  }

  renderFeatureStatus() {
    return html`
      <section id="status">
        <h3>Status in Chromium</h3>
        ${this.feature.browsers.chrome.blink_components
          ? html`
              <p>
                <label>Blink components:</label>
                ${this.feature.browsers.chrome.blink_components.map(
                  c => html`
                    <a
                      href="https://bugs.chromium.org/p/chromium/issues/list?q=component:${c}"
                      target="_blank"
                      rel="noopener"
                      >${c}</a
                    >
                  `
                )}
              </p>
            `
          : nothing}
        <br />
        <p>
          <label>Implementation status:</label>
          <b>${this.feature.browsers.chrome.status.text}</b>
          ${this.feature.browsers.chrome.bug
            ? html`<chromedash-link
                href=${this.feature.browsers.chrome.bug}
                .featureLinks=${this.featureLinks}
                alwaysInTag
                >tracking bug</chromedash-link
              >`
            : nothing}
          <chromedash-gantt .feature=${this.feature}></chromedash-gantt>
        </p>
      </section>

      <section id="consensus">
        <h3>Consensus &amp; Standardization</h3>
        <div style="font-size:smaller;">
          After a feature ships in Chrome, the values listed here are not
          guaranteed to be up to date.
        </div>
        <br />
        <ul>
          ${this.feature.browsers.ff.view.val
            ? html`
                <li>
                  <label>Firefox:</label>
                  <chromedash-vendor-views
                    href=${this.feature.browsers.ff.view.url || nothing}
                    .featureLinks=${this.featureLinks}
                    >${this.feature.browsers.ff.view
                      .text}</chromedash-vendor-views
                  >
                </li>
              `
            : nothing}
          ${this.feature.browsers.safari.view.val
            ? html`
                <li>
                  <label>Safari:</label>
                  <chromedash-vendor-views
                    href=${this.feature.browsers.safari.view.url || nothing}
                    .featureLinks=${this.featureLinks}
                    >${this.feature.browsers.safari.view
                      .text}</chromedash-vendor-views
                  >
                </li>
              `
            : nothing}
          <li>
            <label>Web Developers:</label> ${this.feature.browsers.webdev.view
              .text}
          </li>
        </ul>
      </section>

      ${this.feature.browsers.chrome.owners
        ? html`
            <section id="owner">
              <h3>
                ${this.feature.browsers.chrome.owners.length == 1
                  ? 'Owner'
                  : 'Owners'}
              </h3>
              <ul>
                ${this.feature.browsers.chrome.owners.map(
                  owner => html`
                    <li><a href="mailto:${owner}">${owner}</a></li>
                  `
                )}
              </ul>
            </section>
          `
        : nothing}
      ${this.feature.intent_to_implement_url
        ? html`
            <section id="intent_to_implement_url">
              <h3>Intent to Prototype url</h3>
              <a href=${this.feature.intent_to_implement_url}
                >Intent to Prototype thread</a
              >
            </section>
          `
        : nothing}
      ${this.feature.comments
        ? html`
            <section id="comments">
              <h3>Comments</h3>
              <!-- prettier-ignore -->
              <p class="preformatted">${autolink(
                this.feature.comments,
                this.featureLinks
              )}</p>
            </section>
          `
        : nothing}
      ${this.feature.tags
        ? html`
            <section id="tags">
              <h3>Search tags</h3>
              ${this.feature.tags.map(
                tag => html`
                  <a href="/features#tags:${tag}">${tag}</a
                  ><span class="conditional-comma">, </span>
                `
              )}
            </section>
          `
        : nothing}
    `;
  }

  renderHistory() {
    return html`
      <section id="history">
        <h3>History</h3>
        <p>
          Entry created on
          ${renderAbsoluteDate(this.feature.created?.when, true)}
          ${renderRelativeDate(this.feature.created?.when)}
        </p>
        <p>
          Last updated on
          ${renderAbsoluteDate(this.feature.updated?.when, true)}
          ${renderRelativeDate(this.feature.updated?.when)}
        </p>

        <p>
          <a href="/feature/${this.feature.id}/activity">
            All comments &amp; activity
          </a>
        </p>
      </section>
    `;
  }

  renderFeatureDetails() {
    return html`
      <chromedash-feature-detail
        appTitle=${this.appTitle}
        .loading=${this.loading}
        .user=${this.user}
        ?canEdit=${this.userCanEdit()}
        .feature=${this.feature}
        .gates=${this.gates}
        .comments=${this.comments}
        .process=${this.process}
        .progress=${this.progress}
        .dismissedCues=${this.dismissedCues}
        .featureLinks=${this.featureLinks}
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
      return html`Feature not found.`;
    }
    // At this point, the feature has loaded successfully, render the components.
    return html`
      ${this.renderSubHeader()} ${this.renderWarnings()}
      <sl-details summary="Overview" ?open=${true}>
        <section class="card">
          ${this.canDeleteFeature()
            ? html`
                <sl-dropdown placement="left-start">
                  <sl-icon-button
                    library="material"
                    name="more_vert_24px"
                    label="Feature menu"
                    style="font-size: 1.3rem;"
                    slot="trigger"
                  ></sl-icon-button>
                  <sl-menu-item value="undo">
                    <a
                      id="delete-feature"
                      class="delete-button"
                      @click=${this.handleDeleteFeature}
                    >
                      Delete
                    </a>
                  </sl-menu-item>
                </sl-dropdown>
              `
            : nothing}
          ${this.feature.is_enterprise_featqcure
            ? this.renderEnterpriseFeatureContent()
            : this.renderFeatureContent()}
          ${this.feature.is_enterprise_feature
            ? this.renderEnterpriseFeatureStatus()
            : this.renderFeatureStatus()}
          ${this.renderHistory()}
        </section>
      </sl-details>
      ${this.renderFeatureDetails()}
    `;
  }
}

customElements.define('chromedash-feature-page', ChromedashFeaturePage);
