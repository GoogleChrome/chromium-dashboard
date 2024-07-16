import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User} from '../js-src/cs-client';
import './chromedash-feature-table';
import {ChromedashFeatureTable} from './chromedash-feature-table';
import {showToastMessage} from './utils.js';

@customElement('chromedash-myfeatures-page')
export class ChromedashMyFeaturesPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        sl-details {
          padding: 0 var(--content-padding);
        }
      `,
    ];
  }

  @property({attribute: false})
  user!: User;
  @property({type: Number})
  selectedGateId = 0;
  @state()
  starredFeatures = new Set<number>();

  connectedCallback() {
    super.connectedCallback();
    this.fetchData();
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
    const tables: ChromedashFeatureTable[] = Array.from(
      this.renderRoot.querySelectorAll('chromedash-feature-table')
    );
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
        showToastMessage('Unable to star the Feature. Please Try Again.');
      });
  }

  userCanApprove() {
    return (
      this.user &&
      (this.user.is_admin || this.user.approvable_gate_types?.length > 0)
    );
  }

  renderBox(title, query, columns, sortSpec = '', opened = true) {
    return html`
      <sl-details summary="${title}" ?open=${opened}>
        <chromedash-feature-table
          query="${query}"
          showEnterprise
          sortSpec="${sortSpec}"
          ?signedIn=${Boolean(this.user)}
          ?canEdit=${this.user && this.user.can_edit_all}
          .starredFeatures=${this.starredFeatures}
          @star-toggle-event=${this.handleStarToggle}
          selectedGateId=${this.selectedGateId}
          num="25"
          columns=${columns}
        >
        </chromedash-feature-table>
      </sl-details>
    `;
  }

  renderPendingAndRecentApprovals() {
    const adminNotice = this.user?.is_admin
      ? html`<p>You see all pending approvals because you're a site admin.</p>`
      : nothing;

    const pendingBox = this.renderBox(
      'Features pending my approval',
      'pending-approval-by:me',
      'approvals',
      'gate.requested_on'
    );
    const recentBox = this.renderBox(
      'Recently reviewed features',
      'is:recently-reviewed',
      'normal',
      '-gate.reviewed_on',
      false
    );
    return [adminNotice, pendingBox, recentBox];
  }

  renderIStarred() {
    return this.renderBox('Features I starred', 'starred-by:me', 'normal');
  }

  renderICanEdit() {
    return this.renderBox('Features I can edit', 'can_edit:me', 'normal');
  }

  render() {
    return html`
      <div id="subheader">
        <h2>My features</h2>
      </div>
      <div id="deprecated" class="warning">
        This page will soon be removed from our site.<br />
        Please use one of the "My features" options in the main menu.
      </div>

      ${this.userCanApprove()
        ? this.renderPendingAndRecentApprovals()
        : nothing}
      ${this.renderICanEdit()} ${this.renderIStarred()}
    `;
  }
}
