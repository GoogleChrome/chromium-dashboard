import {LitElement, css, html, nothing} from 'lit';
import {customElement, state} from 'lit/decorators.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {showToastMessage} from './utils';
import {parse} from 'csv-parse/browser/esm/sync';

type Item = {
  row: number;
  entryName?: string;
  csFid: number;
  existing?: string;
  desired: string;
};

const WEB_FEATURE_ID_RE = new RegExp('^[a-z0-9]+(-[a-z0-9]+)*$');
const CHROMESTATUS_URL_RE = new RegExp(
  'https://(wwww.)?chromestatus.com/feature/(?<id>[0-9]+)'
);

@customElement('chromedash-bulk-edit-page')
export class ChromedashBulkEditPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      ...FORM_STYLES,
      css`
        section {
          margin: var(--content-padding);
        }
        .diff.old {
          background: #fdd;
        }
        .diff.new {
          background: #dfd;
        }
      `,
    ];
  }

  @state()
  parsing = false;

  @state()
  cells: string[][] = [];

  @state()
  featureIdIndex: number = -1;

  @state()
  chromestatusUrlIndex: number = -1;

  @state()
  items: Item[] = [];

  @state()
  submitting = false;

  parseChromestatusIdFromURL(url: string): number {
    const match = url.match(CHROMESTATUS_URL_RE);
    if (match) {
      return Number(match.groups?.id);
    }
    return 0;
  }

  isFeatureIdHeader(header: string, index: number) {
    const headerOk =
      header === 'feature id' ||
      header === 'web-features' ||
      (header.includes('feature') && !header.includes('chrome'));
    const firstValueOk =
      this.cells.length > 1 && this.cells[1][index].match(WEB_FEATURE_ID_RE);
    return headerOk && firstValueOk;
  }

  isChromestatusURL(header: string, index: number) {
    const headerOk =
      header.includes('chromestatus') ||
      (header.includes('chrome') && header.includes('status'));
    const firstValueOk =
      this.cells.length > 1 &&
      this.parseChromestatusIdFromURL(this.cells[1][index]);
    return headerOk && firstValueOk;
  }

  detectColumns() {
    const headerCells: string[] = this.cells[0].map(header =>
      header.toLowerCase()
    );
    this.featureIdIndex = headerCells.findIndex(
      this.isFeatureIdHeader.bind(this)
    );
    this.chromestatusUrlIndex = headerCells.findIndex(
      this.isChromestatusURL.bind(this)
    );
  }

  selectItems() {
    this.items = [];
    if (this.featureIdIndex === -1 || this.chromestatusUrlIndex === -1) {
      return;
    }
    for (let i = 1; i < this.cells.length; i++) {
      const row = this.cells[i];
      const webFeatureId: string = row[this.featureIdIndex];
      const csUrl = row[this.chromestatusUrlIndex];
      const csFid: number = this.parseChromestatusIdFromURL(csUrl);
      if (csFid > 0) {
        const item: Item = {
          row: i + 1,
          csFid: csFid,
          existing: 'Loading...',
          desired: webFeatureId,
        };
        this.items.push(item);
      }
    }
  }

  fetchFeature(item: Item): Promise<void> {
    return window.csClient.getFeature(item.csFid).then(fe => {
      item.entryName = fe.name;
      item.existing = fe.web_feature;
      this.requestUpdate(); // Render page to show progress.
    });
  }

  parseFileContent(fileContent: string) {
    this.cells = parse(fileContent);
    this.detectColumns();
    this.selectItems();
  }

  getFileAndParse() {
    const fileField = this.shadowRoot!.querySelector<HTMLInputElement>(
      '#id_file_form_field'
    );
    if (fileField && fileField.files) {
      const file = fileField.files[0];
      const reader = new FileReader();
      reader.onload = e => {
        if (e.target && e.target.result) {
          const fileContent: string = e.target.result as string;
          this.parseFileContent(fileContent);
          const promises = this.items.map(item => this.fetchFeature(item));
          Promise.all(promises).then(() => {
            this.parsing = false;
          });
        }
      };
      reader.readAsText(file);
      // TODO: Start fetching features to fill in their existing web feature ID,
      // and to replace the feature ID number with a human-readable name.
    }
  }

  saveFeature(item: Item): Promise<void> {
    const submitBody = {
      feature_changes: {
        id: item.csFid,
        web_feature: item.desired,
      },
      stages: [],
      has_changes: true,
    };
    return window.csClient
      .updateFeature(submitBody)
      .then(resp => {
        this.fetchFeature(item);
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  async handleSubmit(e: PointerEvent) {
    e.preventDefault();
    this.submitting = true;
    for (const item of this.items) {
      if (item.existing != item.desired) {
        // Save one at a time to avoid a load spike.
        await this.saveFeature(item);
      }
    }
    this.submitting = false;
  }

  handleChange() {
    this.parsing = true;
    this.getFileAndParse();
  }

  renderForm() {
    return html`
      <form name="bulk_edit_form">
        <table cellspacing="6">
          <tbody>
            <tr>
              <th>
                <label for="id_file_form_field">CSV file:</label>
              </th>
              <td>
                <input
                  id="id_file_form_field"
                  name="file_form_field"
                  type="file"
                  accept="text/csv"
                  @change=${this.handleChange}
                />
              </td>
            </tr>
          </tbody>
        </table>
      </form>
    `;
  }

  renderItemRow(item: Item) {
    const different =
      item.existing != 'Loading...' && item.existing != item.desired;
    const differentClass = different ? 'diff' : '';
    return html`
      <tr>
        <td style="text-align: right; width: 4em">${item.row}</td>
        <td>
          <a href="/feature/${item.csFid}" target="_blank"
            >${item.entryName || item.csFid}</a
          >
        </td>
        <td class="${differentClass} old">${item.existing || 'Not set'}</td>
        <td>${different ? html`&larr;` : '=='}</td>
        <td class="${differentClass} new">${item.desired}</td>
      </tr>
    `;
  }

  renderPreview() {
    if (this.items.length == 0) {
      return html`
        <p id="instructions">Select a CSV file to see the preview</p>
      `;
    }
    return html`
      <table class="data-table">
        <tr>
          <th>Row</th>
          <th>ChromeStatus feature</th>
          <th>Existing web feature ID</th>
          <th></th>
          <th>Desired web feature ID</th>
        </tr>
        ${this.items.map(item => this.renderItemRow(item))}
      </table>
    `;
  }

  renderControls() {
    return html`
      <sl-button
        ?disabled=${this.parsing || this.submitting || this.items.length == 0}
        @click=${this.handleSubmit}
        size="small"
        variant="primary"
      >
        Update all
      </sl-button>
    `;
  }

  render() {
    return html`
      <div id="subheader">
        <h2>Bulk edit</h2>
      </div>
      <section>${this.renderForm()}</section>
      <section>
        <h3>Preview</h3>
        ${this.renderPreview()}
      </section>
      <section>${this.renderControls()}</section>
      ${this.parsing || this.submitting
        ? html` <div class="loading">
            <div id="spinner"><img src="/static/img/ring.svg" /></div>
          </div>`
        : nothing}
    `;
  }
}
