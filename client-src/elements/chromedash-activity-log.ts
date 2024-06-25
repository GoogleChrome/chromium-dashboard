import {LitElement, css, html, nothing} from 'lit';
import {property, state} from 'lit/decorators.js';
import {autolink, renderAbsoluteDate, renderRelativeDate} from './utils.js';
import '@polymer/iron-icon';
import {ChromeStatusClient} from '../js-src/cs-client.js';
import {SHARED_STYLES} from '../css/shared-css.js';

interface Amendment {
  field_name: string;
  old_value: string;
  new_value: string;
}

declare global {
  interface Window {
    csClient: ChromeStatusClient;
  }
}

export class ChromedashAmendment extends LitElement {
  @property({type: Object})
  amendment: Amendment = {
    field_name: '',
    old_value: '',
    new_value: '',
  };

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        details {
          color: var(--unimportant-text-color);
          padding: var(--content-padding-quarter);
        }

        summary {
          list-style: revert; /* Show small triangle */
          white-space: nowrap;
          box-sizing: border-box;
          contain: content;
          overflow: hidden;
        }

        details[open] #preview {
          display: none;
        }
        details > div {
          padding: var(--content-padding-quarter);
          padding-left: var(--content-padding);
        }
      `,
    ];
  }

  render() {
    return html`
      <details>
        <summary>
          <b>${this.amendment.field_name}</b>:
          <span id="preview">${this.amendment.new_value}</span>
        </summary>

        <div>
          <b>Old</b>:
          <div>${this.amendment.old_value}</div>
        </div>

        <div>
          <b>New</b>:
          <div>${this.amendment.new_value}</div>
        </div>
      </details>
    `;
  }
}
customElements.define('chromedash-amendment', ChromedashAmendment);

export interface User {
  can_create_feature: boolean;
  can_edit_all: boolean;
  can_comment: boolean;
  is_admin: boolean;
  email: string;
}
interface Activity {
  comment_id: number;
  author: string;
  created: string;
  content: string;
  deleted_by?: string | null;
  amendments: Amendment[];
}

export class ChromedashActivity extends LitElement {
  @property({type: Object})
  user: User = null!;

  @property({type: Number})
  featureId = 0;

  @property({type: Object})
  activity: Activity = null!;

  @property({type: Boolean})
  narrow = false;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .comment_header {
          min-height: 24px;
        }

        .comment_header.narrow .author {
          font-weight: 500;
        }
        .comment_header.narrow .preposition {
          display: none;
        }
        .comment_header.narrow .date {
          display: block;
          padding-bottom: var(--content-padding);
        }

        .comment {
          background: var(--table-alternate-background);
          border-radius: var(--large-border-radius);
          padding: var(--content-padding-half);
          margin-bottom: var(--content-padding);
          margin-right: var(--content-padding);
        }

        .comment-menu-icon {
          float: right;
          margin-right: 8px;
          cursor: pointer;
        }

        .comment_body {
          padding: var(--content-padding-half);
          white-space: pre-wrap;
        }

        p {
          padding: 1em;
        }
      `,
    ];
  }

  // Returns a boolean representing whether the given activity can be edited.
  isEditable() {
    if (!this.user) {
      return false;
    }
    // If the comment has been deleted, it should only be editable
    // by site admins or the user who deleted it.
    if (this.activity.deleted_by) {
      return this.user.is_admin || this.activity.deleted_by === this.user.email;
    }
    // If the comment is not deleted, site admins or the author can edit.
    return this.user.email === this.activity.author || this.user.is_admin;
  }

  // Format a message to show on a deleted comment the user can edit.
  renderDeletedPreface() {
    if (!this.isEditable() || !this.activity.deleted_by) {
      return nothing;
    }
    return html`<div style="color: darkred">
      [Deleted] (comment hidden for other users)
    </div>`;
  }

  // Add a dropdown menu to the activity header if the user can edit the activity.
  formatEditMenu() {
    // If the activity is not editable, don't show a menu.
    if (!this.isEditable()) {
      return nothing;
    }
    // Show delete option if not deleted, else show undelete.
    let menuItem = html` <sl-menu-item
      @click="${() => this.handleDelete(false)}"
      >Delete Comment</sl-menu-item
    >`;
    if (this.activity.deleted_by) {
      menuItem = html` <sl-menu-item @click="${() => this.handleDelete(true)}"
        >Undelete Comment</sl-menu-item
      >`;
    }

    return html` <sl-dropdown class="comment-menu-icon">
      <sl-icon-button
        library="material"
        name="more_vert_24px"
        label="Comment menu"
        slot="trigger"
      ></sl-icon-button>
      <sl-menu>${menuItem}</sl-menu>
    </sl-dropdown>`;
  }

  render() {
    if (!this.activity) {
      return nothing;
    }
    const preface = this.renderDeletedPreface();
    return html`
      <div class="comment">
        <div class="comment_header ${this.narrow ? 'narrow' : ''}">
          ${this.formatEditMenu()}
          <span class="author">${this.activity.author}</span>
          <span class="preposition">on</span>
          <span class="date">
            ${renderAbsoluteDate(this.activity.created, true)}
            ${renderRelativeDate(this.activity.created)}
          </span>
        </div>
        <div id="amendments">
          ${this.activity.amendments.map(
            a => html`
              <chromedash-amendment .amendment=${a}></chromedash-amendment>
            `
          )}
        </div>
        <!-- prettier-ignore -->
        <div class="comment_body">${preface}${autolink(
          this.activity.content
        )}</div>
      </div>
    `;
  }

  // Handle deleting or undeleting a comment.
  async handleDelete(isUndelete) {
    let resp;
    if (isUndelete) {
      resp = await window.csClient.undeleteComment(
        this.featureId,
        this.activity.comment_id
      );
    } else {
      resp = await window.csClient.deleteComment(
        this.featureId,
        this.activity.comment_id
      );
    }
    if (resp && resp.message === 'Done') {
      this.activity.deleted_by = isUndelete ? null : this.user.email;
      this.requestUpdate();
    }
  }
}
customElements.define('chromedash-activity', ChromedashActivity);

export class ChromedashActivityLog extends LitElement {
  @property({type: Object})
  user: User = null!;

  @property({type: Number})
  featureId = 0;

  @property({type: Array})
  comments = [];

  @property({type: Boolean})
  narrow = false;

  @state()
  reverse = false;

  @state()
  loading = false;

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        p {
          padding: var(--content-padding);
        }
      `,
    ];
  }

  render() {
    if (this.loading) {
      return html`<p>Loading...</p>`;
    }

    if (this.comments === undefined || this.comments.length === 0) {
      return html`<p>No comments yet.</p>`;
    }

    const orderedComments = this.reverse
      ? this.comments.slice(0).reverse()
      : this.comments;
    return orderedComments.map(
      activity => html`
        <chromedash-activity
          .user=${this.user}
          .featureId=${this.featureId}
          .narrow=${this.narrow}
          .activity=${activity}
        >
        </chromedash-activity>
      `
    );
  }
}

customElements.define('chromedash-activity-log', ChromedashActivityLog);
