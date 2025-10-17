import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {ifDefined} from 'lit/directives/if-defined.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  Feature,
  FeatureLink,
  FeatureNotFoundError,
  User,
  StageDict,
} from '../js-src/cs-client.js';
import './chromedash-feature-detail';
import {DETAILS_STYLES} from './chromedash-feature-detail';
import './chromedash-feature-highlights.js';
import {GateDict} from './chromedash-gate-chip.js';
import {Process, ProgressItem} from './chromedash-gate-column.js';
import {
  showToastMessage,
  getFeatureOutdatedBanner,
  findClosestShippingDate,
  closestShippingDateInfo,
} from './utils.js';
import {
  STAGE_TYPES_SHIPPING,
  STAGE_TYPES_ORIGIN_TRIAL,
  IMPLEMENTATION_STATUS,
} from './form-field-enums';

const INACTIVE_STATES = ['No longer pursuing', 'Deprecated', 'Removed'];
declare var ga: Function;

@customElement('chromedash-feature-page')
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
      `,
    ];
  }

  @property({attribute: false})
  user!: User;
  @property({attribute: false})
  paired_user!: User;
  @property({attribute: false})
  featureId = 0;
  @property({attribute: false})
  feature!: Feature;
  @property({attribute: false})
  featureLinks: FeatureLink[] = [];
  @property({attribute: false})
  gates: GateDict[] = [];
  @property({attribute: false})
  comments: string[] = [];
  @property({attribute: false})
  process!: Process;
  @property({attribute: false})
  progress!: ProgressItem;
  @property({attribute: false})
  contextLink = '';
  @property({type: String})
  appTitle = '';
  @property({type: Number})
  selectedGateId = 0;
  @state()
  starred = false;
  @state()
  loading = true;
  @state()
  currentDate: number = Date.now();
  @state()
  shippingInfo: closestShippingDateInfo = {
    // The closest milestone shipping date as an ISO string.
    closestShippingDate: '',
    hasShipped: false,
    isUpcoming: false,
  };

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
      window.csClient.getStars(),
      window.csClient.getFeatureProgress(this.featureId),
      window.csClient.getChannels(),
    ])
      .then(
        async ([
          feature,
          gatesRes,
          commentRes,
          process,
          starredFeatures,
          progress,
          channels,
        ]) => {
          this.feature = feature;
          this.gates = gatesRes.gates;
          this.comments = commentRes.comments;
          this.process = process;
          this.progress = progress;
          if (starredFeatures.includes(this.featureId)) {
            this.starred = true;
          }
          if (this.feature.name) {
            document.title = `${this.feature.name} - ${this.appTitle}`;
          }
          this.shippingInfo = await findClosestShippingDate(
            channels,
            feature.stages
          );


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
    Promise.all([
      window.csClient.getFeature(this.featureId),
      window.csClient.getGates(this.featureId),
      window.csClient.getComments(this.featureId, null),
    ])
      .then(([feature, gatesRes, commentRes]) => {
        this.feature = feature;
        this.gates = gatesRes.gates;
        this.comments = commentRes.comments;
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

  handleArchiveFeature() {
    if (
      !confirm(
        'Archive feature? It will only be visible to users who can edit it'
      )
    )
      return;

    window.csClient.doDelete(`/features/${this.feature.id}`).then(resp => {
      if (resp.message === 'Done') {
        location.href = '/features';
      }
    });
  }

  handleSuspend() {
    if (
      !confirm(
        'Suspend development of this feature? It will not appear on the roadmap.'
      )
    ) {
      return;
    }

    const submitBody = {
      feature_changes: {
        id: this.feature.id,
        impl_status_chrome: IMPLEMENTATION_STATUS.ON_HOLD[0],
      },
      stages: [],
      has_changes: true,
    };
    window.csClient.updateFeature(submitBody).then(resp => {
      window.location.reload();
    });
  }

  handleResume() {
    if (
      !confirm(
        'Resume active development of this feature? It will appear on the roadmap if it has milestones set.'
      )
    ) {
      return;
    }

    const submitBody = {
      feature_changes: {
        id: this.feature.id,
        impl_status_chrome: IMPLEMENTATION_STATUS.PROPOSED[0],
      },
      stages: [],
      has_changes: true,
    };
    window.csClient.updateFeature(submitBody).then(resp => {
      window.location.reload();
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
    const status =
      (this.feature && this.feature.browsers.chrome.status.text) || '';
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
    const canShare = typeof navigator.share === 'function';
    return html`
      <div id="subheader" style="display:block">
        <div class="tooltips" style="float:right; font-size:1.1rem">
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
                    <sl-icon
                      name=${this.starred ? 'star-fill' : 'star'}
                      class="pushicon"
                    ></sl-icon>
                  </a>
                </span>
              `
            : nothing}
          <span class="tooltip" title="File a bug against this feature">
            <a
              href=${ifDefined(this.feature.new_crbug_url)}
              class="newbug"
              data-tooltip
              target="_blank"
              rel="noopener"
            >
              <sl-icon name="bug"></sl-icon>
            </a>
          </span>
          <span
            class="tooltip ${canShare ? '' : 'no-web-share'}"
            title="Share this feature"
          >
            <a
              href="#"
              data-tooltip
              id="share-feature"
              @click=${this.handleShareClick}
            >
              <sl-icon name="share"></sl-icon>
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
              <sl-icon library="material" name="link"></sl-icon>
            </a>
          </span>
        </div>
        <h2 id="breadcrumbs">
          <a href="${this.contextLink}">
            <sl-icon name="arrow-left"></sl-icon>
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
    const warnings: TemplateResult[] = [];
    if (this.feature.deleted) {
      warnings.push(html`
        <div id="archived" class="warning">
          This feature is archived. It does not appear in feature lists and is
          only viewable by users who can edit it.
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
    const userCanEdit = this.userCanEdit();
    const featureOutdatedBanner = getFeatureOutdatedBanner(this.feature, this.shippingInfo, this.currentDate, userCanEdit);
    if (featureOutdatedBanner) {
      warnings.push(featureOutdatedBanner);
    }

    return warnings;
  }

  renderFeatureDetails() {
    return html`
      <chromedash-feature-detail
        appTitle=${this.appTitle}
        .user=${this.user}
        ?canEdit=${this.userCanEdit()}
        .feature=${this.feature}
        .gates=${this.gates}
        .comments=${this.comments}
        .process=${this.process}
        .progress=${this.progress}
        .featureLinks=${this.featureLinks}
        selectedGateId=${this.selectedGateId}
      >
      </chromedash-feature-detail>
    `;
  }

  render() {
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
      <chromedash-feature-highlights
        .feature=${this.feature}
        .featureLinks=${this.featureLinks}
        ?canDeleteFeature=${this.canDeleteFeature()}
        ?canEditFeature=${this.userCanEdit()}
        @archive=${this.handleArchiveFeature}
        @suspend=${this.handleSuspend}
        @resume=${this.handleResume}
      ></chromedash-feature-highlights>
      ${this.renderFeatureDetails()}
    `;
  }
}
