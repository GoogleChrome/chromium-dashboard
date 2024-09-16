import {html} from 'lit';
import {ChromedashAllFeaturesPage} from './chromedash-all-features-page';
import {customElement} from 'lit/decorators.js';

@customElement('chromedash-enterprise-page')
export class ChromedashEnterprisePage extends ChromedashAllFeaturesPage {
  renderBox(query) {
    return html`
      <chromedash-feature-table
        query=${query}
        ?signedIn=${Boolean(this.user)}
        ?canEdit=${this.user && this.user.can_edit_all}
        .starredFeatures=${this.starredFeatures}
        @star-toggle-event=${this.handleStarToggle}
        num="100"
        alwaysOfferPagination
        columns="normal"
      >
      </chromedash-feature-table>
    `;
  }

  renderEnterpriseFeatures() {
    return this.renderBox(
      'feature_type="New Feature or removal affecting enterprises" ' +
        'OR enterprise_impact>1'
    );
  }

  render() {
    return html`
      <h2>Enterprise features and breaking changes</h2>
      ${this.renderEnterpriseFeatures()}
    `;
  }
}
