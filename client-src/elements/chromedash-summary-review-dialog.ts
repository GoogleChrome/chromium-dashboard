/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state, query} from 'lit/decorators.js';
import {SHARED_STYLES} from '../css/shared-css.js';
import {User, Feature, SuggestionData} from '../js-src/cs-client.js';
import {showToastMessage, autolink} from './utils.js';
import {SlDialog} from '@shoelace-style/shoelace';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import '@shoelace-style/shoelace/dist/components/checkbox/checkbox.js';
import '@shoelace-style/shoelace/dist/components/spinner/spinner.js';
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/input/input.js';

interface HttpError {
  status?: number;
  message?: string;
}

function isHttpError(err: unknown): err is HttpError {
  return typeof err === 'object' && err !== null;
}

@customElement('chromedash-summary-review-dialog')
export class ChromedashSummaryReviewDialog extends LitElement {
  static get styles() {
    return [
      ...SHARED_STYLES,
      css`
        /* Responsive dialog width override */
        sl-dialog {
          --width: 95vw;
        }
        @media (min-width: 768px) {
          sl-dialog {
            --width: 85vw;
          }
        }
        @media (min-width: 1200px) {
          sl-dialog {
            --width: 70vw;
          }
        }

        .diff-split-container {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        @media (min-width: 768px) {
          .diff-split-container {
            flex-direction: row;
          }
        }

        .diff-column {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
        }

        .diff-column-header {
          font-weight: bold;
          font-size: 1.1rem;
          border-bottom: 1px solid var(--sl-color-neutral-300);
          padding-bottom: 0.4rem;
          margin: 0;
        }

        .field-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          min-height: 32px;
        }

        .field-header strong {
          font-size: 0.95rem;
        }

        .original-text,
        .original-links,
        .suggested-links-container {
          background: var(--sl-color-neutral-50);
          border: 1px solid var(--sl-color-neutral-200);
          padding: 0.8rem;
          border-radius: 4px;
          font-size: 0.95rem;
        }

        .original-text {
          white-space: pre-wrap;
          min-height: 150px;
        }

        .editable-summary-textarea::part(textarea) {
          min-height: 150px;
        }

        .original-links,
        .suggested-links-container {
          min-height: 150px;
          display: flex;
          flex-direction: column;
        }

        .original-link-row {
          margin-bottom: 0.4rem;
          line-height: 1.4;
        }

        .original-link-row a {
          color: var(--sl-color-primary-600);
          text-decoration: none;
          word-break: break-all;
        }

        .original-link-row a:hover {
          text-decoration: underline;
        }

        .suggested-links-container {
          gap: 0.8rem;
        }

        .editable-links-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          flex-grow: 1;
        }

        .link-edit-row {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }

        .link-edit-row sl-checkbox {
          flex-shrink: 0;
        }

        .link-edit-row a {
          color: var(--sl-color-primary-600);
          text-decoration: none;
          word-break: break-all;
        }

        .link-edit-row a:hover {
          text-decoration: underline;
        }

        .add-link-container {
          display: flex;
          gap: 0.5rem;
          margin-top: auto;
          padding-top: 0.8rem;
          border-top: 1px dashed var(--sl-color-neutral-300);
        }

        .bypass-container {
          margin-top: 1.5rem;
          padding: 1rem;
          background: var(--sl-color-warning-50);
          border: 1px solid var(--sl-color-warning-200);
          border-radius: 4px;
        }

        .error-message {
          color: var(--sl-color-danger-600);
          margin-top: 1rem;
          font-weight: 500;
        }

        .dialog-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          width: 100%;
        }

        .dialog-footer-actions {
          display: flex;
          gap: 0.5rem;
        }

        .workspace-container {
          margin-top: 1.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid var(--sl-color-neutral-300);
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
        }

        .workspace-header {
          font-weight: bold;
          font-size: 1.1rem;
          margin: 0;
        }

        .tab-header {
          display: flex;
          gap: 0.5rem;
          border-bottom: 2px solid var(--sl-color-neutral-200);
          margin-bottom: 0.5rem;
        }

        .tab-btn {
          background: none;
          border: none;
          padding: 0.5rem 1rem;
          font-size: 0.95rem;
          font-weight: 500;
          cursor: pointer;
          color: var(--sl-color-neutral-600);
          border-bottom: 2px solid transparent;
          margin-bottom: -2px;
          outline: none;
        }

        .tab-btn:hover {
          color: var(--sl-color-primary-600);
        }

        .tab-btn.active {
          color: var(--sl-color-primary-600);
          border-bottom-color: var(--sl-color-primary-600);
        }

        .preview-container {
          background: var(--sl-color-neutral-50);
          border: 1px solid var(--sl-color-neutral-200);
          padding: 0.8rem;
          border-radius: 4px;
          min-height: 150px;
          overflow-y: auto;
          font-size: 0.95rem;
          line-height: 1.5;
        }

        .preview-container p {
          margin: 0 0 1em 0;
        }

        .preview-container p:last-child {
          margin-bottom: 0;
        }

        .conflict-banner {
          background: var(--sl-color-danger-50);
          border: 1px solid var(--sl-color-danger-200);
          color: var(--sl-color-danger-800);
          padding: 0.8rem 1rem;
          border-radius: 4px;
          margin-bottom: 1.5rem;
          font-weight: 500;
        }

        .conflict-pane-container {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          margin-bottom: 1.5rem;
        }
        @media (min-width: 768px) {
          .conflict-pane-container {
            flex-direction: row;
          }
        }

        .conflict-pane {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
        }
      `,
    ];
  }

