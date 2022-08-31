import {LitElement, css, html, nothing} from 'lit';
import '@polymer/iron-icon';

import {SHARED_STYLES} from '../sass/shared-css.js';


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

  // Returns a boolean representing whether the given comment can be edited.
  commentIsEditable(comment) {
    if (!this.user) {
      return false;
    }
    // If the comment has been deleted, it should only be editable
    // by site admins or the user who deleted it.
    if (comment.deleted_by) {
      return this.user.is_admin || comment.deleted_by === this.user.email;
    }
    // If the comment is not deleted, site admins or the author can edit.
    return this.user.email === comment.author || this.user.is_admin;
  }

  // Format a message to show on a deleted comment the user can edit.
  renderCommentDeletedPreface(comment) {
    if (!this.commentIsEditable(comment) || !comment.deleted_by) {
      return nothing;
    }
    return html`<div style="color: darkred">[Deleted] (comment hidden for other users)
    </div>`;
  }

  toggleCommentMenu(commentId) {
    const menuEl = this.shadowRoot.querySelector(`#comment-menu-${commentId}`);
    // Change the menu icon to represent open/closing on click.
    const iconEl = this.shadowRoot.querySelector(`#icon-${commentId}`);
    const isVisible = menuEl.style.display !== 'none';
    if (isVisible) {
      menuEl.style.display = 'none';
      iconEl.icon = 'chromestatus:more-vert';
    } else {
      menuEl.style.display = 'inline-block';
      iconEl.icon = 'chromestatus:close';
    }
  }

  // Add a dropdown menu to the comment header if the user can edit the comment.
  formatCommentEditMenu(comment) {
    // If the comment is not editable, don't show a comment menu.
    if (!this.commentIsEditable(comment)) {
      return nothing;
    }
    // Show delete option if not deleted, else show undelete.
    let menuItem = html`
    <sl-menu-item @click="${() => this.handleDeleteToggle(comment, false)}"
    >Delete Comment</sl-menu-item>`;
    if (comment.deleted_by) {
      menuItem = html`
      <sl-menu-item @click="${() => this.handleDeleteToggle(comment, true)}"
      >Undelete Comment</sl-menu-item>`;
    }

    return html`
      <iron-icon class="comment-menu-icon" id="icon-${comment.comment_id}"
      icon="chromestatus:more-vert"
      @click=${() => this.toggleCommentMenu(comment.comment_id)}></iron-icon>
      <div class="edit-menu">
        <div id="comment-menu-${comment.comment_id}" style="display: none;">
          <sl-menu>${menuItem}</sl-menu>
        </div>
      </div>`;
  }

  // Display how long ago the comment was created compared to now.
  formatCommentRelativeDate(comment) {
    const commentDate = new Date(`${comment.created}Z`);
    if (isNaN(commentDate)) {
      return nothing;
    }
    return html`
      <span class="relative_date">
        (<sl-relative-time date="${commentDate.toISOString()}">
        </sl-relative-time>)
      </span>`;
  }

  renderComment(comment) {
    const preface = this.renderCommentDeletedPreface(comment);
    return html`
      <div class="comment">
        <div class="comment_header">
           <span class="author">${comment.author}</span>
           on
           <span class="date">${this.formatDate(comment.created)}</span>
           ${this.formatCommentRelativeDate(comment)}
           ${this.formatCommentEditMenu(comment)}
        </div>
        <div class="comment_body">${preface}${comment.content}</div>
      </div>
    `;
  }

  render() {
    return html`
        <div class="comment_section">
          ${this.comments.map(this.renderComment.bind(this))}
        </div>
    `;
  }

  // Handle deleting or undeleting a comment.
  async handleDeleteToggle(comment, isUndelete) {
    let resp;
    if (isUndelete) {
      resp = await window.csClient.undeleteComment(
        this.feature.id, comment.comment_id);
    } else {
      resp = await window.csClient.deleteComment(
        this.feature.id, comment.comment_id);
    }
    if (resp && resp.message === 'Done') {
      comment.deleted_by = (isUndelete) ? null : this.user.email;
      this.toggleCommentMenu(comment.comment_id);
      this.requestUpdate();
    }
  }
}

customElements.define('chromedash-activity-log', ChromedashActivityLog);
