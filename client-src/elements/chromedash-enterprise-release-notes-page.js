import {html, LitElement, css} from 'lit';
import {SHARED_STYLES} from '../sass/shared-css.js';
import {ENTERPRISE_FEATURE_CATEGORIES, PLATFORMS_DISPLAYNAME} from './form-field-enums.js';
import {STAGE_ENT_ROLLOUT} from './form-definition.js';
import {showToastMessage, updateURLParams, parseRawQuery} from './utils.js';

const milestoneQueryParamKey = 'milestone';

export class ChromedashEnterpriseReleaseNotesPage extends LitElement {
  static get properties() {
    return {
      currentFeatures: {type: Array},
      upcomingFeatures: {type: Array},
      features: {type: Array},
      channels: {type: Object},
      selectedMilestone: {type: Number},
    };
  }

  constructor() {
    super();
    this.currentFeatures = [];
    this.upcomingFeatures = [];
    this.features = [];
    this.channels = {};
    this.selectedMilestone = undefined;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
      :host > * {
        margin: 2rem 0;
      }

      h1 {
        font-size: 2rem;
        line-height: 2.5rem;
        margin: 0 0 0.5rem;
      }

      h2 {
        font-size: 1.5rem;
        letter-spacing: 0rem;
        line-height: 2rem;
        margin: 2rem 0 0.5rem;
        font-weight: bold;
      }

      h3 {
        margin: 16px 0;
      }

      table {
        width: 100%;
      }

      tr {
        background-color: var(--table-row-background);
      }

      th {
        background-color: var(--table-header-background);
      }
    
      table, th, td {
        border: var(--table-divider);
      }

      table th, .bold {
        font-weight: bold;
      }
  
      table th, table td {
        padding: 16px 32px;
        vertical-align: top;
      }

      ul {
        padding-inline-start: 1rem;
      }

      li {
        list-style: disc;
      }

      ul ul li {
        list-style: circle;
      }

      ul.note-details li , .summary{
        margin: 1rem 0;
      }
  
      td:not(:first-child), th:not(:first-child) {
        text-align: center;
      }`,
    ];
  }

  connectedCallback() {
    super.connectedCallback();
    Promise.all([
      window.csClient.getChannels(),
      window.csClient.searchFeatures(
        'feature_type="New Feature or removal affecting enterprises" OR breaking_change=true'),
    ]).then(([channels, {features}]) => {
      this.channels = channels;
      const queryParams = parseRawQuery(window.location.search);
      if (milestoneQueryParamKey in queryParams) {
        this.selectedMilestone = parseInt(queryParams[milestoneQueryParamKey], 10);
      } else {
        this.selectedMilestone = this.channels.stable.version;
        updateURLParams(milestoneQueryParamKey, this.selectedMilestone);
      }
      // Filter out features that don't have rollout stages.
      // Ensure that the stages are only rollout stages.
      this.features = features
        .filter(({stages}) => stages.some(s => s.stage_type === STAGE_ENT_ROLLOUT))
        .map(f => ({
          ...f,
          stages: f.stages
            .filter(s => s.stage_type === STAGE_ENT_ROLLOUT && !!s.rollout_milestone)
            .sort((a, b) => a.rollout_milestone - b.rollout_milestone)}));
    }).catch(() => {
      showToastMessage('Some errors occurred. Please refresh the page or try again later.');
    });
  }

  /**
   *  Updates currentFeatures and upcomingFeatures based on the selected milestone.
   */
  updateCurrentAndUpcomingFeatures() {
    // Features with a rollout stage in the selected milestone sorted with the highest impact.
    this.currentFeatures = this.features
      .filter(({stages}) => stages.some(s => s.rollout_milestone === this.selectedMilestone))
      .sort((a, b) => {
        // Highest impact of the stages from feature A.
        const impactA = Math.max(a.stages
          .filter(s => s.rollout_milestone === this.selectedMilestone)
          .map(s => s.rollout_impact));
        // Highest impact of the stages from feature B.
        const impactB = Math.max(b.stages
          .filter(s => s.rollout_milestone === this.selectedMilestone)
          .map(s => s.rollout_impact));
        return impactB - impactA;
      });

    // Features that are rolling out in a future milestone sorted with the closest milestone
    // first.
    this.upcomingFeatures = this.features
      .filter(({stages}) => !stages.some(s => s.rollout_milestone === this.selectedMilestone) &&
                             stages.some(s => s.rollout_milestone > this.selectedMilestone))
      .sort((a, b) => {
        const minA = Math.min(a.stages
          .filter(s => s.rollout_milestone > this.selectedMilestone)
          .map(s => s.rollout_milestone));
        const minB = Math.min(b.stages
          .filter(s => s.rollout_milestone > this.selectedMilestone)
          .map(s => s.rollout_milestone));
        return minA - minB;
      });
  }

  updateSelectedMilestone() {
    this.selectedMilestone = parseInt(this.shadowRoot.querySelector('#milestone-selector').value);
  }

  update() {
    this.updateCurrentAndUpcomingFeatures();
    if (this.selectedMilestone !== undefined) {
      updateURLParams(milestoneQueryParamKey, this.selectedMilestone);
    }
    super.update();
  }

  renderMilestoneSelector() {
    const options = [];
    for (let i = 0; i < this.selectedMilestone + 20; ++i) {
      options.push(html`<sl-option value="${i}">Chrome ${i} release summary</sl-option>`);
    }
    return html`
    <sl-select
      id="milestone-selector"
      placement="top" hoist
      size="small"
      value=${this.selectedMilestone}
      @sl-change=${this.updateSelectedMilestone}>
      ${options.map(option => option)}
    </sl-select>`;
  }

  /**
   *  Returns a checkmark or empty string depending on whether the feature is in the category.
   *  @param {!Object} feature
   *  @param {!number} category
   *  @return {string}
   */
  getFeatureMarkerForCategory(feature, category) {
    return feature.enterprise_feature_categories.includes(category.toString()) ? '✓' : '';
  }

  renderReleaseNotesSummarySection(title, features) {
    return html`
    <tr>
      <th>${title}</th>
      <th>Security / Privacy</th>
      <th>User productivity / Apps</th>
      <th>Management</th>
    </tr>
    ${features.length === 0 ?
      html`<tr><td colspan="4">Nothing</td></tr>` :
      features
        .map(f => html`
        <tr>
          <td>${f.name}</td>
          <td>
            ${this.getFeatureMarkerForCategory(
              f,
              ENTERPRISE_FEATURE_CATEGORIES['SECURITYANDPRIVACY'][0])}
          </td>
          <td>
            ${this.getFeatureMarkerForCategory(
              f,
              ENTERPRISE_FEATURE_CATEGORIES['USERPRODUCTIVITYANDAPPS'][0])}
          </td>
          <td>
            ${this.getFeatureMarkerForCategory(
              f,
              ENTERPRISE_FEATURE_CATEGORIES['MANAGEMENT'][0])}
          </td>
        </tr>
      `)}
    `;
  }

  renderReleaseNotesSummary() {
    return html`
    <table id="release-notes-summary">
      ${this.renderReleaseNotesSummarySection(
        `Chrome browser updates`,
        this.currentFeatures)}
      ${this.renderReleaseNotesSummarySection(
        `Upcoming Chrome browser updates`,
        this.upcomingFeatures)}
    </table>`;
  }

  /**
   *  Returns the title of a rollout stage based on the platforms it affects
   *  @param {!Object} stage
   *  @return {string}
   */

  getStageTitle(stage) {
    if (stage.rollout_platforms.length === 0 ||
        stage.rollout_platforms.length === Object.values(PLATFORMS_DISPLAYNAME).length) {
      return `Chrome ${stage.rollout_milestone}: `;
    }
    return `Chrome ${stage.rollout_milestone} on ` +
           `${stage.rollout_platforms.map(p => PLATFORMS_DISPLAYNAME[p]).join(', ')}: `;
  }

  renderReleaseNotesDetailsSection(title, features, shouldDisplayStageTitleInBold) {
    return html`
    <div class="note-section">
      <h2>${title}</h2>
      <ul class="note-details">
        ${features.map(f => html`
        <li>
          <strong>${f.name}</strong>
          <p class="summary">${f.summary}</p>
          <ul>
          ${f.stages.map(s => html`
            <li>
              <span class="${shouldDisplayStageTitleInBold(s.rollout_milestone,
      f.stages.map(s => s.rollout_milestone).sort()) ? 'bold' : ''}">
                ${this.getStageTitle(s)}
              </span>
              ${s.rollout_details || 'Missing details' }
            </li>`)}
          </ul>
        </li>`)}
      </ul>
    </div>`;
  }

  renderReleaseNotesDetails() {
    return html`
    ${this.renderReleaseNotesDetailsSection(
      `Chrome browser updates`, this.currentFeatures,
      m => m === this.selectedMilestone)}
    ${this.renderReleaseNotesDetailsSection(
      `Upcoming Chrome browser updates`, this.upcomingFeatures,
      (m, milestones) => milestones.find(x => x> this.selectedMilestone) === m)}`;
  }

  render() {
    return html`
      <h1>Chrome Enterprise and Education release notes</h1>
      ${this.renderMilestoneSelector()}
      ${this.renderReleaseNotesSummary()}
      ${this.renderReleaseNotesDetails()}
    `;
  }
}

customElements.define(
  'chromedash-enterprise-release-notes-page',
  ChromedashEnterpriseReleaseNotesPage);
