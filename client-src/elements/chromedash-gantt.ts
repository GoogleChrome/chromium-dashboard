import {LitElement, TemplateResult, css, html, nothing} from 'lit';
import {customElement, property} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {Feature, StageDict} from '../js-src/cs-client.js';
import {
  STAGE_TYPES_DEV_TRIAL,
  STAGE_TYPES_ORIGIN_TRIAL,
  STAGE_TYPES_SHIPPING,
} from './form-field-enums.js';

@customElement('chromedash-gantt')
export class ChromedashGantt extends LitElement {
  @property({type: Object})
  feature!: Feature;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        :host {
          width: 600px;
        }

        label {
          display: block;
          font-weight: 500;
          margin-right: 5px;
          padding-top: var(--content-padding);
        }

        .platform-row {
          margin: var(--content-padding) 0;
        }

        .platform {
          display: inline-block;
          padding-top: 7px;
          vertical-align: top;
          width: 100px;
        }

        /* On small displays, show milestones as a bullet list. */
        .chart li {
          list-style: circle;
          margin-left: var(--content-padding);
        }

        .empty {
          display: none;
        }

        /* On large displays, show milestones as a gantt chart. */
        @media only screen and (min-width: 701px) {
          .chart {
            display: inline-grid;
            grid-auto-columns: 50px;
            grid-auto-rows: 30px;
            gap: 2px;
          }

          .chart li {
            list-style: none;
            margin-left: 0;
            height: 30px;
            overflow: visible;
            white-space: nowrap;
            padding: 4px;
            line-height: 22px;
          }

          .empty {
            display: block;
            background: #eee;
          }

          .chart .dev_trial {
            background: #cfe2f3ff;
          }

          .chart .origin_trial {
            background: #6fa8dcff;
          }

          .chart .shipping {
            background: #0b5394ff;
            color: white;
          }
        }
      `,
    ];
  }

  _isInactive() {
    const status = this.feature.browsers.chrome.status.text;
    return (
      status === 'No active development' ||
      status === 'On hold' ||
      status === 'No longer pursuing'
    );
  }

  renderChartRow(
    gridRow: number,
    first: number,
    last: number,
    sortedMilestones: number[],
    cssClass: string,
    label: string
  ) {
    const cellsOnRow: TemplateResult[] = [];
    for (let col = 0; col < sortedMilestones.length; col++) {
      const m = sortedMilestones[col];
      if (m < first || m > last) {
        cellsOnRow.push(html`
          <li
            style="grid-row: ${gridRow};
                     grid-column: ${col + 1}"
            class="empty"
          ></li>
        `);
      }
    }

    const firstCol = sortedMilestones.indexOf(first);
    const lastCol = sortedMilestones.indexOf(last);
    const span = Math.max(0, lastCol - firstCol) + 1;
    cellsOnRow.push(html`
      <li
        style="grid-row: ${gridRow};
                 grid-column: ${firstCol + 1} / span ${span}"
        class="${cssClass}"
      >
        ${label}
      </li>
    `);

    return cellsOnRow;
  }

  // Get lists of all dev trial, origin trial, and shipping stages
  // associated with the feature.
  getByStageType() {
    const dtStages: StageDict[] = [];
    const otStages: StageDict[] = [];
    const shipStages: StageDict[] = [];

    for (const stage of this.feature.stages) {
      if (STAGE_TYPES_DEV_TRIAL.has(stage.stage_type)) {
        dtStages.push(stage);
      } else if (STAGE_TYPES_ORIGIN_TRIAL.has(stage.stage_type)) {
        otStages.push(stage);
      } else if (STAGE_TYPES_SHIPPING.has(stage.stage_type)) {
        shipStages.push(stage);
      }
    }

    return [dtStages, otStages, shipStages];
  }

  renderPlatform(
    platform: string,
    platformParam: string,
    dtStages: StageDict[],
    otStages: StageDict[],
    shipStages: StageDict[],
    sortedMilestones: number[]
  ) {
    const dtStartMilestones: (number | undefined)[] = dtStages.map(
      s => s[`${platformParam}_first`]
    );
    const otStartMilestones: (number | undefined)[] = otStages.map(
      s => s[`${platformParam}_first`]
    );
    const otEndMilestones: (number | undefined)[] = otStages.map(s => {
      let maxEnd = s[`${platformParam}_last`];
      for (const e of s.extensions) {
        // Extensions only have "desktop_last" milestone values.
        if (e.desktop_last && !maxEnd) {
          maxEnd = e.desktop_last;
        } else if (e.desktop_last && maxEnd) {
          maxEnd = Math.max(maxEnd, e.desktop_last);
        }
      }
      return maxEnd;
    });
    const shipStartMilestones = shipStages.map(
      s => s[`${platformParam}_first`]
    );

    if (
      dtStartMilestones.length === 0 &&
      otStartMilestones.length === 0 &&
      shipStartMilestones.length === 0
    ) {
      return nothing;
    }
    const maxMilestone = Math.max(...sortedMilestones);

    let currentRow = 1;

    const validShipMilestones = shipStartMilestones.filter(x => x);
    const dtChartRows: (typeof nothing | TemplateResult[])[] = [];
    for (const dtMilestone of dtStartMilestones) {
      if (!dtMilestone) {
        continue;
      }
      let devTrialMilestoneLast = maxMilestone;
      // If there is a shipping milestone, Dev trial stops just before it.
      if (validShipMilestones.length > 0) {
        const shippingIndex = sortedMilestones.indexOf(
          Math.min(...validShipMilestones)
        );
        devTrialMilestoneLast = sortedMilestones[shippingIndex - 1];
      }
      dtChartRows.push(
        this.renderChartRow(
          currentRow,
          dtMilestone,
          devTrialMilestoneLast,
          sortedMilestones,
          'dev_trial',
          'Dev Trial: ' + dtMilestone
        )
      );
      currentRow++;
    }

    const otChartRows: (typeof nothing | TemplateResult[])[] = [];
    for (let i = 0; i < otStartMilestones.length; i++) {
      const otStartMilestone = otStartMilestones[i];
      const otEndMilestone = otEndMilestones[i];
      if (!otStartMilestone || !otEndMilestone) {
        continue;
      }
      otChartRows.push(
        this.renderChartRow(
          currentRow,
          otStartMilestone,
          otEndMilestone,
          sortedMilestones,
          'origin_trial',
          `Origin Trial: ${otStartMilestone} to ${otEndMilestone}`
        )
      );
      currentRow++;
    }

    const shipChartRows: (typeof nothing | TemplateResult[])[] = [];
    for (const shipMilestone of shipStartMilestones) {
      if (!shipMilestone) {
        continue;
      }
      shipChartRows.push(
        this.renderChartRow(
          currentRow,
          shipMilestone,
          maxMilestone,
          sortedMilestones,
          'shipping',
          `Shipping: ${shipMilestone}`
        )
      );
      currentRow++;
    }

    return html`
      <li class="platform-row">
        <div class="platform">${platform}</div>

