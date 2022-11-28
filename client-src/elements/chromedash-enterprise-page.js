import {html} from 'lit';
import {ChromedashAllFeaturesPage} from './chromedash-all-features-page';


export class ChromedashEnterprisePage extends ChromedashAllFeaturesPage {
  renderBox(query) {
    return html`
      <chromedash-feature-table
        query="${query}"
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        ?canApprove=${this.user && this.user.can_approve}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        @open-approvals-event=${this.handleOpenApprovals}
        num=25 alwaysOfferPagination columns="normal">
      </chromedash-feature-table>
    `;
  }

  renderEnterpriseFeatures() {
    return this.renderBox('feature_type=4');
  }

  renderBreankingChanges() {
    return this.renderBox('breaking_change=true');
  }

  render() {
    return html`
      <h2>Enterprise Features</h2>
      ${this.renderEnterpriseFeatures()}

      <h2 style="margin-top: 2em">Breaking Changes</h2>
      ${this.renderBreankingChanges()}
    `;
  }
}

customElements.define('chromedash-enterprise-page', ChromedashEnterprisePage);
