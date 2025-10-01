import {css, html, LitElement, TemplateResult} from 'lit';
import {customElement, state, property} from 'lit/decorators.js';
import {ifDefined} from 'lit/directives/if-defined.js';
import {
  SlTextarea,
  SlInput,
  SlSelect,
  SlCheckbox,
} from '@shoelace-style/shoelace';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, User, StageDict} from '../js-src/cs-client.js';
import {
  ENTERPRISE_FEATURE_CATEGORIES,
  ENTERPRISE_PRODUCT_CATEGORY,
  ENTERPRISE_IMPACT_DISPLAYNAME,
  PLATFORM_CATEGORIES,
  PLATFORMS_DISPLAYNAME,
  STAGE_ENT_ROLLOUT,
  STAGE_TYPES_SHIPPING,
} from './form-field-enums.js';
import {
  autolink,
  FieldInfo,
  formatFeatureChanges,
  parseRawQuery,
  renderHTMLIf,
  renderRelativeDate,
  showToastMessage,
  updateURLParams,
} from './utils.js';

const milestoneQueryParamKey = 'milestone';

interface Channels {
  stable: {
    version: number;
  };
}

// A simple interface for any Shoelace element that has a .value
interface ValueElement {
  value: string | string[] | undefined;
  checked?: boolean;
  tagName: string;
}

@customElement('chromedash-enterprise-release-notes-page')
export class ChromedashEnterpriseReleaseNotesPage extends LitElement {
  @property({attribute: false})
  user!: User;
  @state()
  currentChromeBrowserUpdates: Feature[] = [];
  @state()
  upcomingChromeBrowserUpdates: Feature[] = [];
  @state()
  currentChromeEnterpriseCore: Feature[] = [];
  @state()
  upcomingChromeEnterpriseCore: Feature[] = [];
  @state()
  currentChromeEnterprisePremium: Feature[] = [];
  @state()
  upcomingChromeEnterprisePremium: Feature[] = [];
  @state()
  features: Feature[] = [];
  @state()
  channels!: Channels;
  @state()
  selectedMilestone?: number;
  @state()
  editingFeatureIds = new Set<number>();

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

        .stages li {
          margin-block-end: 16px;
        }

        .feature {
          margin: 1rem 0 2rem;
          background: var(--card-background);
          border: var(--card-border);
          border-radius: var(--default-border-radius);
          box-shadow: var(--card-box-shadow);
          padding: var(--content-padding);
        }

        .feature p {
          margin: 1rem 0;
        }

        .confidential {
          background: var(--warning-background);
          padding: var(--content-padding-quarter) var(--content-padding-half);
          border-radius: var(--pill-border-radius);
        }

        .toremove {
          font-style: italic;
        }

        td:not(:first-child),
        th:not(:first-child) {
          text-align: center;
        }

