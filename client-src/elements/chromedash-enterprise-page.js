import {html} from 'lit';
import {ChromedashAllFeaturesPage} from './chromedash-all-features-page';


export class ChromedashEnterprisePage extends ChromedashAllFeaturesPage {
  renderBox(query) {
    return html`
      <chromedash-feature-table
        query=${query}
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        num=100 alwaysOfferPagination columns="normal">
      </chromedash-feature-table>
    `;
  }

  renderEnterpriseFeatures() {
    return this.renderBox(
      'feature_type="New Feature or removal affecting enterprises" ' +
        'OR breaking_change=true');
  }

  render() {
    return html`
      <h2>Enterprise features and breaking changes</h2>
      ${this.renderEnterpriseFeatures()}
    `;
  }
}

customElements.define('chromedash-enterprise-page', ChromedashEnterprisePage);
