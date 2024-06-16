// @ts-check
import {Task} from '@lit/task';
import '@shoelace-style/shoelace';
import {LitElement, css, html, nothing} from 'lit';
import {choose} from 'lit/directives/choose.js';
import {SHARED_STYLES} from '../css/shared-css.js';

/**
 * @typedef {import('chromestatus-openapi').ExternalReviewsResponse} ExternalReviewsResponse
 * @typedef {import('chromestatus-openapi').OutstandingReview} OutstandingReview
 * @typedef {import('chromestatus-openapi').OutstandingReviewCurrentStageEnum} Stage
 */

/** Array.sort() comparison helper function ordering numbers ascending and putting undefined last.
 *
 * @param {number | undefined} a
 * @param {number | undefined} b
 * @returns {number}
 */
function ascendingNumberUndefinedLast(a, b) {
  if (a === b) return 0;
  if (a === undefined) return 1;
  if (b === undefined) return -1;
  return a - b;
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
  console.assert(
    a.current_stage === b.current_stage,
    `Tried to compare features at stages ${a.current_stage} and ` +
      `${b.current_stage} using a function that ignores features' stages.`
  );
  if (a.estimated_end_milestone !== b.estimated_end_milestone) {
    // Lower milestones are happening sooner and so more urgent.
    return ascendingNumberUndefinedLast(
      a.estimated_end_milestone,
      b.estimated_end_milestone
    );
  }
  if (a.estimated_start_milestone !== b.estimated_start_milestone) {
    return ascendingNumberUndefinedLast(
      a.estimated_start_milestone,
      b.estimated_start_milestone
    );
  }
  // Break ties by putting review links in ascending order, which for github issues puts them in
  // order by creation time.
  if (a.review_link < b.review_link) {
    return -1;
  }
  if (a.review_link > b.review_link) {
    return 1;
  }
  return 0;
}

export class ChromedashReportExternalReviewsPage extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        #subheader {
          display: block;
        }
        h3 {
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

  /** @type {'tag' | 'gecko' | 'webkit' | undefined} */
  reviewer = undefined;

  /** @type {import('chromestatus-openapi').DefaultApiInterface} */
  _client;

  constructor() {
    super();
    // @ts-ignore
    this._client = window.csOpenApiClient;
    this._reviewsTask = new Task(this, {
      task: async ([reviewer], {signal}) => {
        if (reviewer === undefined) {
          throw new Error('Element must have "reviewer" attribute.', {
            cause: this,
          });
        }
        if (!['tag', 'gecko', 'webkit'].includes(reviewer)) {
          throw new Error(
            `Reviewer (${reviewer}) must be 'tag', 'gecko', or 'webkit'.`,
            {cause: this}
          );
        }
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

  /**
   * @param {Record<import("chromestatus-openapi").OutstandingReviewCurrentStageEnum, import("chromestatus-openapi").OutstandingReview[]>} reviews
   * @param {import('../js-src/cs-client.js').FeatureLink[]} links
   */
  renderOutstandingReviews(reviews, links) {
    return [
      ['Preparing to ship', 'shipping'],
      ['In Origin Trial', 'origin-trial'],
      ['Getting wide review', 'wide-review'],
      ['In developer trials', 'dev-trial'],
      ['Prototyping', 'prototyping'],
      ['Incubating', 'incubating'],
      ['Already shipped', 'shipped'],
    ].map(([title, key]) =>
      reviews[key].length > 0
        ? html`<section>
            <h3 id=${key}>${title}</h3>
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
            </table>
          </section>`
        : nothing
    );
  }

  render() {
    return html`
      <div id="subheader">
        <h2>
          Open
          ${choose(this.reviewer, [
            ['tag', () => html`W3C TAG`],
            ['webkit', () => html`WebKit`],
            ['gecko', () => html`Mozilla`],
          ])}
          reviews for Chromium features
        </h2>
        <p>
          Reviews are in rough order of urgency, from about-to-ship down to
          incubations. Already-shipped features are listed at the bottom.
        </p>
      </div>
      ${this._reviewsTask.render({
        pending: () => html`
          <section>
            <h3><sl-skeleton effect="sheen"></sl-skeleton></h3>
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
          </section>
        `,
        complete: ({reviews, links, noOutstandingReviews}) =>
          noOutstandingReviews
            ? html`No outstanding reviews. Congratulations!`
            : this.renderOutstandingReviews(reviews, links),
        error: e => {
          console.error(`Couldn't fetch ${this.reviewer}'s reviews: `, e);
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
