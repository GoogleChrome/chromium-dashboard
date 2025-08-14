import {LitElement, css, html, nothing} from 'lit';
import {customElement, state} from 'lit/decorators.js';
import {FORM_STYLES} from '../css/forms-css.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {handleSaveChangesResponse, showToastMessage} from './utils';
import {parse} from 'csv-parse/browser/esm/sync';

type Item = {
  row: number;
  csFid: number;
  existing: string;
  desired: string;
};

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
      `,
    ];
  }

  @state()
  parsing = false;

  @state()
  cells: string[][] = [];

  @state()
  items: Item[] = [];

  @state()
  submitting = false;

  parseChromestatusIdFromURL(url: string): number {
    const parts = url.split('/');
    const idStr = parts[parts.length - 1];
    return Number(idStr);
  }

  selectItems() {
    const headerCells: string[] = this.cells[0];
    const featureIdIndex: number = headerCells.indexOf('Feature ID');
    const chromestatusUrlIndex: number = headerCells.indexOf(
      'Chrome Status Entry'
    );
    this.items = [];
    for (let i = 1; i < this.cells.length; i++) {
      const row = this.cells[i];
      const webFeatureId: string = row[featureIdIndex];
      const csUrl = row[chromestatusUrlIndex];
      const csFid: number = this.parseChromestatusIdFromURL(csUrl);
      if (csFid > 0) {
        const item: Item = {
          row: i + 1,
          csFid: csFid,
          existing: 'loading...',
          desired: webFeatureId,
        };
        this.items.push(item);
      }
    }
  }

  getFileAndParse() {
    var fileField: HTMLInputElement = this.shadowRoot!.querySelector(
      '#id_file_form_field'
    ) as HTMLInputElement;
    if (fileField && fileField.files) {
      const file = fileField.files[0];
      const reader = new FileReader();
      reader.onload = e => {
        if (e.target && e.target.result) {
          const fileContent: string = e.target.result as string;
          this.cells = parse(fileContent);
          this.selectItems();
          this.parsing = false;
        }
      };
      reader.readAsText(file);
      // TODO: Start fetching features to fill in their existing web feature ID,
      // and to replace the feature ID number with a human-readable name.
    }
  }

  handleSubmit(e) {
    e.preventDefault();
    this.submitting = true;
    console.log('submitting');
    // TODO: Implement logic to actually call the features API to make changes.
    setTimeout(() => {
      this.submitting = false;
    }, 10000);
  }

  handleChange(e) {
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
    return html`
      <tr>
        <td style="text-align: right; width: 4em">${item.row}</td>
        <td>${item.csFid}</td>
        <td>${item.existing}</td>
        <td>${item.desired}</td>
      </tr>
    `;
  }

  renderPreview() {
    if (this.items.length == 0) {
      return html` <p>Select a CSV file to see the preview</p> `;
    }
    return html`
      <table class="data-table">
        <tr>
          <th>Row</th>
          <th>ChromeStatus feature</th>
          <th>Existing web feature ID</th>
          <th>Desired web feature ID</th>
        </tr>
        ${this.items.map(item => this.renderItemRow(item))}
      </table>
    `;
  }

  renderControls() {
    return html`
      <sl-button
        ?disabled=${this.parsing || this.submitting}
        @click=${this.handleSubmit}
        size="small"
        variant="primary"
      >
        Submit
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