        .edit-button {
          float: right;
        }
        .feature-summary {
          margin-bottom: var(--content-padding);
        }
        .rollout-milestone {
          width: 6em;
        }
        .rollout-platforms {
          margin-left: 2em;
          flex-grow: 1;
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

  convertShippingStageToRolloutStages(stage): Partial<StageDict>[] {
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
    const milestoneAndPlatformsMap: Record<
      number,
      Set<number>
    > = milestones.reduce(
      (acc, milestone) => ({...acc, [milestone]: new Set<number>()}),
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
        rollout_platforms: Array.from(platforms).map(String),
      })
    );
  }

  convertFeatureShippingStagesToRolloutStages(f: Feature): Feature {
    const rollouts: StageDict[] = f.stages.filter(
      s => s.stage_type === STAGE_ENT_ROLLOUT
    );
    const converted: StageDict[] = f.stages
      .filter(s => STAGE_TYPES_SHIPPING.has(s.stage_type))
      .map(s => this.convertShippingStageToRolloutStages(s) as StageDict[])
      .flatMap(x => x);

    let newStages = rollouts.length > 0 ? rollouts : converted;
    newStages = newStages.filter(s => !!s.rollout_milestone);
    newStages = newStages.sort(
      (a, b) => a.rollout_milestone! - b.rollout_milestone!
    );

    return {
      ...f,
      stages: newStages,
    };
  }

  updateFeatures(features) {
    features = features.map(f =>
      this.convertFeatureShippingStagesToRolloutStages(f)
    );

    // Filter out features that don't have rollout stages.
    // Ensure that the stages are only rollout stages.
    this.features = features.filter(({stages}) =>
      stages.some(s => s.stage_type === STAGE_ENT_ROLLOUT)
    );

    this.categorizeFeatures();
  }

  categorizeFeatures() {
    // Features with a rollout stage in the selected milestone sorted with the highest impact.
    const currentFeatures = this.features
      .filter(({stages}) =>
        stages.some(s => s.rollout_milestone === this.selectedMilestone)
      )
      .sort((a, b) => {
        // Descending order
        return b.enterprise_impact - a.enterprise_impact;
      });

    this.currentChromeBrowserUpdates = currentFeatures.filter(
      f =>
        f.enterprise_product_category ===
        ENTERPRISE_PRODUCT_CATEGORY.CHROME_BROWSER_UPDATE[0]
    );
    this.currentChromeEnterpriseCore = currentFeatures.filter(
      f =>
        f.enterprise_product_category ===
        ENTERPRISE_PRODUCT_CATEGORY.CHROME_ENTERPRISE_CORE[0]
    );
    this.currentChromeEnterprisePremium = currentFeatures.filter(
      f =>
        f.enterprise_product_category ===
        ENTERPRISE_PRODUCT_CATEGORY.CHROME_ENTERPRISE_PREMIUM[0]
    );

    // Features that are rolling out in a future milestone sorted with the closest milestone
    // first.
    const upcomingFeatures = this.features
      .filter(
        ({stages}) =>
          !stages.some(s => s.rollout_milestone === this.selectedMilestone) &&
          stages.some(s => s.rollout_milestone! > this.selectedMilestone!)
      )
      .sort((a, b) => {
        const minA =
          Math.min(
            ...a.stages
              .filter(
                s => (s.rollout_milestone! || 0) > this.selectedMilestone!
              )
              .map(s => s.rollout_milestone!)
          ) || 0;
        const minB =
          Math.min(
            ...b.stages
              .filter(
                s => (s.rollout_milestone! || 0) > this.selectedMilestone!
              )
              .map(s => s.rollout_milestone!)
          ) || 0;
        return minA - minB;
      });
    this.upcomingChromeBrowserUpdates = upcomingFeatures.filter(
      f =>
        f.enterprise_product_category ===
        ENTERPRISE_PRODUCT_CATEGORY.CHROME_BROWSER_UPDATE[0]
    );
    this.upcomingChromeEnterpriseCore = upcomingFeatures.filter(
      f =>
        f.enterprise_product_category ===
        ENTERPRISE_PRODUCT_CATEGORY.CHROME_ENTERPRISE_CORE[0]
    );
    this.upcomingChromeEnterprisePremium = upcomingFeatures.filter(
      f =>
        f.enterprise_product_category ===
        ENTERPRISE_PRODUCT_CATEGORY.CHROME_ENTERPRISE_PREMIUM[0]
    );
  }

  replaceOneFeature(revisedFeature: Feature) {
    const revisedList = this.features.map(f =>
      f.id === revisedFeature.id ? revisedFeature : f
    );
    this.features = revisedList;
    this.categorizeFeatures();
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
    const milestoneSelector = this.shadowRoot!.querySelector(
      '#milestone-selector'
    ) as HTMLSelectElement;
    this.selectedMilestone = parseInt(milestoneSelector.value);
    window.csClient
      .getFeaturesForEnterpriseReleaseNotes(this.selectedMilestone)
      .then(({features}) => this.updateFeatures(features))
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  update(changedProperties: Map<string | number | symbol, unknown>) {
    if (this.selectedMilestone !== undefined) {
      updateURLParams(milestoneQueryParamKey, this.selectedMilestone);
    }
    super.update(changedProperties);
  }

  renderMilestoneSelector() {
    const options: TemplateResult[] = [];
    for (let i = 0; i < this.selectedMilestone! + 20; ++i) {
      options.push(
        html`<sl-option value="${i}">Chrome ${i} release summary</sl-option>`
      );
    }
    return html` <sl-select
      id="milestone-selector"
      placement="top"
      hoist
      size="small"
      value=${this.selectedMilestone!}
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
        'Chrome Browser updates',
        this.currentChromeBrowserUpdates
      )}
      ${this.renderReleaseNotesSummarySection(
        'Chrome Enterprise Core (CEC)',
        this.currentChromeEnterpriseCore
      )}
      ${this.renderReleaseNotesSummarySection(
        'Chrome Enterprise Premium (CEP, paid SKU)',
        this.currentChromeEnterprisePremium
      )}
      ${this.renderReleaseNotesSummarySection(
        'Upcoming Chrome Browser updates',
        this.upcomingChromeBrowserUpdates
      )}
      ${this.renderReleaseNotesSummarySection(
        'Upcoming Chrome Enterprise Core (CEC)',
        this.upcomingChromeEnterpriseCore
      )}
      ${this.renderReleaseNotesSummarySection(
        'Upcoming Chrome Enterprise Premium (CEP, paid SKU)',
        this.upcomingChromeEnterprisePremium
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

  userCanEdit(f: Feature) {
    return (
      this.user &&
      (this.user.can_edit_all || this.user.editable_features.includes(f.id))
    );
  }

  startEditing(featureId) {
    const newEditing = new Set(this.editingFeatureIds);
    newEditing.add(featureId);
    this.editingFeatureIds = newEditing;
  }

  cancel(featureId) {
    const newEditing = new Set(this.editingFeatureIds);
    newEditing.delete(featureId);
    this.editingFeatureIds = newEditing;
  }

  nowString() {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('en-CA', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
      hour12: false,
      timeZone: 'UTC',
    });
    let nowStr = formatter.format(now); // YYYY-MM-DD, HH:mm:ss
    nowStr = nowStr.replace(',', '');
    return nowStr;
  }

  save(f: Feature) {
    const fieldValues: FieldInfo[] = [];
    const addFieldValue = (
      name: string,
      el: ValueElement,
      originalValue: string | string[] | number | boolean | undefined,
      stage?: StageDict
    ) => {
      const value = el?.tagName === 'SL-CHECKBOX' ? el?.checked : el?.value;
      if (value !== undefined && '' + value != '' + originalValue) {
        fieldValues.push({name, value, touched: true, stageId: stage?.id});
      }
    };
    let nameEl: SlTextarea = this.shadowRoot?.querySelector<SlTextarea>(
      '#edit-name-' + f.id
    )!;
    addFieldValue('name', nameEl, f.name);
    let confidentialEl: SlCheckbox = this.shadowRoot?.querySelector<SlCheckbox>(
      '#edit-confidential-' + f.id
    )!;
    addFieldValue('confidential', confidentialEl, f.confidential);
    let summaryEl: SlTextarea = this.shadowRoot?.querySelector<SlTextarea>(
      '#edit-feature-' + f.id
    )!;
    addFieldValue('summary', summaryEl, f.summary);

    for (const s of f.stages) {
      if (s.id) {
        const milestoneEl = this.shadowRoot?.querySelector<SlInput>(
          '#edit-rollout-milestone-' + s.id
        )!;
        addFieldValue('rollout_milestone', milestoneEl, s.rollout_milestone, s);
        const platformsEl = this.shadowRoot?.querySelector<SlSelect>(
          '#edit-rollout-platforms-' + s.id
        )!;
        addFieldValue('rollout_platforms', platformsEl, s.rollout_platforms, s);
        const detailsEl = this.shadowRoot?.querySelector<SlInput>(
          '#edit-rollout-details-' + s.id
        )!;
        addFieldValue('rollout_details', detailsEl, s.rollout_details, s);
      }
    }

    const submitBody = formatFeatureChanges(fieldValues, f.id);
    window.csClient
      .updateFeature(submitBody)
      .then(resp => {
        window.csClient.getFeature(f.id).then(resp2 => {
          this.replaceOneFeature(
            this.convertFeatureShippingStagesToRolloutStages(resp2 as Feature)
          );
        });
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      })
      .finally(() => {
        this.cancel(f.id);
      });
  }

  renderToRemoveParagraph(f: Feature): TemplateResult {
    return html`
      <p class="toremove">
        <b>< To remove</b>
        - <a target="_blank" href="/feature/${f.id}">Feature details</a> -
        <b>Owners:</b> ${f.browsers.chrome.owners?.join(', ')} -
        <b>Editors:</b> ${(f.editors || []).join(', ')} -
        <b>Enterprise impact:</b> ${ENTERPRISE_IMPACT_DISPLAYNAME[
          f.enterprise_impact
        ]}
        - <b>First notice:</b> ${f.first_enterprise_notification_milestone} -
        <b>Last updated:</b>
        <a
          href="/feature/${f.id}/activity"
          target="_blank"
          title=${ifDefined(f.updated.when)}
        >
          ${renderRelativeDate(f.updated.when)}
        </a>
        by ${f.updated.by}
        <b>></b>
      </p>
    `;
  }

  renderEditButton(f: Feature): TemplateResult {
    if (this.userCanEdit(f) && !this.editingFeatureIds.has(f.id)) {
      return html`
        <sl-button
          @click=${() => {
            this.startEditing(f.id);
          }}
          class="edit-button"
          size="small"
          >Edit</sl-button
        >
      `;
    }
    return html``;
  }

  renderConfidential(f: Feature): TemplateResult {
    if (f.confidential) {
      return html`<span class="confidential"><strong>CONFIDENTIAL</strong></div>`;
    } else {
      return html``;
    }
  }

  renderEditableConfidential(f: Feature): TemplateResult {
    return html`
      <sl-checkbox
        class="feature-confidential"
        id="edit-confidential-${f.id}"
        ?checked=${f.confidential}
        size="small"
      >
        Confidential
      </sl-checkbox>
    `;
  }

  renderFeatureName(f: Feature): TemplateResult {
    return html`<strong>${f.name}</strong>`;
  }

  renderEditableFeatureName(f: Feature): TemplateResult {
    return html`
      <sl-input
        class="feature-name"
        id="edit-name-${f.id}"
        value=${f.name}
        size="small"
      >
      </sl-input>
    `;
  }

  renderFeatureSummary(f: Feature): TemplateResult {
    const isMarkdown = (f.markdown_fields || []).includes('summary');
    const markup = autolink(f.summary, [], isMarkdown);
    if (isMarkdown) {
      return html`${markup}`;
    } else {
      return html`<p class="summary preformatted">${markup}</p>`;
    }
  }

  renderEditableFeatureSummary(f: Feature): TemplateResult {
    return html`
    <sl-textarea
    class="feature-summary""
        id="edit-feature-${f.id}"
        value=${f.summary}
        size="small"
        resize="auto"
      >
      </sl-textarea>
    `;
  }

  renderEditableStageItem(
    f: Feature,
    s,
    shouldDisplayStageTitleInBold
  ): TemplateResult {
    // TODO(jrobbins): Implement editing widgets in the next CL.
    const platforms: string[] = s.rollout_platforms;
    const choices = PLATFORM_CATEGORIES;
    const availableOptions = Object.values(choices).filter(
      ([value, label, obsolete]) => !obsolete || platforms.includes('' + value)
    );

    return html`
      <li>
        <div class="hbox">
          <sl-input
            class="rollout-milestone"
            id="edit-rollout-milestone-${s.id}"
            type="number"
            value=${s.rollout_milestone}
          ></sl-input>

          <sl-select
            class="rollout-platforms"
            multiple
            clearable
            id="edit-rollout-platforms-${s.id}"
            .value=${platforms}
          >
            ${availableOptions.map(
              ([value, label]) => html`
                <sl-option value="${value}"> ${label} </sl-option>
              `
            )}
          </sl-select>
        </div>
        <sl-input
          class="rollout-details"
          id="edit-rollout-details-${s.id}"
          value=${s.rollout_details}
        ></sl-input>
      </li>
    `;
  }

  renderStageItem(
    f: Feature,
    s,
    shouldDisplayStageTitleInBold
  ): TemplateResult {
    return html`
      <li>
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
          html`<br /><span class="preformatted">${s.rollout_details}</span>`
        )}
      </li>
    `;
  }

  renderSaveAndCancel(f: Feature): TemplateResult {
    if (this.editingFeatureIds.has(f.id)) {
      return html`
        <sl-button
          class="save-button"
          @click=${() => {
            this.save(f);
          }}
          size="small"
          variant="primary"
          >Save</sl-button
        >
        <sl-button
          class="cancel-button"
          @click=${() => {
            this.cancel(f.id);
          }}
          size="small"
          >Cancel</sl-button
        >
      `;
    }
    return html``;
  }

  renderFeatureReleaseNote(f: Feature, shouldDisplayStageTitleInBold) {
    const isEditing = this.editingFeatureIds.has(f.id);
    return html` <section class="feature">
      ${this.renderEditButton(f)}
      ${isEditing
        ? this.renderEditableConfidential(f)
        : this.renderConfidential(f)}
      ${isEditing
        ? this.renderEditableFeatureName(f)
        : this.renderFeatureName(f)}
      ${this.renderToRemoveParagraph(f)}
      ${isEditing
        ? this.renderEditableFeatureSummary(f)
        : this.renderFeatureSummary(f)}
      <ul class="stages">
        ${f.stages.map(s =>
          isEditing && s.id
            ? this.renderEditableStageItem(f, s, shouldDisplayStageTitleInBold)
            : this.renderStageItem(f, s, shouldDisplayStageTitleInBold)
        )}
      </ul>
      ${this.renderSaveAndCancel(f)}

      <div class="screenshots">
        ${f.screenshot_links.map(
          (url, i) =>
            html`<img src="${url}" alt="Feature screenshot ${i + 1}" />`
        )}
      </div>
    </section>`;
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
      ${features.map(f =>
        this.renderFeatureReleaseNote(f, shouldDisplayStageTitleInBold)
      )}
    </div>`;
  }

  renderReleaseNotesDetails() {
    return html` ${this.renderReleaseNotesDetailsSection(
      'Chrome Browser updates',
      this.currentChromeBrowserUpdates,
      m => m === this.selectedMilestone
    )}
    ${this.renderReleaseNotesDetailsSection(
      'Chrome Enterprise Core (CEC)',
      this.currentChromeEnterpriseCore,
      m => m === this.selectedMilestone
    )}
    ${this.renderReleaseNotesDetailsSection(
      'Chrome Enterprise Premium (CEP, paid SKU)',
      this.currentChromeEnterprisePremium,
      m => m === this.selectedMilestone
    )}
    ${this.renderReleaseNotesDetailsSection(
      'Upcoming Chrome Browser updates',
      this.upcomingChromeBrowserUpdates,
      (m, milestones) =>
        milestones.find(x => parseInt(x) > this.selectedMilestone!) === m
    )}
    ${this.renderReleaseNotesDetailsSection(
      'Upcoming Chrome Enterprise Core (CEC)',
      this.upcomingChromeEnterpriseCore,
      (m, milestones) =>
        milestones.find(x => parseInt(x) > this.selectedMilestone!) === m
    )}
    ${this.renderReleaseNotesDetailsSection(
      'Upcoming Chrome Enterprise Premium (CEP, paid SKU)',
      this.upcomingChromeEnterprisePremium,
      (m, milestones) =>
        milestones.find(x => parseInt(x) > this.selectedMilestone!) === m
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