  @property({attribute: false})
  user!: User | null;
  @property({attribute: false})
  feature!: Feature | null;
  @property({attribute: false})
  suggestion!: SuggestionData | null;

  @state()
  showBypassUI = false;
  @state()
  bypassJustification = '';

  @state()
  summaryText = '';
  @state()
  linksList: {url: string; approved: boolean}[] = [];
  @state()
  newLinkLabelInput = '';
  @state()
  submitting = false;
  @state()
  errorMessage = '';
  @state()
  activeTab: 'write' | 'preview' = 'write';
  @state()
  isDirty = false;
  @state()
  inConflict = false;
  @state()
  serverSummaryText = '';
  @state()
  serverLinksList: {url: string; approved: boolean}[] = [];
  @state()
  serverVersionToken = 1;

  @query('#dialog')
  dialogEl!: SlDialog;

  show() {
    if (!this.feature || !this.suggestion) return;

    // Initialize editing states
    this.summaryText =
      this.suggestion.suggested_summary || this.feature.summary || '';

    const aiLinks = new Set(this.suggestion.suggested_doc_links || []);
    const featureLinks = new Set(this.feature.resources?.docs || []);
    const combined = Array.from(new Set([...aiLinks, ...featureLinks]));

    this.linksList = combined.map(url => ({
      url,
      approved: aiLinks.has(url),
    }));
    this.newLinkLabelInput = '';
    this.errorMessage = '';
    this.submitting = false;
    this.showBypassUI = false;
    this.bypassJustification = '';
    this.activeTab = 'write';
    this.isDirty = false;
    this.inConflict = false;
    this.serverSummaryText = '';
    this.serverLinksList = [];
    this.serverVersionToken = this.suggestion.version_token || 1;

    void this.dialogEl.show();
  }

  hide() {
    void this.dialogEl.hide();
  }

  useOriginalText() {
    if (this.isDirty) {
      const ok = window.confirm(
        'You have unsaved changes. Overwriting will discard your edits. Do you want to proceed?'
      );
      if (!ok) return;
    }
    if (this.feature) {
      this.summaryText = this.feature.summary || '';
      this.isDirty = false;
    }
  }

  useAIText() {
    if (this.isDirty) {
      const ok = window.confirm(
        'You have unsaved changes. Overwriting will discard your edits. Do you want to proceed?'
      );
      if (!ok) return;
    }
    if (this.suggestion) {
      this.summaryText = this.suggestion.suggested_summary || '';
      this.isDirty = false;
    }
  }

  toggleLinkApproved(index: number) {
    this.linksList[index].approved = !this.linksList[index].approved;
    this.linksList = [...this.linksList];
    this.isDirty = true;
  }

  addNewLink() {
    const url = this.newLinkLabelInput.trim();
    if (!url) return;
    if (this.linksList.some(item => item.url === url)) {
      showToastMessage('Link is already in the list.');
      return;
    }
    this.linksList = [...this.linksList, {url, approved: true}];
    this.newLinkLabelInput = '';
    this.isDirty = true;
  }

  isBypassRequired() {
    if (!this.feature || !this.suggestion || !this.user) return false;

    if (this.suggestion.status_timestamp) {
      const statusTime = new Date(this.suggestion.status_timestamp).getTime();
      const now = Date.now();
      const isWithinGrace = now < statusTime + 7 * 24 * 60 * 60 * 1000;
      if (isWithinGrace) {
        const email = this.user.email;
        const isOwner = this.feature.owner_emails?.includes(email) || false;
        const isEditor = this.feature.editor_emails?.includes(email) || false;
        const isCreator = this.feature.creator_email === email;
        const isPrivileged = isOwner || isEditor || isCreator;
        return !isPrivileged;
      }
    }
    return false;
  }

