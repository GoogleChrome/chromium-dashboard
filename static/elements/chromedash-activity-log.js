import {LitElement, css, html, nothing} from 'lit';
import {autolink} from './utils.js';
import '@polymer/iron-icon';

import {SHARED_STYLES} from '../sass/shared-css.js';


export class ChromedashActivity extends LitElement {
  static get properties() {
    return {
      user: {type: Object},
      feature: {type: Object},
      activity: {type: Object},
    };
  }

  constructor() {
    super();
    this.user = null;
    this.feature = {};
    this.activity = null;
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .comment_header {
          height: 24px;
        }

        .comment {
          margin-left: var(--content-padding);
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
          background: var(--table-alternate-background);
          padding: var(--content-padding-half);
          white-space: pre-wrap;
          width: 46em;
          margin-bottom: var(--content-padding);
        }
      `];
  }

  formatDate(dateStr) {
    return dateStr.split('.')[0]; // Ignore microseconds.
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

  // Display how long ago the comment was created compared to now.
  formatRelativeDate() {
    // Format date to "YYYY-MM-DDTHH:mm:ss.sssZ" to represent UTC.
    let dateStr = this.activity.created || '';
    dateStr = this.activity.created.replace(' ', 'T');
    const activityDate = new Date(`${dateStr}Z`);
    if (isNaN(activityDate)) {
      return nothing;
    }
    return html`
      <span class="relative_date">
        (<sl-relative-time date="${activityDate.toISOString()}">
        </sl-relative-time>)
      </span>`;
  }

  render() {
    if (!this.activity) {
      return nothing;
    }
    const preface = this.renderDeletedPreface();
    return html`
      <div class="comment">
        <div class="comment_header">
           <span class="author">${this.activity.author}</span>
           on
           <span class="date">${this.formatDate(this.activity.created)}</span>
           ${this.formatRelativeDate()}
           ${this.formatEditMenu()}
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
    };
  }

  constructor() {
    super();
    this.user = null;
    this.feature = {};
    this.comments = [];
  }

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .comment_section {
          max-height: 250px;
          overflow-y: scroll;
        }
      `];
  }


  render() {
    return html`
        <div class="comment_section">
          ${this.comments.map((activity) => html`
        <chromedash-activity
        .user=${this.user}
        .feature=${this.feature}
        .activity=${activity}>
        </chromedash-activity>
          `)}
        </div>
    `;
  }
}

customElements.define('chromedash-activity-log', ChromedashActivityLog);
