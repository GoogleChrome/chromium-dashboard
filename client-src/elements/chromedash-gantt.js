import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {
  STAGE_TYPES_DEV_TRIAL,
  STAGE_TYPES_ORIGIN_TRIAL,
  STAGE_TYPES_SHIPPING,
} from './form-field-enums.js';

class ChromedashGantt extends LitElement {
  static get properties() {
    return {
      feature: {type: Object},
      stableMilestone: {type: Number},
    };
  }

  constructor() {
    super();
    this.feature = {};
    this.stableMilestone = null;
    window.csClient.getChannels().then((channels) =>
      this.stableMilestone = channels['stable'].version);
  }

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

    `];
  }

  _isInactive() {
    const status = this.feature.browsers.chrome.status.text;
    return (status === 'No active development' ||
            status === 'On hold' ||
            status === 'No longer pursuing');
  }

  renderChartRow(gridRow, first, last, sortedMilestones, cssClass, label) {
    const cellsOnRow = [];
    for (let col = 0; col < sortedMilestones.length; col++) {
      const m = sortedMilestones[col];
      if (m < first || m > last) {
        cellsOnRow.push(html`
          <li style="grid-row: ${gridRow};
                     grid-column: ${col + 1}"
              class="empty"></li>
        `);
      }
    }

    const firstCol = sortedMilestones.indexOf(first);
    const lastCol = sortedMilestones.indexOf(last);
    const span = Math.max(0, lastCol - firstCol) + 1;
    cellsOnRow.push(html`
      <li style="grid-row: ${gridRow};
                 grid-column: ${firstCol + 1} / span ${span}"
          class="${cssClass}">
        ${label}
      </li>
    `);

    return cellsOnRow;
  }

  // Get lists of all dev trial, origin trial, and shipping stages
  // associated with the feature.
  getByStageType() {
    const dtStages = [];
    const otStages = [];
    const shipStages = [];

    for (const stage of this.feature.stages) {
      if (STAGE_TYPES_DEV_TRIAL.has(stage.stage_type)) {
        dtStages.push(stage);
      } else if (STAGE_TYPES_ORIGIN_TRIAL.has(stage.stage_type)) {
        otStages.push(stage);
      } else if (STAGE_TYPES_SHIPPING.has(stage.stage_type)) {
        shipStages.push(stage);
      }
    }

    // TODO(DanielRyanSmith): Fix this to support multiple stages.
    return [dtStages[0], otStages[0], shipStages[0]];
  }

  renderPlatform(
    platform, devTrialMilestone, originTrialMilestoneFirst,
    originTrialMilestoneLast, shippingMilestone,
    sortedMilestones) {
    if (!devTrialMilestone && !originTrialMilestoneFirst && !shippingMilestone) {
      return nothing;
    }
    const maxMilestone = Math.max(...sortedMilestones);

    let gridRow = 1;

    let dtChartRow = nothing;
    if (devTrialMilestone) {
      let devTrialMilestoneLast = maxMilestone;
      // If there is a shipping milestone, Dev trial stops just before it.
      if (shippingMilestone) {
        const shippingIndex = sortedMilestones.indexOf(shippingMilestone);
        devTrialMilestoneLast = sortedMilestones[shippingIndex - 1];
      }
      dtChartRow = this.renderChartRow(
        gridRow, devTrialMilestone, devTrialMilestoneLast,
        sortedMilestones, 'dev_trial',
        'Dev Trial: ' + devTrialMilestone);
      gridRow++;
    }

    let otChartRow = nothing;
    if (originTrialMilestoneFirst) {
      otChartRow = this.renderChartRow(
        gridRow, originTrialMilestoneFirst, originTrialMilestoneLast,
        sortedMilestones, 'origin_trial',
        'Origin Trial: ' + originTrialMilestoneFirst +
          ' to ' + originTrialMilestoneLast);
      gridRow++;
    }

    let shipChartRow = nothing;
    if (shippingMilestone) {
      shipChartRow = this.renderChartRow(
        gridRow, shippingMilestone, maxMilestone,
        sortedMilestones, 'shipping',
        'Shipping: ' + shippingMilestone);
      gridRow++;
    }

    return html`
       <li class="platform-row">
         <div class="platform">${platform}</div>

