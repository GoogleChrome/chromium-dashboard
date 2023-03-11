import {LitElement, css, html, nothing} from 'lit';
import {autolink, renderAbsoluteDate, renderRelativeDate,
} from './utils.js';
import '@polymer/iron-icon';

import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashAmendment extends LitElement {
  static get properties() {
    return {
      amendment: {type: Object},
    };
  }

  constructor() {
    super();
    this.amendment = {};
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        details {
          color: var(--unimportant-text-color);
          padding: var(--content-padding-quarter);
        }

        summary {
          list-style: revert;  /* Show small triangle */
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
      `];
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
};
customElements.define('chromedash-amendment', ChromedashAmendment);


export class ChromedashActivity extends LitElement {
  static get properties() {
    return {
      user: {type: Object},
      feature: {type: Object},
      activity: {type: Object},
      narrow: {type: Boolean},
    };
  }

  constructor() {
    super();
    this.user = null;
    this.feature = {};
    this.activity = null;
    this.narrow = false;
  }

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

        .edit-menu {
          display: block;
          float: right;
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
      `];
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
    return html`<div style="color: darkred">[Deleted] (comment hidden for other users)
    </div>`;
  }

  toggleMenu() {
    const menuEl = this.shadowRoot.querySelector(`#comment-menu`);
    // Change the menu icon to represent open/closing on click.
    const iconEl = this.shadowRoot.querySelector(`iron-icon`);
    const isVisible = menuEl.style.display !== 'none';
    if (isVisible) {
      menuEl.style.display = 'none';
      iconEl.icon = 'chromestatus:more-vert';
    } else {
      menuEl.style.display = 'inline-block';
      iconEl.icon = 'chromestatus:close';
    }
  }

  // Add a dropdown menu to the activity header if the user can edit the activity.
  formatEditMenu() {
    // If the activity is not editable, don't show a menu.
    if (!this.isEditable()) {
      return nothing;
    }
    // Show delete option if not deleted, else show undelete.
    let menuItem = html`
    <sl-menu-item @click="${() => this.handleDeleteToggle(false)}"
    >Delete Comment</sl-menu-item>`;
    if (this.activity.deleted_by) {
      menuItem = html`
      <sl-menu-item @click="${() => this.handleDeleteToggle(true)}"
      >Undelete Comment</sl-menu-item>`;
    }

    return html`
      <iron-icon class="comment-menu-icon"
      icon="chromestatus:more-vert"
      @click=${() => this.toggleMenu()}></iron-icon>
      <div class="edit-menu">
        <div id="comment-menu" style="display: none;">
          <sl-menu>${menuItem}</sl-menu>
        </div>
      </div>`;
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
          ${this.activity.amendments.map((a) => html`
            <chromedash-amendment .amendment=${a}></chromedash-amendment>
          `)}
        </div>
        <div class="comment_body">${preface}${autolink(this.activity.content)}</div>
      </div>
    `;
  }

  // Handle deleting or undeleting a comment.
  async handleDeleteToggle(isUndelete) {
    let resp;
    if (isUndelete) {
      resp = await window.csClient.undeleteComment(
        this.feature.id, this.activity.comment_id);
    } else {
      resp = await window.csClient.deleteComment(
        this.feature.id, this.activity.comment_id);
    }
    if (resp && resp.message === 'Done') {
      this.activity.deleted_by = (isUndelete) ? null : this.user.email;
      this.toggleMenu();
      this.requestUpdate();
    }
  }
};
customElements.define('chromedash-activity', ChromedashActivity);


export class ChromedashActivityLog extends LitElement {
  static get properties() {
    return {
      user: {type: Object},
      feature: {type: Object},
      comments: {type: Array},
      narrow: {type: Boolean},
      reverse: {type: Boolean},
    };
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        p {
          padding: var(--content-padding);
        }
    `];
  }

  constructor() {
    super();
    this.user = null;
    this.feature = {};
    this.comments = [];
    this.narrow = false;
    this.reverse = false;
  }

  render() {
    if (this.loading) {
      return html`<p>Loading...</p>`;
    }

    if (this.comments === undefined || this.comments.length === 0) {
      return html`<p>No comments yet.</p>`;
    }

    const orderedComments = (
      this.reverse ? this.comments.slice(0).reverse() : this.comments);
    return orderedComments.map((activity) => html`
        <chromedash-activity
          .user=${this.user}
          .feature=${this.feature}
          .narrow=${this.narrow}
          .activity=${activity}>
        </chromedash-activity>
      `);
  }
}

customElements.define('chromedash-activity-log', ChromedashActivityLog);