  async enterConflictMode() {
    this.inConflict = true;
    this.errorMessage =
      'Conflict: Another editor has saved edits. Please choose how to resolve this conflict.';
    this.submitting = true;
    try {
      const serverSuggestion = await window.csClient.getSummarySuggestion(
        this.feature!.id
      );
      this.serverSummaryText = serverSuggestion.suggested_summary || '';
      const serverAiLinks = new Set<string>(
        serverSuggestion.suggested_doc_links || []
      );
      const featureLinks = new Set<string>(this.feature!.resources?.docs || []);
      const combined = Array.from<string>(
        new Set<string>([...serverAiLinks, ...featureLinks])
      );

      this.serverLinksList = combined.map((url: string) => ({
        url,
        approved: serverAiLinks.has(url),
      }));
      this.serverVersionToken = serverSuggestion.version_token || 1;
    } catch {
      this.errorMessage = 'Failed to fetch latest server version for merging.';
    } finally {
      this.submitting = false;
    }
  }

  acceptServerChanges() {
    this.summaryText = this.serverSummaryText;
    this.linksList = this.serverLinksList.map(item => ({...item}));
    if (this.suggestion) {
      this.suggestion.suggested_summary = this.serverSummaryText;
      this.suggestion.suggested_doc_links = this.serverLinksList
        .filter(item => item.approved)
        .map(item => item.url);
      this.suggestion.version_token = this.serverVersionToken;
    }
    this.inConflict = false;
    this.isDirty = false;
    this.errorMessage = '';
  }

