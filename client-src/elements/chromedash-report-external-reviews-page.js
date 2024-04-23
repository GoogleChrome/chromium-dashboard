// @ts-check
import {Task} from '@lit/task';
import '@shoelace-style/shoelace';
import {LitElement, css, html, nothing} from 'lit';
import {SHARED_STYLES} from '../css/shared-css.js';

/**
 * @typedef {import('chromestatus-openapi').ExternalReviewsResponse} ExternalReviewsResponse
 * @typedef {import('chromestatus-openapi').OutstandingReview} OutstandingReview
 * @typedef {import('chromestatus-openapi').OutstandingReviewCurrentStageEnum} Stage
 */

/** Array.sort() comparison helper function ordering numbers descending and putting undefined last.
 *
 * @param {number | undefined} a
 * @param {number | undefined} b
 * @returns {number}
 */
function descendingNumberUndefinedLast(a, b) {
  if (a === b) return 0;
  if (a === undefined) return 1;
  if (b === undefined) return -1;
  return b - a;
}

/** Array.sort() comparison function to order outstanding reviews by descending urgency.
 *
 * Reviews' features must be within the same stage.
 *
 * @param {OutstandingReview} a
 * @param {OutstandingReview} b
 * @returns {number}
 */
function compareOutstandingReview(a, b) {
  console.assert(a.current_stage === b.current_stage);
  if (a.estimated_end_milestone !== b.estimated_end_milestone) {
    return descendingNumberUndefinedLast(
      a.estimated_end_milestone,
      b.estimated_end_milestone
    );
  }
  if (a.estimated_start_milestone !== b.estimated_start_milestone) {
    return descendingNumberUndefinedLast(
      a.estimated_start_milestone,
      b.estimated_start_milestone
    );
  }
  return 0;
}

export class ChromedashReportExternalReviewsPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        h2 {
          margin-top: var(--content-padding);
          margin-bottom: var(--content-padding-quarter);

          sl-skeleton {
            width: 30%;
            height: 1lh;
          }
        }
        td.feature,
        td.review {
          width: 45%;
        }
        td.milestones {
          width: 10%;
        }
      `,
    ];
  }

  static get properties() {
    return {
      reviewer: {type: String},
    };
  }

  /** @type {'tag' | 'gecko' | 'webkit'} */
  reviewer;

  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  constructor() {
    super();
    // @ts-ignore
    this._client = window.csOpenApiClient;
    this._reviewsTask = new Task(this, {
      task: async ([reviewer], {signal}) => {
        const response = await this._client.listExternalReviews(
          {reviewGroup: reviewer},
          {signal}
        );
        return {
          reviews: this.groupReviews(response.reviews),
          links: response.link_previews,
          noOutstandingReviews: response.reviews.length === 0,
        };
      },
      args: () => [this.reviewer],
    });
  }

  /**
   * @param {OutstandingReview[]} reviews
   * @returns {Record<Stage, OutstandingReview[]>}
   */
  groupReviews(reviews) {
    /** @type {Record<Stage, OutstandingReview[]>} */
    const result = {
      incubating: [],
      prototyping: [],
      'dev-trial': [],
      'wide-review': [],
      'origin-trial': [],
      shipping: [],
      shipped: [],
    };
    for (const review of reviews) {
      if (review.current_stage) {
        result[review.current_stage].push(review);
      }
    }
    for (const list of Object.values(result)) {
      list.sort(compareOutstandingReview);
    }
    return result;
  }

  headerRow() {
    return html`<tr>
      <th>Feature</th>
      <th>Review</th>
      <th>Target Milestones</th>
    </tr>`;
  }

  render() {
    return html`
      <div id="subheader">
        Reviews are in rough order of urgency, from about-to-ship down to
        incubations. Already-shipped features are listed at the bottom.
      </div>
      ${this._reviewsTask.render({
        pending: () => html`
          <h2><sl-skeleton effect="sheen"></sl-skeleton></h2>
          <table class="data-table">
            ${this.headerRow()}
            ${[1, 2, 3].map(
              () => html`
                <tr>
                  <td class="feature">
                    <sl-skeleton effect="sheen"></sl-skeleton>
                  </td>
                  <td class="review">
                    <sl-skeleton effect="sheen"></sl-skeleton>
                  </td>
                  <td class="milestones">
                    <sl-skeleton effect="sheen"></sl-skeleton>
                  </td>
                </tr>
              `
            )}
          </table>
        `,
        complete: ({reviews, links, noOutstandingReviews}) =>
          noOutstandingReviews
            ? html`No outstanding reviews. Congratulations!`
            : [
                ['Preparing to ship', 'shipping'],
                ['In Origin Trial', 'origin-trial'],
                ['Getting wide review', 'wide-review'],
                ['In developer trials', 'dev-trial'],
                ['Prototyping', 'prototyping'],
                ['Incubating', 'incubating'],
                ['Already shipped', 'shipped'],
              ].map(([title, key]) =>
                reviews[key].length > 0
                  ? html`<h2 id=${key}>${title}</h2>
                      <table class="data-table">
                        ${this.headerRow()}
                        ${reviews[key].map(
                          /** @param {OutstandingReview} review */ review => html`
                            <tr>
                              <td class="feature">
                                <a href="/feature/${review.feature.id}"
                                  >${review.feature.name}</a
                                >
                              </td>
                              <td class="review">
                                <chromedash-link
                                  href=${review.review_link}
                                  .featureLinks=${links}
                                ></chromedash-link>
                              </td>
                              <td class="milestones">
                                ${review.estimated_start_milestone
                                  ? 'M' + review.estimated_start_milestone
                                  : nothing}${['shipping', 'shipped'].includes(
                                  review.current_stage
                                )
                                  ? nothing
                                  : html`${review.estimated_start_milestone ||
                                    review.estimated_end_milestone
                                      ? '–'
                                      : nothing}${review.estimated_end_milestone
                                      ? 'M' + review.estimated_end_milestone
                                      : nothing}`}
                              </td>
                            </tr>
                          `
                        )}
                      </table>`
                  : nothing
              ),
        error: e => {
          console.error(e);
          return html`<p>
            Some errors occurred. Please refresh the page or try again later.
          </p>`;
        },
      })}
    `;
  }
}

customElements.define(
  'chromedash-report-external-reviews-page',
  ChromedashReportExternalReviewsPage
);
