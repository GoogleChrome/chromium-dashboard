import {LitElement, css, html, nothing} from 'lit';
import {ref, createRef, Ref} from 'lit/directives/ref.js';
import './chromedash-activity-log';
import {showToastMessage} from './utils.js';
import {property, state, customElement} from 'lit/decorators.js';
import {User} from './chromedash-activity-log.js';
import {SHARED_STYLES} from '../css/shared-css.js';

@customElement('chromedash-activity-page')
export class ChromedashActivityPage extends LitElement {
  commentAreaRef: Ref<HTMLTextAreaElement> = createRef();

  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        .instructions {
          padding: var(--content-padding-half);
          margin-bottom: var(--content-padding-large);
          margin-left: 10px;
        }

        #comment_area {
          margin: 0 var(--content-padding);
        }
        #header {
          margin-bottom: 10px;
          margin-left: 15px;
        }
        #controls {
          padding: var(--content-padding);
          text-align: right;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        #controls * + * {
          padding-left: var(--content-padding);
        }
      `,
    ];
  }

  @property({type: Object})
  user: User = {
    can_create_feature: false,
    can_edit_all: false,
    can_comment: false,
    is_admin: false,
    email: '',
  };
  @property({type: Number})
  featureId = 0;
  @property({type: Array})
  comments = [];
  @state()
  loading = true;
  @property({type: Boolean})
  needsPost = false;
  @property({type: String})
  contextLink = '';

  connectedCallback() {
    super.connectedCallback();
    this.fetchComments();
  }

  fetchComments() {
    this.loading = true;
    Promise.all([window.csClient.getComments(this.featureId, null)])
      .then(([commentRes]) => {
        this.comments = commentRes.comments;
        this.needsPost = false;
        this.loading = false;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  reloadComments() {
    const commentArea = this.commentAreaRef.value;
    commentArea!.value = '';
    this.needsPost = false;
    Promise.all([window.csClient.getComments(this.featureId, null)])
      .then(([commentRes]) => {
        this.comments = commentRes.comments;
      })
      .catch(() => {
        showToastMessage(
          'Some errors occurred. Please refresh the page or try again later.'
        );
      });
  }

  checkNeedsPost() {
    let newNeedsPost = false;
    const commentArea = this.commentAreaRef.value;
    const newVal = (commentArea && commentArea.value.trim()) || '';
    if (newVal != '') newNeedsPost = true;
    this.needsPost = newNeedsPost;
  }

  handlePost() {
    const commentArea = this.commentAreaRef.value;
    const commentText = commentArea!.value.trim();
    if (commentText != '') {
      window.csClient
        .postComment(this.featureId, null, commentText, 0)
        .then(() => {
          this.reloadComments();
        })
        .catch(() => {
          showToastMessage(
            'Some errors occurred. Please refresh the page or try again later.'
          );
        });
    }
  }

  renderCommentsSkeleton() {
    // TODO(jrobbins): Include activities too.
    return html`
      <h2>Comments</h2>
      <sl-skeleton effect="sheen"></sl-skeleton>
    `;
  }

  renderControls() {
    if (!this.user || !this.user.can_comment) return nothing;

    const postButton = html`
      <sl-button
        variant="primary"
        @click=${this.handlePost}
        ?disabled=${!this.needsPost}
        size="small"
        >Post</sl-button
      >
    `;

    return html`
      <sl-textarea
        id="comment_area"
        rows="2"
        cols="40"
        ${ref(this.commentAreaRef)}
        @sl-change=${this.checkNeedsPost}
        @keypress=${this.checkNeedsPost}
        placeholder="Add a comment"
      ></sl-textarea>
      <div class="instructions">
        Comments will be visible publicly. Only reviewers will be notified when
        a comment is posted.
      </div>
      <div id="controls">${postButton}</div>
    `;
  }

  renderComments() {
    // TODO(jrobbins): Include relevant activities too.
    return html`
      <div id="header">
        <h2 id="breadcrumbs">
          <a href="/feature/${this.featureId}">
            <iron-icon icon="chromestatus:arrow-back"></iron-icon>
            Comments &amp; Activity
          </a>
        </h2>
      </div>
      ${this.renderControls()}
      <chromedash-activity-log
        .user=${this.user}
        .featureId=${this.featureId}
        .narrow=${true}
        .reverse=${true}
        .comments=${this.comments}
      >
      </chromedash-activity-log>
    `;
  }

  render() {
    return html`
      ${this.loading ? this.renderCommentsSkeleton() : this.renderComments()}
    `;
  }
}
