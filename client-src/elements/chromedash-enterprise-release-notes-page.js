import {html, LitElement, css} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  ENTERPRISE_FEATURE_CATEGORIES,
  PLATFORM_CATEGORIES,
  PLATFORMS_DISPLAYNAME,
  STAGE_ENT_ROLLOUT,
  STAGE_TYPES_SHIPPING,
} from './form-field-enums.js';
import {
  showToastMessage,
  updateURLParams,
  parseRawQuery,
  renderHTMLIf,
} from './utils.js';

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

        table,
        th,
        td {
          border: var(--table-divider);
        }

        table th,
        .bold {
          font-weight: bold;
        }

        table th,
        table td {
          padding: 16px 32px;
          vertical-align: top;
        }

        ul {
          padding-inline-start: 1rem;
        }

        li {
          list-style: circle;
          margin-block-end: 16px;
        }

        .feature {
          margin: 1rem 0 2rem;
        }

        .feature p {
          margin: 1rem 0;
        }

        .toremove {
          font-style: italic;
          font-weight: bold;
        }

        td:not(:first-child),
        th:not(:first-child) {
          text-align: center;
        }

        .screenshots {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .screenshots img {
          flex: 0 1 auto;
          max-height: 300px;
          max-width: calc(50% - 0.5rem);
        }
      `,
    ];
  }

  convertShippingStageToRolloutStages(stage) {
    const milestones = [
      stage.desktop_first,
      stage.android_first,
      stage.ios_first,
      stage.webview_first,
      stage.desktop_last,
      stage.android_last,
      stage.ios_last,
      stage.webview_last,
    ];
    const milestoneAndPlatformsMap = milestones.reduce(
      (acc, milestone) => ({...acc, [milestone]: new Set()}),
      {}
    );

    if (stage.desktop_first) {
      milestoneAndPlatformsMap[stage.desktop_first].add(
        PLATFORM_CATEGORIES['PLATFORM_WINDOWS'][0]
      );
      milestoneAndPlatformsMap[stage.desktop_first].add(
        PLATFORM_CATEGORIES['PLATFORM_MAC'][0]
      );
      milestoneAndPlatformsMap[stage.desktop_first].add(
        PLATFORM_CATEGORIES['PLATFORM_LINUX'][0]
      );
    }
    if (stage.android_first) {
      milestoneAndPlatformsMap[stage.android_first].add(
        PLATFORM_CATEGORIES['PLATFORM_ANDROID'][0]
      );
    }
    if (stage.ios_first) {
      milestoneAndPlatformsMap[stage.ios_first].add(
        PLATFORM_CATEGORIES['PLATFORM_IOS'][0]
      );
    }
    if (stage.webview_first) {
      milestoneAndPlatformsMap[stage.webview_first].add(
        PLATFORM_CATEGORIES['PLATFORM_ANDROID'][0]
      );
    }
    if (stage.desktop_last) {
      milestoneAndPlatformsMap[stage.desktop_last].add(
        PLATFORM_CATEGORIES['PLATFORM_WINDOWS'][0]
      );
      milestoneAndPlatformsMap[stage.desktop_last].add(
        PLATFORM_CATEGORIES['PLATFORM_MAC'][0]
      );
      milestoneAndPlatformsMap[stage.desktop_last].add(
        PLATFORM_CATEGORIES['PLATFORM_LINUX'][0]
      );
    }
    if (stage.android_last) {
      milestoneAndPlatformsMap[stage.android_last].add(
        PLATFORM_CATEGORIES['PLATFORM_ANDROID'][0]
      );
    }
    if (stage.ios_last) {
      milestoneAndPlatformsMap[stage.ios_last].add(
        PLATFORM_CATEGORIES['PLATFORM_IOS'][0]
      );
    }
    if (stage.webview_last) {
      milestoneAndPlatformsMap[stage.webview_last].add(
        PLATFORM_CATEGORIES['PLATFORM_ANDROID'][0]
      );
    }
    return Object.entries(milestoneAndPlatformsMap).map(
      ([milestone, platforms]) => ({
        stage_type: STAGE_ENT_ROLLOUT,
        rollout_milestone: Number(milestone),
        rollout_platforms: Array.from(platforms),
        rollout_impact: 1,
      })
    );
  }

  updateFeatures(features) {
    // Simulate rollout stage for features with breaking changes and planned
    // milestones but without rollout stages so that they appear on the release
    // notes.
    const featuresRequiringRolloutStages = features
      .filter(
        ({stages}) =>
          !stages.some(s => s.stage_type === STAGE_ENT_ROLLOUT) &&
          stages.some(s => STAGE_TYPES_SHIPPING.has(s.stage_type))
      )
      .map(f => ({
        ...f,
        stages: f.stages
          .filter(s => STAGE_TYPES_SHIPPING.has(s.stage_type))
          .map(this.convertShippingStageToRolloutStages)
          .flatMap(x => x),
      }));

    // Filter out features that don't have rollout stages.
    // Ensure that the stages are only rollout stages.
    this.features = [...features, ...featuresRequiringRolloutStages]
      .filter(({stages}) =>
        stages.some(s => s.stage_type === STAGE_ENT_ROLLOUT)
      )
      .map(f => ({
        ...f,
        stages: f.stages
          .filter(
            s => s.stage_type === STAGE_ENT_ROLLOUT && !!s.rollout_milestone
          )
          .sort((a, b) => a.rollout_milestone - b.rollout_milestone),
      }));

    // Features with a rollout stage in the selected milestone sorted with the highest impact.
    this.currentFeatures = this.features
      .filter(({stages}) =>
        stages.some(s => s.rollout_milestone === this.selectedMilestone)
      )
      .sort((a, b) => {
        // Highest impact of the stages from feature A.
        const impactA = Math.max(
          a.stages
            .filter(s => s.rollout_milestone === this.selectedMilestone)
            .map(s => s.rollout_impact)
        );
        // Highest impact of the stages from feature B.
        const impactB = Math.max(
          b.stages
            .filter(s => s.rollout_milestone === this.selectedMilestone)
            .map(s => s.rollout_impact)
        );
        return impactB - impactA;
      });

    // Features that are rolling out in a future milestone sorted with the closest milestone
    // first.
    this.upcomingFeatures = this.features
      .filter(
        ({stages}) =>
          !stages.some(s => s.rollout_milestone === this.selectedMilestone) &&
          stages.some(s => s.rollout_milestone > this.selectedMilestone)
      )
      .sort((a, b) => {
        const minA =
          Math.min(
            a.stages
              .filter(s => (s.rollout_milestone || 0) > this.selectedMilestone)
              .map(s => s.rollout_milestone)
          ) || 0;
        const minB =
          Math.min(
            b.stages
              .filter(s => (s.rollout_milestone || 0) > this.selectedMilestone)
              .map(s => s.rollout_milestone)
          ) || 0;
        return minA - minB;
      });
  }

  connectedCallback() {
    window.csClient
      .getChannels()
      .then(channels => {
        this.channels = channels;
        const queryParams = parseRawQuery(window.location.search);
        if (milestoneQueryParamKey in queryParams) {
          this.selectedMilestone = parseInt(
            queryParams[milestoneQueryParamKey],
            10
          );
        } else {
          this.selectedMilestone = this.channels.stable.version;
          updateURLParams(milestoneQueryParamKey, this.selectedMilestone);
        }
      })
      .then(() =>
        window.csClient.getFeaturesForEnterpriseReleaseNotes(
          this.selectedMilestone
        )
      )
      .then(({features}) => this.updateFeatures(features))
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      })
      .finally(() => super.connectedCallback());
  }

  updateSelectedMilestone() {
    this.selectedMilestone = parseInt(
      this.shadowRoot.querySelector('#milestone-selector').value
    );
    window.csClient
      .getFeaturesForEnterpriseReleaseNotes(this.selectedMilestone)
      .then(({features}) => this.updateFeatures(features))
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  update() {
    if (this.selectedMilestone !== undefined) {
      updateURLParams(milestoneQueryParamKey, this.selectedMilestone);
    }
    super.update();
  }

  renderMilestoneSelector() {
    const options = [];
    for (let i = 0; i < this.selectedMilestone + 20; ++i) {
      options.push(
        html`<sl-option value="${i}">Chrome ${i} release summary</sl-option>`
      );
    }
    return html` <sl-select
      id="milestone-selector"
      placement="top"
      hoist
      size="small"
      value=${this.selectedMilestone}
      @sl-change=${this.updateSelectedMilestone}
    >
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
    return feature.enterprise_feature_categories.includes(category.toString())
      ? '✓'
      : '';
  }

  renderReleaseNotesSummarySection(title, features) {
    return html`
      <tr>
        <th>${title}</th>
        <th>Security / Privacy</th>
        <th>User productivity / Apps</th>
        <th>Management</th>
      </tr>
      ${features.length === 0
        ? html`<tr>
            <td colspan="4">Nothing</td>
          </tr>`
        : features.map(
            f => html`
              <tr>
                <td>${f.name}</td>
                <td>
                  ${this.getFeatureMarkerForCategory(
                    f,
                    ENTERPRISE_FEATURE_CATEGORIES['SECURITYANDPRIVACY'][0]
                  )}
                </td>
                <td>
                  ${this.getFeatureMarkerForCategory(
                    f,
                    ENTERPRISE_FEATURE_CATEGORIES['USERPRODUCTIVITYANDAPPS'][0]
                  )}
                </td>
                <td>
                  ${this.getFeatureMarkerForCategory(
                    f,
                    ENTERPRISE_FEATURE_CATEGORIES['MANAGEMENT'][0]
                  )}
                </td>
              </tr>
            `
          )}
    `;
  }

  renderReleaseNotesSummary() {
    return html` <table id="release-notes-summary">
      ${this.renderReleaseNotesSummarySection(
        'Chrome browser updates',
        this.currentFeatures
      )}
      ${this.renderReleaseNotesSummarySection(
        'Upcoming Chrome browser updates',
        this.upcomingFeatures
      )}
    </table>`;
  }

  /**
   *  Returns the title of a rollout stage based on the platforms it affects
   *  @param {!Object} stage
   *  @return {string}
   */

  getStageTitle(stage) {
    if (
      stage.rollout_platforms.length === 0 ||
      stage.rollout_platforms.length ===
        Object.values(PLATFORMS_DISPLAYNAME).length
    ) {
      return `Chrome ${stage.rollout_milestone}`;
    }
    return (
      `Chrome ${stage.rollout_milestone} on ` +
      `${stage.rollout_platforms.map(p => PLATFORMS_DISPLAYNAME[p]).join(', ')}`
    );
  }

  renderReleaseNotesDetailsSection(
    title,
    features,
    shouldDisplayStageTitleInBold
  ) {
    // Each feature has a "To remove" line that contains the feature's owners and last update date.
    // That line is to be removed by whomever copy/pastes the content into the final release notes.
    return html` <div class="note-section">
      <h2>${title}</h2>
      ${features.map(
        f =>
          html` <section class="feature">
            <strong>${f.name}</strong>
            <p class="toremove">
              < To remove -
              <a target="_blank" href="/feature/${f.id}">Feature details</a> -
              Owners: ${f.browsers.chrome.owners.join(', ')} - Editors:
              ${(f.editors || []).join(', ')} - First Notice:
              ${f.first_enterprise_notification_milestone} - Last Updated:
              ${f.updated.when} >
            </p>
            <p class="summary preformatted">${f.summary}</p>
            <ul>
              ${f.stages.map(
                s =>
                  html` <li>
                    <span
                      class="${shouldDisplayStageTitleInBold(
                        s.rollout_milestone,
                        f.stages.map(s => s.rollout_milestone).sort()
                      )
                        ? 'bold'
                        : ''}"
                    >
                      ${this.getStageTitle(s)}
                    </span>
                    ${renderHTMLIf(
                      s.rollout_details,
                      html`<br /><span class="preformatted"
                          >${s.rollout_details}</span
                        >`
                    )}
                  </li>`
              )}
            </ul>
            <div class="screenshots">
              ${f.screenshot_links.map(
                (url, i) =>
                  html`<img src="${url}" alt="Feature screenshot ${i + 1}" />`
              )}
            </div>
          </section>`
      )}
    </div>`;
  }

  renderReleaseNotesDetails() {
    return html` ${this.renderReleaseNotesDetailsSection(
      'Chrome browser updates',
      this.currentFeatures,
      m => m === this.selectedMilestone
    )}
    ${this.renderReleaseNotesDetailsSection(
      'Upcoming Chrome browser updates',
      this.upcomingFeatures,
      (m, milestones) =>
        milestones.find(x => parseInt(x) > parseInt(this.selectedMilestone)) ===
        m
    )}`;
  }

  render() {
    return html`
      <h1>Chrome Enterprise and Education release notes</h1>
      ${this.renderMilestoneSelector()} ${this.renderReleaseNotesSummary()}
      ${this.renderReleaseNotesDetails()}
    `;
  }
}

customElements.define(
  'chromedash-enterprise-release-notes-page',
  ChromedashEnterpriseReleaseNotesPage
);