         <ul class="chart">
            ${dtChartRow}
            ${otChartRow}
            ${shipChartRow}
         </ul>
       </li>
    `;
  }

  render() {
    // Don't show the visualization if there is no active development.
    // But, any milestones are available as text in the details section.
    if (this._isInactive()) {
      return nothing;
    }

    const [dtStage, otStage, shipStage] = this.getByStageType();

    // TODO(DanielRyanSmith): This implementation is a fix that does not
    // account for multiple stages on the same feature. Add functionality to
    // accommodate multiples of the same stage type.
    const allMilestones = [
      dtStage?.desktop_first, dtStage?.android_first, dtStage?.ios_first, dtStage?.webview_first,
      otStage?.desktop_first, otStage?.android_first, otStage?.ios_first, otStage?.webview_first,
      otStage?.desktop_last, otStage?.android_last, otStage?.ios_last, otStage?.webview_last,
      shipStage?.desktop_first, shipStage?.android_first,
      shipStage?.ios_first, shipStage?.webview_first].filter(x => x);

    if (allMilestones.length == 0) {
      return html`<p>No milestones specified</p>`;
    }

    const minMilestone = Math.min(...allMilestones);
    const maxMilestone = Math.max(...allMilestones);
    // We always show one extra after the last milestone so that the
    // "Shipped" block has room for that text.
    const milestoneRange = (maxMilestone - minMilestone + 1) + 1;
    // sortedMilestones would be the list of column heading labels,
    // execpt that they are not shown.
    let sortedMilestones;

    if (milestoneRange <= 12) {
      // First choice:
      // Use columns for every milestone in the range min...max.
      // In python it would be range(minMilestone, maxMilestone + 1)
      sortedMilestones = Array(milestoneRange).fill(minMilestone).map(
        (x, y) => x + y);
    } else {
      // Second choice:
      // Use columns for each milestone value and the one after it
      // even if that means that milestone numbers are not consecutive.
      const augmentedMilestoneSet = new Set(allMilestones);
      for (const m of allMilestones) {
        augmentedMilestoneSet.add(m + 1);
      }
      sortedMilestones = Array.from(augmentedMilestoneSet).sort(
        (a, b) => a - b);

      if (sortedMilestones.length > 12) {
        // Third choice:
        // Use columns for exactly those milestones that are actually used
        // even if that means that milestone numbers are not consecutive.
        const milestoneSet = new Set(allMilestones);
        sortedMilestones = Array.from(milestoneSet).sort(
          (a, b) => a - b);
        sortedMilestones.push(maxMilestone + 1); // After Shipped.
      }
    }

    return html`
       <label>Estimated milestones:</label>
       <ul>
       ${this.renderPlatform('Desktop',
          dtStage?.desktop_first,
          otStage?.desktop_first,
          otStage?.desktop_last,
          shipStage?.desktop_first,
          sortedMilestones)}
       ${this.renderPlatform('Android',
          dtStage?.android_first,
          otStage?.android_first,
          otStage?.android_last,
          shipStage?.android_first,
          sortedMilestones)}
       ${this.renderPlatform('iOS',
          dtStage?.ios_first,
          otStage?.ios_first,
          otStage?.ios_last,
          shipStage?.ios_first,
          sortedMilestones)}
       ${this.renderPlatform('Webview',
          dtStage?.webview_first,
          otStage?.webview_first,
          otStage?.webview_last,
          shipStage?.webview_first,
          sortedMilestones)}
       </ul>
    `;
  }
}

customElements.define('chromedash-gantt', ChromedashGantt);
