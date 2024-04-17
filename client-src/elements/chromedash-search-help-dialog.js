import {LitElement, css, html} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';
import {QUERIABLE_FIELDS} from './queriable-fields.js';

let searchHelpDialogEl;

export async function openSearchHelpDialog() {
  if (!searchHelpDialogEl) {
    searchHelpDialogEl = document.createElement(
      'chromedash-search-help-dialog'
    );
    document.body.appendChild(searchHelpDialogEl);
    await searchHelpDialogEl.updateComplete;
  }
  searchHelpDialogEl.show();
}

export class ChromedashSearchHelpDialog extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        h3 {
          margin: var(--content-padding-large) 0;
        }
        section {
          margin-left: var(--content-padding);
        }
        p {
          margin: var(--content-padding-half) 0;
        }
        #dialog-content {
          max-width: 60rem;
        }
        li {
          list-style: disc;
          margin-left: var(--content-padding);
        }
      `,
    ];
  }

  show() {
    this.shadowRoot.querySelector('sl-dialog').show();
  }

  hide() {
    this.shadowRoot.querySelector('sl-dialog').hide();
  }

  renderExampleRow(terms, explanation) {
    return html`
      <tr>
        <td>${terms.map(term => html`<div><code>${term}</code></div>`)}</td>
        <td>${explanation}</td>
      </tr>
    `;
  }

  renderCommonSearchExamples() {
    return html`
      <h3>Common search examples</h3>
      <section>
        <table class="data-table">
          ${this.renderExampleRow(
            ['memory', 'memory pool', 'memory -pool'],
            'Features that include or exclude words in any field.'
          )}
          ${this.renderExampleRow(
            ['browsers.chrome.desktop=123'],
            'Features shipping in the specified milestone.'
          )}
          ${this.renderExampleRow(
            ['browsers.chrome.desktop>=120 browsers.chrome.desktop<=122'],
            'Features shipping in a milestone range.'
          )}
          ${this.renderExampleRow(
            ['owner:user@example.com'],
            'Features with the specified owner.'
          )}
          ${this.renderExampleRow(
            [
              'created.when>2024-01-01',
              'updated.when>=2023-01-01 updated.when<=2023-12-31',
            ],
            'Features created or modified before or after a date.'
          )}
          ${this.renderExampleRow(
            [
              'feature_type="Feature deprecation"',
              'feature_type!="Feature deprecation"',
              '-feature_type="Feature deprecation"',
            ],
            'Features of a specific type or excluding a type.'
          )}
          ${this.renderExampleRow(
            ['category=CSS,DOM'],
            'Features that have a value in a comma-separated list.'
          )}
          ${this.renderExampleRow(
            ['category=CSS OR category=DOM'],
            'Combine two query clauses with a logical-OR.'
          )}
        </table>
      </section>
    `;
  }

  renderSearchSyntax() {
    return html`
      <h3>Search syntax</h3>
      <section>
        <p>
          A search query consists of a series of terms that are separated by
          spaces. Terms can be single words or conditions.
        </p>

        <p>
          When searching for words, the results will include features that
          include those words in any field of the feature entry. We do not
          support searching for wildcards, partial words, punctuation, or quoted
          phrases.
        </p>

        <p>
          When searching using conditions, each condition consists of three
          parts: FIELD OPERATOR VALUE(S)
        </p>

        <ul>
          <li>FIELD: One of the fields listed below.</li>
          <li>
            OPERATOR: Usually an equals sign, but it can be an inequality for
            numeric, date, or enum fields.
          </li>
          <li>
            VALUE(S): A single word, number, date, or enum value listed below.
            If the value contains spaces, it must be inside double quotes. Use
            the equals operator with a comma-separated list to match any value
            in that list.
          </li>
        </ul>

        <p>
          You may negate any seearch term by prefixing it with a minus sign.
          Search terms are implicitly joined together by a logical-AND. However,
          you may type the keyword <code>OR</code> between terms as a logical-OR
          operator. We do not support parenthesis in queries.
        </p>
      </section>
    `;
  }

  renderFieldRow(queryField) {
    if (queryField.choices) {
      const choiceItems = Object.values(queryField.choices).map(
        c => html` <div>${queryField.name}="${c[1]}"</div> `
      );
      return html`
        <tr>
          <td>
            <code>${choiceItems}</code>
          </td>
          <td>${queryField.doc}</td>
        </tr>
      `;
    } else {
      return html`
        <tr>
          <td>
            <code>${queryField.name}=<i>${queryField.kind}</i></code>
          </td>
          <td>${queryField.doc}</td>
        </tr>
      `;
    }
  }

  renderFieldList() {
    return html`
      <h3>Available search fields</h3>
      <section>
        <table class="data-table">
          ${QUERIABLE_FIELDS.map(qf => this.renderFieldRow(qf))}
        </table>
      </section>
    `;
  }

  renderDialogContent() {
    return html`
      <div id="dialog-content">
        ${this.renderCommonSearchExamples()} ${this.renderSearchSyntax()}
        ${this.renderFieldList()}
      </div>
    `;
  }

  render() {
    return html`
      <sl-dialog
        class="missing-prereqs"
        label="Feature Search Help"
        style="--width:fit-content"
      >
        ${this.renderDialogContent()}
      </sl-dialog>
    `;
  }
}

customElements.define(
  'chromedash-search-help-dialog',
  ChromedashSearchHelpDialog
);