  async applySuggestion() {
    if (!this.feature || !this.suggestion) return;

    if (this.isBypassRequired() && !this.showBypassUI) {
      this.showBypassUI = true;
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    const approvedLinks = this.linksList
      .filter(item => item.approved)
      .map(item => item.url);

    try {
      await window.csClient.patchSummarySuggestion(
        this.feature.id,
        'applied',
        this.inConflict
          ? this.serverVersionToken
          : this.suggestion.version_token,
        this.summaryText,
        approvedLinks,
        this.bypassJustification || undefined
      );

      this.dispatchEvent(
        new CustomEvent<{summary: string; links: string[]}>('applied', {
          detail: {
            summary: this.summaryText,
            links: approvedLinks,
          },
        })
      );
      this.inConflict = false;
      this.isDirty = false;
      this.hide();
    } catch (err) {
      if (isHttpError(err)) {
        if (err.status === 409) {
          await this.enterConflictMode();
        } else {
          this.errorMessage = err.message || 'Failed to apply suggestion.';
        }
      } else {
        this.errorMessage = 'Failed to apply suggestion.';
      }
    } finally {
      if (!this.inConflict) {
        this.submitting = false;
      }
    }
  }

  async discardSuggestion() {
    if (!this.feature || !this.suggestion) return;
    this.submitting = true;
    this.errorMessage = '';

    try {
      await window.csClient.patchSummarySuggestion(
        this.feature.id,
        'discarded',
        this.suggestion.version_token
      );

      this.dispatchEvent(new CustomEvent('discarded'));
      this.hide();
    } catch (err) {
      if (isHttpError(err)) {
        if (err.status === 409) {
          this.errorMessage =
            'Conflict: This suggestion was modified by another editor.';
        } else {
          this.errorMessage = err.message || 'Failed to discard suggestion.';
        }
      } else {
        this.errorMessage = 'Failed to discard suggestion.';
      }
    } finally {
      this.submitting = false;
    }
  }

  render() {
    return html`
      <sl-dialog
        id="dialog"
        label="Review AI Suggested Summary & Links"
        @sl-request-close=${(e: CustomEvent<{source: string}>) => {
          if (this.submitting || e.detail.source === 'overlay')
            e.preventDefault();
        }}
      >
        ${this.inConflict
          ? html`
              <div class="conflict-banner">
                ⚠️ Conflict: Another editor has already saved changes to this
                suggestion. Please review the server's version and choose how to
                resolve this conflict.
              </div>
              <div class="conflict-pane-container">
                <!-- Left Pane: Server Version -->
                <div class="conflict-pane">
                  <h4 class="diff-column-header">
                    Their Version (Saved on Server)
                  </h4>
                  <div class="field-header">
                    <strong>Summary</strong>
                  </div>
                  <div class="original-text" data-testid="server-summary-reference">
                    ${this.serverSummaryText || 'No summary'}
                  </div>
                  <div class="field-header">
                    <strong>Links</strong>
                  </div>
                  <div class="original-links">
                    ${this.serverLinksList.length
                      ? this.serverLinksList.map(
                          item => html`
                            <div class="original-link-row">
                              &bull;
                              <a href=${item.url} target="_blank"
                                >${item.url}</a
                              >
                              ${item.approved ? '(Approved)' : '(Not Approved)'}
                            </div>
                          `
                        )
                      : 'No doc links'}
                  </div>
                </div>

                <!-- Right Pane: Your Version (Local Draft) -->
                <div class="conflict-pane">
                  <h4 class="diff-column-header">Your Version (Local Draft)</h4>
                  <div class="field-header">
                    <strong>Summary</strong>
                  </div>
                  <div class="original-text" data-testid="local-summary-draft-reference">${this.summaryText}</div>
                  <div class="field-header">
                    <strong>Links</strong>
                  </div>
                  <div class="original-links">
                    ${this.linksList.length
                      ? this.linksList.map(
                          item => html`
                            <div class="original-link-row">
                              &bull;
                              <a href=${item.url} target="_blank"
                                >${item.url}</a
                              >
                              ${item.approved ? '(Approved)' : '(Not Approved)'}
                            </div>
                          `
                        )
                      : 'No doc links'}
                  </div>
                </div>
              </div>

              ${this.errorMessage
                ? html`<div class="error-message">${this.errorMessage}</div>`
                : nothing}

              <div slot="footer">
                <div class="dialog-footer">
                  <sl-button
                    @click=${this.acceptServerChanges}
                    ?disabled=${this.submitting}
                  >
                    Accept Server Changes
                  </sl-button>
                  <div class="dialog-footer-actions">
                    <sl-button @click=${this.hide} ?disabled=${this.submitting}
                      >Cancel</sl-button
                    >
                    <sl-button
                      variant="primary"
                      ?loading=${this.submitting}
                      ?disabled=${this.submitting}
                      @click=${this.applySuggestion}
                    >
                      Force Overwrite Server
                    </sl-button>
                  </div>
                </div>
              </div>
            `
          : html`
              <div class="diff-split-container">
                <!-- Left Column (Original/Baseline) -->
                <div class="diff-column">
                  <h3 class="diff-column-header">Original Feature Details</h3>

                  <div class="field-header">
                    <strong>Original Summary</strong>
                  </div>
                  <div class="original-text" data-testid="original-summary">
                    ${this.feature?.summary || 'No summary'}
                  </div>

                  <div class="field-header">
                    <strong>Original Doc Links</strong>
                  </div>
                  <div class="original-links">
                    ${this.feature?.resources?.docs?.length
                      ? this.feature.resources.docs.map(
                          link => html`
                            <div class="original-link-row">
                              &bull; <a href=${link} target="_blank">${link}</a>
                            </div>
                          `
                        )
                      : 'No doc links'}
                  </div>
                </div>

                <!-- Right Column (AI/Suggested Reference) -->
                <div class="diff-column">
                  <h3 class="diff-column-header">
                    AI-Assisted Suggestion (Reference)
                  </h3>

                  <div class="field-header">
                    <strong>Suggested Summary</strong>
                  </div>
                  <div class="original-text" data-testid="suggested-summary-reference">
                    ${this.suggestion?.suggested_summary ||
                    'No suggested summary'}
                  </div>

                  <div class="field-header">
                    <strong>Suggested Doc Links</strong>
                  </div>
                  <div class="original-links">
                    ${this.suggestion?.suggested_doc_links?.length
                      ? this.suggestion.suggested_doc_links.map(
                          link => html`
                            <div class="original-link-row">
                              &bull; <a href=${link} target="_blank">${link}</a>
                            </div>
                          `
                        )
                      : 'No doc links'}
                  </div>
                </div>
              </div>

              <!-- Bottom Workspace -->
              <div class="workspace-container">
                <h3 class="workspace-header">Edit and Finalize Draft</h3>

                <div class="field-header">
                  <div
                    class="tab-header"
                    role="tablist"
                    aria-label="Draft tabs"
                  >
                    <button
                      class="tab-btn ${this.activeTab === 'write'
                        ? 'active'
                        : ''}"
                      role="tab"
                      aria-selected=${this.activeTab === 'write'}
                      @click=${() => {
                        this.activeTab = 'write';
                      }}
                    >
                      Write
                    </button>
                    <button
                      class="tab-btn ${this.activeTab === 'preview'
                        ? 'active'
                        : ''}"
                      role="tab"
                      aria-selected=${this.activeTab === 'preview'}
                      @click=${() => {
                        this.activeTab = 'preview';
                      }}
                    >
                      Preview
                    </button>
                  </div>