        <ul class="chart" id="${platformParam}-chart">
          ${dtChartRows} ${otChartRows} ${shipChartRows}
        </ul>
      </li>
    `;
  }

  concatAllMilestones(allMilestones: (number | undefined)[], stage: StageDict) {
    if (!stage) {
      return allMilestones;
    }
    return allMilestones.concat([
      stage.desktop_first,
      stage.desktop_last,
      stage.android_first,
      stage.android_last,
      stage.ios_first,
      stage.ios_last,
      stage.webview_first,
      stage.webview_last,
    ]);
  }

  render() {
    // Don't show the visualization if there is no active development.
    // But, any milestones are available as text in the details section.
    if (!this.feature || this._isInactive()) {
      return nothing;
    }

    const [dtStages, otStages, shipStages] = this.getByStageType();

    let allMilestones: Array<number | undefined> = [];
    for (const stage of [...dtStages, ...otStages, ...shipStages]) {
      if (stage.extensions) {
        for (const extension of stage.extensions) {
          allMilestones = this.concatAllMilestones(allMilestones, extension);
        }
      }
      allMilestones = this.concatAllMilestones(allMilestones, stage);
    }
    allMilestones = allMilestones.filter(x => x);

    if (allMilestones.length == 0) {
      return html`<p>No milestones specified</p>`;
    }
    const allValidMilestones = allMilestones.filter(x => x !== undefined);
    const minMilestone = Math.min(...allValidMilestones);
    const maxMilestone = Math.max(...allValidMilestones);
    // We always show one extra after the last milestone so that the
    // "Shipped" block has room for that text.
    const milestoneRange = maxMilestone - minMilestone + 1 + 1;
    // sortedMilestones would be the list of column heading labels,
    // except that they are not shown.
    let sortedMilestones: number[] | undefined;

    if (milestoneRange <= 12) {
      // First choice:
      // Use columns for every milestone in the range min...max.
      // In python it would be range(minMilestone, maxMilestone + 1)
      sortedMilestones = Array(milestoneRange)
        .fill(minMilestone)
        .map((x, y) => x + y);
    } else {
      // Second choice:
      // Use columns for each milestone value and the one after it
      // even if that means that milestone numbers are not consecutive.
      const augmentedMilestoneSet = new Set<number>(allValidMilestones);
      for (const m of allValidMilestones) {
        augmentedMilestoneSet.add(m + 1);
      }
      sortedMilestones = Array.from(augmentedMilestoneSet).sort(
        (a, b) => a - b
      );

      if (sortedMilestones.length > 12) {
        // Third choice:
        // Use columns for exactly those milestones that are actually used
        // even if that means that milestone numbers are not consecutive.
        const milestoneSet = new Set(allValidMilestones);
        sortedMilestones = Array.from(milestoneSet).sort((a, b) => a - b);
        sortedMilestones.push(maxMilestone + 1); // After Shipped.
      }
    }

    return html`
      <label>Estimated milestones:</label>
      <ul>
        ${this.renderPlatform(
          'Desktop',
          'desktop',
          dtStages,
          otStages,
          shipStages,
          sortedMilestones
        )}
        ${this.renderPlatform(
          'Android',
          'android',
          dtStages,
          otStages,
          shipStages,
          sortedMilestones
        )}
        ${this.renderPlatform(
          'iOS',
          'ios',
          dtStages,
          otStages,
          shipStages,
          sortedMilestones
        )}
        ${this.renderPlatform(
          'Webview',
          'webview',
          dtStages,
          otStages,
          shipStages,
          sortedMilestones
        )}
      </ul>
    `;
  }
}
