import {LitElement, css, html, nothing} from 'lit';
import {showToastMessage} from './utils.js';
import './chromedash-feature-table';
import {SHARED_STYLES} from '../css/shared-css.js';
import {customElement, property, queryAll, state} from 'lit/decorators.js';
import {User} from '../js-src/cs-client.js';
import {RawQuery} from './utils.js';

@customElement('chromedash-all-features-page')
export class ChromedashAllFeaturesPage extends LitElement {
  static get styles() {
    return [
      SHARED_STYLES,
      css`
        #content-title {
          padding-top: var(--content-padding);
        }
      `,
    ];
  }

  @property({type: String})
  title = 'Features';
  @property({type: Boolean})
  showQuery = true;
  @property({type: Object})
  user!: User;
  @property({type: Number})
  selectedGateId = 0;
  @property({type: Object})
  rawQuery: RawQuery | undefined = {};

  @state()
  query = '';
  @state()
  columns = 'normal';
  @state()
  showEnterprise = false;
  @state()
  sortSpec = '';
  @state()
  start = 0;
  @state()
  num = 100;
  @state()
  starredFeatures: Set<number> = new Set();

  @queryAll('chromedash-feature-table')
  chromedashFeatureTables;

  connectedCallback() {
    super.connectedCallback();
    this.initializeParams();
    this.fetchData();
  }

  initializeParams() {
    if (!this.rawQuery) {
      return;
    }

    if (this.rawQuery.q != null) {
      this.query = this.rawQuery['q'];
    }
    if (this.rawQuery.columns != null) {
      this.columns = this.rawQuery['columns'];
    }
    if (this.rawQuery.enterprise != null) {
      this.showEnterprise = true;
    }
    if (this.rawQuery.sort != null) {
      this.sortSpec = this.rawQuery['sort'];
    }
    if (
      this.rawQuery.start != null &&
      !Number.isNaN(parseInt(this.rawQuery['start']))
    ) {
      this.start = parseInt(this.rawQuery['start']);
    }
    if (
      this.rawQuery.num != null &&
      !Number.isNaN(parseInt(this.rawQuery['num']))
    ) {
      this.num = parseInt(this.rawQuery['num']);
    }
  }

  fetchData() {
    window.csClient
      .getStars()
      .then(starredFeatures => {
        this.starredFeatures = new Set(starredFeatures);
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  refetch() {
    const tables = this.chromedashFeatureTables;
    for (const table of tables) {
      table.refetch();
    }
  }

  // Handles the Star-Toggle event fired by any one of the child components
  handleStarToggle(e) {
    const newStarredFeatures = new Set(this.starredFeatures);
    window.csClient
      .setStar(e.detail.featureId, e.detail.doStar)
      .then(() => {
        if (e.detail.doStar) {
          newStarredFeatures.add(e.detail.featureId);
        } else {
          newStarredFeatures.delete(e.detail.featureId);
        }
        this.starredFeatures = newStarredFeatures;
      })
      .catch(() => {
        alert('Unable to star the Feature. Please Try Again.');
      });
  }

  renderFeatureList() {
    return html`
      <chromedash-feature-table
        .query=${this.query}
        ?showEnterprise=${this.showEnterprise}
        .sortSpec=${this.sortSpec}
        .start=${this.start}
        .num=${this.num}
        ?showQuery=${this.showQuery}
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        selectedGateId=${this.selectedGateId}
        alwaysOfferPagination
        columns=${this.columns}
      >
      </chromedash-feature-table>
    `;
  }

  render() {
    const adminNotice =
      this.user?.is_admin && this.columns === 'approvals'
        ? html`<p>
            You see all pending approvals because you're a site admin.
          </p>`
        : nothing;

    return html`
      <div id="content-title">
        <h2>${this.title}</h2>
      </div>
      ${adminNotice} ${this.renderFeatureList()}
    `;
  }
}