                  ${this.activeTab === 'write'
                    ? html`
                        <sl-button-group
                          label="Copy original or suggested text"
                        >
                          <sl-button
                            size="small"
                            @click=${this.useOriginalText}
                            ?disabled=${this.submitting}
                            >Use Original</sl-button
                          >
                          <sl-button
                            size="small"
                            @click=${this.useAIText}
                            ?disabled=${this.submitting}
                            >Use Suggested</sl-button
                          >
                        </sl-button-group>
                      `
                    : nothing}
                </div>

                ${this.activeTab === 'write'
                  ? html`
                      <sl-textarea
                        class="editable-summary-textarea"
                        aria-label="Suggested Summary"
                        .value=${this.summaryText}
                        ?disabled=${this.submitting}
                        @sl-input=${(e: Event) => {
                          const target = e.target;
                          if (target && 'value' in target) {
                            this.summaryText = String(target.value);
                            this.isDirty = true;
                          }
                        }}
                      ></sl-textarea>
                    `
                  : html`
                      <div class="preview-container">
                        ${autolink(this.summaryText, [], true)}
                      </div>
                    `}

                <div class="field-header">
                  <strong>Final Documentation Links</strong>
                </div>
                <div class="suggested-links-container">
                  <div class="editable-links-list">
                    ${this.linksList.map(
                      (item, idx) => html`
                        <div class="link-edit-row">
                          <sl-checkbox
                            data-testid="link-checkbox-${idx}"
                            aria-label="Approve link: ${item.url}"
                            ?checked=${item.approved}
                            ?disabled=${this.submitting}
                            @sl-change=${() => this.toggleLinkApproved(idx)}
                          ></sl-checkbox>
                          <a href=${item.url} target="_blank">${item.url}</a>
                        </div>
                      `
                    )}
                  </div>

                  <div class="add-link-container">
                    <sl-input
                      size="small"
                      placeholder="Add custom doc link URL..."
                      aria-label="New document link URL"
                      .value=${this.newLinkLabelInput}
                      ?disabled=${this.submitting}
                      @sl-change=${(e: Event) => {
                        const target = e.target;
                        if (target && 'value' in target) {
                          this.newLinkLabelInput = String(target.value);
                        }
                      }}
                      style="flex-grow: 1;"
                    ></sl-input>
                    <sl-button
                      size="small"
                      @click=${this.addNewLink}
                      ?disabled=${this.submitting}
                      >Add</sl-button
                    >
                  </div>
                </div>
              </div>

              ${this.showBypassUI
                ? html`
                    <div class="bypass-container">
                      <sl-textarea
                        name="bypass_justification"
                        label="Bypass Justification (Required)"
                        placeholder="Explain why you are bypassing the feature owner..."
                        .value=${this.bypassJustification}
                        ?disabled=${this.submitting}
                        @sl-input=${(e: Event) => {
                          const target = e.target;
                          if (target && 'value' in target) {
                            this.bypassJustification = String(target.value);
                          }
                        }}
                      ></sl-textarea>
                    </div>
                  `
                : nothing}
              ${this.errorMessage
                ? html`<div class="error-message">${this.errorMessage}</div>`
                : nothing}

              <div slot="footer">
                <div class="dialog-footer">
                  <sl-button
                    variant="danger"
                    outline
                    ?loading=${this.submitting}
                    ?disabled=${this.submitting}
                    @click=${this.discardSuggestion}
                  >
                    Discard Suggestion
                  </sl-button>
                  <div class="dialog-footer-actions">
                    <sl-button ?disabled=${this.submitting} @click=${this.hide}
                      >Cancel</sl-button
                    >
                    ${this.showBypassUI
                      ? html`
                          <sl-button
                            ?disabled=${this.submitting}
                            @click=${() => {
                              this.showBypassUI = false;
                            }}
                          >
                            Cancel Bypass
                          </sl-button>
                          <sl-button
                            variant="primary"
                            ?loading=${this.submitting}
                            ?disabled=${this.submitting ||
                            !this.bypassJustification.trim()}
                            @click=${this.applySuggestion}
                          >
                            Confirm Bypass
                          </sl-button>
                        `
                      : html`
                          <sl-button
                            variant="primary"
                            ?loading=${this.submitting}
                            ?disabled=${this.submitting}
                            @click=${this.applySuggestion}
                          >
                            Save & Apply
                          </sl-button>
                        `}
                  </div>
                </div>
              </div>
            `}
      </sl-dialog>
    `;
  }
}
