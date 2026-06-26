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
            --width: 90vw;
          }
        }
        @media (min-width: 1200px) {
          sl-dialog {
            --width: 80vw;
          }
        }

        /* Unified Review Grid (Stack of Rows) */
        .unified-review-grid {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        /* Equal-Height Row Design */
        .review-row {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding-bottom: 2rem;
          border-bottom: 1px solid var(--sl-color-neutral-200);
        }

        .review-row:last-child {
          border-bottom: none;
          padding-bottom: 0;
        }

        /* Cells inside the Row */
        .review-cell {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
        }

        /* Desktop Side-by-Side Symmetrical Divider Layout */
        @media (min-width: 992px) {
          .review-row {
            flex-direction: row;
            align-items: stretch; /* Forces left and right columns to match height perfectly */
          }
          .review-cell {
            width: 50%;
          }
          .review-cell.left-cell {
            border-right: 1px solid var(--sl-color-neutral-200);
            padding-right: 1.8rem;
          }
          .review-cell.right-cell {
            padding-left: 1.8rem;
          }
        }

        /* Headers & Titles */
        .section-title {
          font-size: 1.15rem;
          font-weight: 700;
          margin: 0 0 0.5rem 0;
          color: var(--sl-color-neutral-800);
          border-bottom: 2px solid var(--sl-color-neutral-200);
          padding-bottom: 0.4rem;
        }

        .field-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          min-height: 32px;
          margin-bottom: 0.2rem;
        }

        .field-header strong {
          font-size: 0.95rem;
          color: var(--sl-color-neutral-700);
        }

        /* Custom Text and Links Panels */
        .original-text,
        .original-links,
        .suggested-links-container,
        .summary-workspace-card {
          background: var(--sl-color-neutral-50);
          border: 1px solid var(--sl-color-neutral-200);
          padding: 0.8rem;
          border-radius: 4px;
          font-size: 0.95rem;
          display: flex;
          flex-direction: column;
          flex-grow: 1; /* Allows container to fill all remaining height in the cell */
        }

        .original-text {
          white-space: pre-wrap;
          min-height: 150px;
        }

        .editable-summary-textarea {
          flex-grow: 1;
        }

        .editable-summary-textarea::part(textarea) {
          min-height: 150px;
          height: 100%;
        }

        /* Write/Preview Tabs */
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
          background: var(--sl-color-neutral-0);
          border: 1px solid var(--sl-color-neutral-200);
          padding: 0.8rem;
          border-radius: 4px;
          min-height: 150px;
          flex-grow: 1;
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

        /* Links Layouts */
        .original-links {
          min-height: 120px;
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
          min-height: 120px;
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

        /* Bypass Container */
        .bypass-container {
          margin-top: 1.5rem;
          padding: 1rem;
          background: var(--sl-color-warning-50);
          border: 1px solid var(--sl-color-warning-200);
          border-radius: 4px;
        }

        /* Error Message */
        .error-message {
          color: var(--sl-color-danger-600);
          font-weight: 500;
          margin-bottom: 0.5rem;
          width: 100%;
          text-align: left;
        }

        /* Footer Container & Actions */
        .dialog-footer-container {
          display: flex;
          flex-direction: column;
          width: 100%;
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

        /* Conflict Pane styles */
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

        /* Baseline Radio Card Group */
        sl-radio-group {
          width: 100%;
        }

        sl-radio-group::part(form-control-input) {
          display: flex;
          flex-direction: column;
          width: 100%;
        }

        .baseline-radio-group {
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
          width: 100%;
        }

        /* Styled Interactive Cards */
        .baseline-card {
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: 6px;
          padding: 0.9rem;
          transition: all 0.2s ease;
          background: var(--sl-color-neutral-0);
          cursor: pointer;
        }

        .baseline-card:hover {
          border-color: var(--sl-color-neutral-400);
        }

        .baseline-card.selected {
          border-color: var(--sl-color-primary-600);
          box-shadow: 0 0 0 1px var(--sl-color-primary-600);
        }

        /* AI Suggested Highlight Card Style */
        .baseline-card.ai-suggested {
          background: #f4f8ff; /* Subtle Gemini Blue */
          border-color: #d0e2ff;
        }

        .baseline-card.ai-suggested.selected {
          border-color: var(--sl-color-primary-600);
          box-shadow: 0 0 0 1px var(--sl-color-primary-600);
          background: var(
            --sl-color-neutral-0
          ); /* Revert back to neutral background on select for better focus */
        }

        /* Card layout details */
        .baseline-card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          width: 100%;
        }

        .baseline-card-label-left {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
        }

        .baseline-card-icon {
          width: 14px;
          height: 14px;
          flex-shrink: 0;
          display: inline-block;
        }

        .baseline-card-description {
          font-size: 0.85rem;
          color: var(--sl-color-neutral-600);
          margin-top: 0.25rem;
          margin-left: 28px; /* Indent under the radio bubble */
        }

        /* Card Dates container */
        .baseline-card-dates {
          margin-top: 0.8rem;
          margin-left: 28px;
          padding-top: 0.8rem;
          border-top: 1px dashed var(--sl-color-neutral-200);
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          animation: slideDown 0.2s ease-out;
        }

        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-5px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .baseline-card-dates sl-input {
          width: 190px;
        }

        .baseline-card-badge {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          flex-shrink: 0;
        }

        /* Divider & Metadata styles for Original Column */
        .compare-section-divider {
          margin-top: 15px;
          border-top: 1px solid var(--sl-color-neutral-200);
          padding-top: 15px;
        }

        .compare-field-header-margin {
          margin-bottom: 5px;
        }

        .baseline-info-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 5px;
        }

        .baseline-badge-flex {
          display: inline-flex;
          align-items: center;
          gap: 4px;
        }

        .baseline-badge-icon-sz {
          width: 12px;
          height: 12px;
          display: inline-block;
        }

        .baseline-date-label {
          font-size: 0.85em;
          color: var(--sl-color-neutral-600);
        }

        .feature-context-meta-list {
          font-size: 0.85em;
          color: var(--sl-color-neutral-600);
          line-height: 1.5;
          margin-top: 5px;
        }

        .feature-context-meta-list div {
          margin-bottom: 0.3rem;
        }

        .feature-context-meta-list a {
          color: var(--sl-color-primary-600);
          text-decoration: none;
        }

        .feature-context-meta-list a:hover {
          text-decoration: underline;
        }

        /* Global Feature Context Metadata Bar */
        .global-feature-context {
          display: flex;
          flex-wrap: wrap;
          gap: 1.5rem;
          background: var(--sl-color-neutral-50);
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: var(--sl-input-border-radius-medium);
          padding: 10px 16px;
          margin-bottom: 1.5rem;
          font-size: 0.85rem;
          color: var(--sl-color-neutral-600);
          line-height: 1.4;
        }

        .context-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .context-label {
          font-weight: 600;
          color: var(--sl-color-neutral-800);
        }

        .context-item a {
          color: var(--sl-color-primary-600);
          text-decoration: none;
        }

        .context-item a:hover {
          text-decoration: underline;
        }

        /* AI Rationale Callout Box */
        .rationale-callout {
          display: flex;
          gap: 10px;
          background: var(--sl-color-primary-50);
          border-left: 4px solid var(--sl-color-primary-500);
          padding: 12px;
          border-radius: 0 4px 4px 0;
          margin-bottom: 1rem;
          font-size: 0.85rem;
          line-height: 1.4;
          color: var(--sl-color-neutral-800);
        }

        .rationale-icon {
          color: var(--sl-color-primary-600);
          font-size: 1.1rem;
          margin-top: 1px;
          flex-shrink: 0;
        }

        .rationale-label {
          font-weight: 600;
          color: var(--sl-color-primary-800);
          margin-right: 4px;
        }

        /* Traceability & Console Log details widget */
        .traceability-details {
          margin-top: 2rem;
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: var(--sl-input-border-radius-medium);
          background: var(--sl-color-neutral-50);
          overflow: hidden;
        }

        .traceability-summary {
          font-weight: 600;
          cursor: pointer;
          color: var(--sl-color-neutral-700);
          font-size: 0.85rem;
          user-select: none;
          padding: 12px 16px;
          background: var(--sl-color-neutral-100);
          transition: background-color 0.2s ease;
        }

        .traceability-summary:hover {
          background: var(--sl-color-neutral-200);
        }

        .traceability-content {
          padding: 16px;
          border-top: 1px solid var(--sl-color-neutral-200);
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        /* Call-To-Action (CTA) to edit prompt */
        .cta-improve-prompt {
          background: var(--sl-color-success-50);
          border: 1px solid var(--sl-color-success-200);
          border-radius: 4px;
          padding: 12px;
          font-size: 0.85rem;
          line-height: 1.5;
          color: var(--sl-color-success-800);
          display: flex;
          align-items: flex-start;
          gap: 8px;
        }

        .cta-icon {
          color: var(--sl-color-success-600);
          font-size: 1.1rem;
          margin-top: 1px;
          flex-shrink: 0;
        }

        /* Console Log style from chromedash-ai-summary-progress */
        .traceability-logs-tray {
          width: 100%;
          max-height: 160px;
          overflow-y: auto;
          background: var(--sl-color-neutral-950);
          border: 1px solid var(--sl-color-neutral-800);
          border-radius: 4px;
          padding: 10px 14px;
          font-family: var(--sl-font-mono);
          font-size: 0.75rem;
          color: var(--sl-color-neutral-300);
          box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }

        /* Thin scrollbar for console tray */
        .traceability-logs-tray::-webkit-scrollbar {
          width: 6px;
        }
        .traceability-logs-tray::-webkit-scrollbar-track {
          background: var(--sl-color-neutral-950);
        }
        .traceability-logs-tray::-webkit-scrollbar-thumb {
          background: var(--sl-color-neutral-800);
          border-radius: 3px;
        }

        .trace-line {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          line-height: 1.5;
          margin-bottom: 4px;
        }

        .trace-line:last-child {
          margin-bottom: 0;
        }

        .trace-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 14px;
          height: 14px;
          margin-top: 2px;
        }

        .trace-line.in_progress {
          color: var(--sl-color-primary-400);
        }
        .trace-line.success {
          color: var(--sl-color-success-400);
        }
        .trace-line.failed {
          color: var(--sl-color-danger-400);
        }
        .trace-line.retrying {
          color: var(--sl-color-warning-400);
        }
        .trace-line.pruned-marker-line {
          color: var(--sl-color-neutral-500);
          font-style: italic;
        }

        .trace-time {
          color: var(--sl-color-neutral-600);
          user-select: none;
          min-width: 135px; /* Fits YYYY-MM-DD HH:MM:SS */
        }

        .trace-msg {
          flex-grow: 1;
          word-break: break-word;
        }

        .trace-elapsed {
          color: var(--sl-color-neutral-500);
          text-align: right;
          min-width: 45px;
          user-select: none;
        }

        /* Visual Diff Styling */
        .visual-diff-container {
          display: flex;
          flex-direction: column;
          border: 1px solid var(--sl-color-neutral-200);
          border-radius: 4px;
          background: var(--sl-color-neutral-0);
          overflow: hidden;
          max-height: 300px;
          overflow-y: auto;
        }

        .diff-line {
          padding: 0.25rem 0.5rem;
          font-family: var(--sl-font-mono);
          font-size: 0.85rem;
          line-height: 1.5;
          white-space: pre-wrap;
          word-break: break-all;
        }

        .diff-line.unchanged {
          color: var(--sl-color-neutral-700);
        }

        .diff-line.removed {
          background: var(--sl-color-danger-50);
          color: var(--sl-color-danger-800);
          border-left: 3px solid var(--sl-color-danger-500);
        }

        .diff-line.added {
          background: var(--sl-color-success-50);
          color: var(--sl-color-success-800);
          border-left: 3px solid var(--sl-color-success-500);
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
  activeTab: 'edit' | 'diff' | 'preview' = 'edit';

  get isLocked() {
    return this.suggestion?.status === 'disputed' || this.suggestion?.status === 'finalized';
  }
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
  @state()
  editingBaselineStatus = 'none';
  @state()
  editingBaselineNewlyDate = '';
  @state()
  editingBaselineWidelyDate = '';
  @state()
  bypassAction: 'apply' | 'discard' = 'apply';

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
    this.bypassAction = 'apply';
    this.bypassJustification = '';
    this.activeTab = 'edit';
    this.isDirty = false;
    this.inConflict = false;
    this.serverSummaryText = '';
    this.serverLinksList = [];
    this.serverVersionToken = this.suggestion.version_token || 1;
    this.editingBaselineStatus = this.suggestion.baseline_status || 'none';
    this.editingBaselineNewlyDate = this.suggestion.baseline_newly_date || '';
    this.editingBaselineWidelyDate = this.suggestion.baseline_widely_date || '';

    void this.dialogEl.show();
  }

  hide() {
    void this.dialogEl.hide();
  }

  useOriginalSummaryOnly() {
    if (this.isLocked) return;
    if (this.feature) {
      this.summaryText = this.feature.summary || '';
      this.isDirty = true;
    }
  }

  useAISummaryOnly() {
    if (this.isLocked) return;
    if (this.suggestion) {
      this.summaryText = this.suggestion.suggested_summary || '';
      this.isDirty = true;
    }
  }

  useOriginalLinksOnly() {
    if (this.isLocked) return;
    if (this.feature) {
      const featureLinks = this.feature.resources?.docs || [];
      this.linksList = featureLinks.map(url => ({url, approved: true}));
      this.isDirty = true;
    }
  }

  useAILinksOnly() {
    if (this.isLocked) return;
    if (this.suggestion) {
      const aiLinks = this.suggestion.suggested_doc_links || [];
      this.linksList = aiLinks.map(url => ({url, approved: true}));
      this.isDirty = true;
    }
  }

  toggleLinkApproved(index: number) {
    if (this.isLocked) return;
    this.linksList[index].approved = !this.linksList[index].approved;
    this.linksList = [...this.linksList];
    this.isDirty = true;
  }

  addNewLink() {
    if (this.isLocked) return;
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

  renderAIBaselineInfo() {
    if (
      !this.suggestion ||
      !this.suggestion.baseline_status ||
      this.suggestion.baseline_status === 'none'
    ) {
      return nothing;
    }

    let label = '';
    let variant = '';
    let iconSrc = '';
    let dateLabel = '';

    switch (this.suggestion.baseline_status) {
      case 'widely':
        label = 'Baseline Widely Available';
        variant = 'success';
        iconSrc = '/static/img/baseline-widely-icon.svg';
        if (this.suggestion.baseline_widely_date) {
          dateLabel = `Widely Available since ${this.suggestion.baseline_widely_date}`;
        } else if (this.suggestion.baseline_newly_date) {
          dateLabel = `Newly Available on ${this.suggestion.baseline_newly_date}`;
        }
        break;
      case 'newly':
        label = 'Baseline Newly Available';
        variant = 'primary';
        iconSrc = '/static/img/baseline-newly-icon.svg';
        if (this.suggestion.baseline_newly_date) {
          dateLabel = `Newly Available since ${this.suggestion.baseline_newly_date}`;
        }
        break;
      case 'limited':
        label = 'Baseline Limited';
        variant = 'warning';
        iconSrc = '/static/img/baseline-limited-icon.svg';
        break;
      default:
        return nothing;
    }

    return html`
      <div class="compare-section-divider">
        <div class="field-header compare-field-header-margin">
          <strong>AI-Evaluated Baseline Status</strong>
        </div>
        <div class="baseline-info-row">
          <sl-tag
            variant=${variant}
            size="small"
            class="baseline-badge-flex"
            pill
          >
            <img src="${iconSrc}" class="baseline-badge-icon-sz" alt="" />
            ${label}
          </sl-tag>
          ${dateLabel
            ? html` <span class="baseline-date-label">${dateLabel}</span> `
            : nothing}
        </div>
      </div>
    `;
  }

  renderOriginalBaselineInfo() {
    if (!this.suggestion) return nothing;

    const status = this.suggestion.original_baseline_status || 'none';
    const newlyDate = this.suggestion.original_baseline_newly_date;
    const widelyDate = this.suggestion.original_baseline_widely_date;

    if (status === 'none') {
      return html`
        <div class="compare-section-divider">
          <div class="field-header compare-field-header-margin">
            <strong>Original Baseline Status</strong>
          </div>
          <div class="baseline-info-row">
            <sl-tag
              variant="neutral"
              size="small"
              class="baseline-badge-flex"
              pill
              data-testid="original-baseline-badge"
            >
              None (Not Set)
            </sl-tag>
          </div>
        </div>
      `;
    }

    let label = '';
    let variant = '';
    let iconSrc = '';
    let dateLabel = '';

    switch (status) {
      case 'widely':
        label = 'Baseline Widely Available';
        variant = 'success';
        iconSrc = '/static/img/baseline-widely-icon.svg';
        if (widelyDate) {
          dateLabel = `Widely Available since ${widelyDate}`;
        } else if (newlyDate) {
          dateLabel = `Newly Available on ${newlyDate}`;
        }
        break;
      case 'newly':
        label = 'Baseline Newly Available';
        variant = 'primary';
        iconSrc = '/static/img/baseline-newly-icon.svg';
        if (newlyDate) {
          dateLabel = `Newly Available since ${newlyDate}`;
        }
        break;
      case 'limited':
        label = 'Baseline Limited';
        variant = 'warning';
        iconSrc = '/static/img/baseline-limited-icon.svg';
        break;
      default:
        return nothing;
    }

    return html`
      <div class="compare-section-divider">
        <div class="field-header compare-field-header-margin">
          <strong>Original Baseline Status</strong>
        </div>
        <div class="baseline-info-row">
          <sl-tag
            variant=${variant}
            size="small"
            class="baseline-badge-flex"
            pill
            data-testid="original-baseline-badge"
          >
            <img src="${iconSrc}" class="baseline-badge-icon-sz" alt="" />
            ${label}
          </sl-tag>
          ${dateLabel
            ? html` <span class="baseline-date-label">${dateLabel}</span> `
            : nothing}
        </div>
      </div>
    `;
  }

  // Master selector helper that handles status changes and date clearing
  selectBaselineStatus(status: string) {
    if (this.isLocked) return;
    if (this.submitting || this.editingBaselineStatus === status) return;
    this.editingBaselineStatus = status;

    // Enforce strict date clearing logic to prevent sending stale parameters
    if (status === 'none' || status === 'limited') {
      this.editingBaselineNewlyDate = '';
      this.editingBaselineWidelyDate = '';
    } else if (status === 'newly') {
      this.editingBaselineWidelyDate = '';
    }

    this.isDirty = true;
    this.validateBaselineDates();
  }

  // Use Original Baseline Action
  useOriginalBaseline() {
    if (this.isLocked) return;
    if (!this.suggestion) return;
    const origStatus = this.suggestion.original_baseline_status || 'none';

    this.editingBaselineStatus = origStatus;
    this.editingBaselineNewlyDate =
      this.suggestion.original_baseline_newly_date || '';
    this.editingBaselineWidelyDate =
      this.suggestion.original_baseline_widely_date || '';

    this.isDirty = true;
    this.validateBaselineDates();
  }

  // Use AI Baseline Action
  useAIBaseline() {
    if (this.isLocked) return;
    if (!this.suggestion) return;
    const aiStatus = this.suggestion.baseline_status || 'none';

    this.editingBaselineStatus = aiStatus;
    this.editingBaselineNewlyDate = this.suggestion.baseline_newly_date || '';
    this.editingBaselineWidelyDate = this.suggestion.baseline_widely_date || '';

    this.isDirty = true;
    this.validateBaselineDates();
  }

  // Individual Date Inputs Handlers
  handleNewlyDateChange(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target) {
      this.editingBaselineNewlyDate = target.value;
      this.isDirty = true;
      this.validateBaselineDates();
    }
  }

  handleWidelyDateChange(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target) {
      this.editingBaselineWidelyDate = target.value;
      this.isDirty = true;
      this.validateBaselineDates();
    }
  }

  // Front-end Validation and Inline Error Messages
  validateBaselineDates(): boolean {
    this.errorMessage = '';

    if (this.editingBaselineStatus === 'newly') {
      if (!this.editingBaselineNewlyDate) {
        this.errorMessage =
          'Newly Available Date is required for Baseline Newly Available.';
        return false;
      }
    }

    if (this.editingBaselineStatus === 'widely') {
      if (!this.editingBaselineNewlyDate || !this.editingBaselineWidelyDate) {
        this.errorMessage =
          'Both Newly and Widely Available Dates are required for Baseline Widely Available.';
        return false;
      }

      const newly = new Date(this.editingBaselineNewlyDate);
      const widely = new Date(this.editingBaselineWidelyDate);
      if (widely < newly) {
        this.errorMessage =
          'Widely Available Date must be chronologically after or equal to the Newly Available Date.';
        return false;
      }
    }

    return true;
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

    // Perform date validation
    if (!this.validateBaselineDates()) {
      return; // Stop and display the validation message
    }

    if (this.isBypassRequired() && !this.showBypassUI) {
      this.bypassAction = 'apply';
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
        this.bypassJustification || undefined,
        this.editingBaselineStatus,
        this.editingBaselineStatus !== 'none'
          ? this.editingBaselineNewlyDate || null
          : null,
        this.editingBaselineStatus === 'widely'
          ? this.editingBaselineWidelyDate || null
          : null
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

    if (this.isBypassRequired() && !this.showBypassUI) {
      this.bypassAction = 'discard';
      this.showBypassUI = true;
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    try {
      await window.csClient.patchSummarySuggestion(
        this.feature.id,
        'discarded',
        this.suggestion.version_token,
        undefined,
        undefined,
        this.bypassJustification || undefined
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

  renderVisualDiff() {
    const original = this.feature?.summary || '';
    const curated = this.summaryText;
    const originalLines = original.split('\n');
    const curatedLines = curated.split('\n');
    const diffLines: any[] = [];
    const maxLines = Math.max(originalLines.length, curatedLines.length);
    for (let i = 0; i < maxLines; i++) {
      const origLine = originalLines[i];
      const curLine = curatedLines[i];
      if (origLine === curLine) {
        if (origLine !== undefined) {
          diffLines.push(html`<div class="diff-line unchanged">${origLine}</div>`);
        }
      } else {
        if (origLine !== undefined) {
          diffLines.push(html`<div class="diff-line removed">- ${origLine}</div>`);
        }
        if (curLine !== undefined) {
          diffLines.push(html`<div class="diff-line added">+ ${curLine}</div>`);
        }
      }
    }
    return html`
      <div class="visual-diff-container">
        ${diffLines}
      </div>
    `;
  }

  async keepCuratedVersion() {
    if (!this.feature || !this.suggestion) return;
    if (this.suggestion.drift_detected === 'major') return;
    if (!confirm('Are you sure you want to keep the curated version and dismiss the minor drift warning?')) {
      return;
    }
    this.submitting = true;
    try {
      await window.csClient.patchSummarySuggestion(
        this.feature.id,
        'applied',
        this.suggestion.version_token,
        this.summaryText,
        this.linksList.filter(l => l.approved).map(l => l.url),
        this.editingBaselineStatus,
        this.editingBaselineNewlyDate || null,
        this.editingBaselineWidelyDate || null
      );
      
      this.dispatchEvent(
        new CustomEvent<{summary: string; links: string[]}>('applied', {
          detail: {
            summary: this.summaryText,
            links: this.linksList.filter(l => l.approved).map(l => l.url),
          },
        })
      );
      showToastMessage('Curated version kept. Drift warning resolved.');
      this.hide();
    } catch (err) {
      console.error(err);
      this.errorMessage = 'Failed to keep curated version.';
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
                  <div
                    class="original-text"
                    data-testid="server-summary-reference"
                  >
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
                  <div
                    class="original-text"
                    data-testid="local-summary-draft-reference"
                  >
                    ${this.summaryText}
                  </div>
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
              ${
                this.suggestion?.status === 'skipped'
                  ? html`
                      <sl-alert
                        variant="neutral"
                        open
                        style="margin-bottom: 1.5rem; border-left: 4px solid var(--sl-color-neutral-400);"
                      >
                        <sl-icon
                          slot="icon"
                          name="robot"
                          style="font-size: 1.25rem; color: var(--sl-color-neutral-600);"
                        ></sl-icon>
                        <strong style="color: var(--sl-color-neutral-800);"
                          >AI Summary Generation Skipped</strong
                        ><br />
                        The summary generator evaluated this feature and decided
                        to skip automatic generation.<br />
                        <strong>Reason:</strong>
                        <em
                          >${this.suggestion.generation_rationale ||
                          'Insufficient technical details or documentation to generate confidently.'}</em
                        >
                      </sl-alert>
                    `
                  : nothing
              }

              ${this.suggestion?.status === 'out_of_date'
                ? html`
                    <sl-alert variant="warning" open style="margin-bottom: 1.5rem;">
                      <sl-icon slot="icon" name="exclamation-triangle"></sl-icon>
                      <strong>Out-of-Date Curation (Drift Detected):</strong> The original summary or fields have been modified by the owner since this suggestion was curated.
                      ${this.suggestion.drift_detected === 'major'
                        ? html`<br /><span style="color: var(--sl-color-danger-600); font-weight: bold;">Major Drift: The original summary has changed significantly. Curation is out of date and must be revised manually or re-generated.</span>`
                        : html`<br />Minor Drift: The changes are minor. You can keep your curated version or revise it.`}
                    </sl-alert>
                  `
                : nothing}

              <!-- Global Feature Context Metadata Bar (Top-Level) -->
              <div class="global-feature-context">
                ${
                  this.feature?.blink_components?.length
                    ? html`
                        <div class="context-item">
                          <span class="context-label">Blink Components:</span>
                          <span>${this.feature.blink_components.join(', ')}</span>
                        </div>
                      `
                    : nothing
                }
                ${
                  this.feature?.web_feature
                    ? html`
                        <div class="context-item">
                          <span class="context-label">WebDX Feature:</span>
                          <sl-badge variant="neutral" pill
                            >${this.feature.web_feature}</sl-badge
                          >
                        </div>
                      `
                    : nothing
                }
                ${
                  this.feature?.spec_link
                    ? html`
                        <div class="context-item">
                          <span class="context-label">Spec Link:</span>
                          <a
                            href="${this.feature.spec_link}"
                            target="_blank"
                            rel="noopener"
                            >Specification</a
                          >
                        </div>
                      `
                    : nothing
                }
                ${
                  this.feature?.explainer_links?.length
                    ? html`
                        <div class="context-item">
                          <span class="context-label">Explainers:</span>
                          <span>
                            ${(this.feature?.explainer_links || []).map(
                              (link, idx) => html`
                                <a href="${link}" target="_blank" rel="noopener"
                                  >Explainer ${idx + 1}</a
                                >${idx <
                                (this.feature?.explainer_links || []).length - 1
                                  ? ', '
                                  : ''}
                              `
                            )}
                          </span>
                        </div>
                      `
                    : nothing
                }
              </div>

              <!-- Top-Level symmetrical 3-tab header -->
              <div class="curation-tab-header" role="tablist" aria-label="Curation workspace tabs" style="margin-bottom: 1.5rem; border-bottom: 1px solid var(--sl-color-neutral-200); display: flex; gap: 1rem;">
                <button class="tab-btn ${this.activeTab === 'edit' ? 'active' : ''}" role="tab" aria-selected=${this.activeTab === 'edit'} @click=${() => { this.activeTab = 'edit'; }} style="background: none; border: none; padding: 0.5rem 1rem; cursor: pointer; font-weight: bold; border-bottom: 2px solid ${this.activeTab === 'edit' ? 'var(--sl-color-primary-500)' : 'transparent'}; color: ${this.activeTab === 'edit' ? 'var(--sl-color-primary-600)' : 'var(--sl-color-neutral-600)'};">
                  Review & Edit
                </button>
                <button class="tab-btn ${this.activeTab === 'diff' ? 'active' : ''}" role="tab" aria-selected=${this.activeTab === 'diff'} @click=${() => { this.activeTab = 'diff'; }} style="background: none; border: none; padding: 0.5rem 1rem; cursor: pointer; font-weight: bold; border-bottom: 2px solid ${this.activeTab === 'diff' ? 'var(--sl-color-primary-500)' : 'transparent'}; color: ${this.activeTab === 'diff' ? 'var(--sl-color-primary-600)' : 'var(--sl-color-neutral-600)'};">
                  Visual Diff
                </button>
                <button class="tab-btn ${this.activeTab === 'preview' ? 'active' : ''}" role="tab" aria-selected=${this.activeTab === 'preview'} @click=${() => { this.activeTab = 'preview'; }} style="background: none; border: none; padding: 0.5rem 1rem; cursor: pointer; font-weight: bold; border-bottom: 2px solid ${this.activeTab === 'preview' ? 'var(--sl-color-primary-500)' : 'transparent'}; color: ${this.activeTab === 'preview' ? 'var(--sl-color-primary-600)' : 'var(--sl-color-neutral-600)'};">
                  Preview
                </button>
              </div>

              <!-- Tab Contents -->
              <div class="curation-tab-contents" style="margin-bottom: 1.5rem;">
                ${this.activeTab === 'diff'
                  ? this.renderVisualDiff()
                  : this.activeTab === 'preview'
                  ? html`
                      <div class="preview-container" data-testid="summary-preview-container" style="padding: 1rem; border: 1px solid var(--sl-color-neutral-200); border-radius: 4px; min-height: 200px; background: #fff;">
                        ${autolink(this.summaryText, [], true)}
                      </div>
                    `
                  : html`
                      <!-- activeTab === 'edit' -->
                      <fieldset ?disabled=${this.isLocked} style="border: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 1.5rem;">
                        <!-- ==================== ROW 1: SUMMARY REVIEW ==================== -->
                        <div class="review-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                          <!-- Left Column: Original (Read-Only) -->
                          <div class="review-cell left-cell" style="background: var(--sl-color-neutral-50); padding: 1rem; border-radius: 4px; border: 1px solid var(--sl-color-neutral-200); overflow-y: auto; max-height: 300px;">
                            <h4 class="section-title" style="margin-top: 0;">Original Feature Details</h4>
                            <div class="field-header">
                              <strong>Original Summary</strong>
                            </div>
                            <div class="original-text" data-testid="original-summary" style="white-space: pre-wrap; font-size: 0.9rem;">
                              ${this.feature?.summary || 'No summary'}
                            </div>
                          </div>

                          <!-- Right Column: Interactive Workspace (Draft) -->
                          <div class="review-cell right-cell" style="display: flex; flex-direction: column; gap: 0.75rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                              <h4 class="section-title" style="margin: 0;">Interactive Workspace (Draft)</h4>
                              ${
                                this.suggestion?.status !== 'skipped'
                                  ? html`
                                      <sl-button-group
                                        label="Copy original or suggested text"
                                      >
                                        <sl-button
                                          size="small"
                                          @click=${this.useOriginalSummaryOnly}
                                          ?disabled=${this.submitting || this.isLocked}
                                          >Use Original</sl-button
                                        >
                                        <sl-button
                                          size="small"
                                          @click=${this.useAISummaryOnly}
                                          ?disabled=${this.submitting || this.isLocked}
                                          >Use AI</sl-button
                                        >
                                      </sl-button-group>
                                    `
                                  : nothing
                              }
                            </div>

                            <sl-textarea
                              class="editable-summary-textarea"
                              data-testid="suggested-summary-textarea"
                              aria-label="Suggested Summary"
                              .value=${this.summaryText}
                              ?disabled=${this.submitting || this.isLocked}
                              @sl-input=${(e: Event) => {
                                const target = e.target;
                                if (target && 'value' in target) {
                                  this.summaryText = String(target.value);
                                  this.isDirty = true;
                                }
                              }}
                              style="flex-grow: 1;"
                              rows="10"
                            ></sl-textarea>
                          </div>
                        </div>

                        <!-- ==================== ROW 2: DOCUMENTATION LINKS REVIEW ==================== -->
                        <div class="review-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                          <!-- Left Column: Original (Read-Only) -->
                          <div class="review-cell left-cell" style="background: var(--sl-color-neutral-50); padding: 1rem; border-radius: 4px; border: 1px solid var(--sl-color-neutral-200);">
                            <div class="field-header">
                              <strong>Original Doc Links</strong>
                            </div>
                            <div class="original-links" style="font-size: 0.9rem;">
                              ${
                                this.feature?.resources?.docs?.length
                                  ? this.feature.resources.docs.map(
                                      link => html`
                                        <div class="original-link-row">
                                          &bull;
                                          <a href=${link} target="_blank">${link}</a>
                                        </div>
                                      `
                                    )
                                  : 'No doc links'
                              }
                            </div>
                          </div>

                          <!-- Right Column: Interactive Workspace (Draft) -->
                          <div class="review-cell right-cell" style="display: flex; flex-direction: column; gap: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                              <strong style="font-size: 0.95rem;">Final Documentation Links</strong>
                              <sl-button-group label="Use original or suggested links">
                                <sl-button
                                  size="small"
                                  @click=${this.useOriginalLinksOnly}
                                  ?disabled=${this.submitting || this.isLocked}
                                >
                                  Use Original
                                </sl-button>
                                <sl-button
                                  size="small"
                                  @click=${this.useAILinksOnly}
                                  ?disabled=${this.submitting || this.isLocked}
                                >
                                  Use AI
                                </sl-button>
                              </sl-button-group>
                            </div>

                            <div class="suggested-links-container" style="display: flex; flex-direction: column; gap: 0.5rem;">
                              <div class="editable-links-list" style="max-height: 150px; overflow-y: auto; display: flex; flex-direction: column; gap: 0.25rem;">
                                ${this.linksList.map(
                                  (item, idx) => html`
                                    <div class="link-edit-row" style="display: flex; align-items: center; gap: 0.5rem;">
                                      <sl-checkbox
                                        data-testid="link-checkbox-${idx}"
                                        aria-label="Approve link: ${item.url}"
                                        ?checked=${item.approved}
                                        ?disabled=${this.submitting || this.isLocked}
                                        @sl-change=${() => this.toggleLinkApproved(idx)}
                                      ></sl-checkbox>
                                      <a href=${item.url} target="_blank" style="font-size: 0.9rem;"
                                        >${item.url}</a
                                      >
                                    </div>
                                  `
                                )}
                              </div>

                              <div class="add-link-container" style="display: flex; gap: 0.5rem; align-items: center;">
                                <sl-input
                                  size="small"
                                  placeholder="Add custom doc link URL..."
                                  aria-label="New document link URL"
                                  .value=${this.newLinkLabelInput}
                                  ?disabled=${this.submitting || this.isLocked}
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
                                  ?disabled=${this.submitting || this.isLocked}
                                  >Add</sl-button
                                >
                              </div>
                            </div>
                          </div>
                        </div>

                        <!-- ==================== ROW 3: BASELINE STATUS REVIEW ==================== -->
                        <div class="review-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                          <!-- Left Column: Original Status (Read-Only) -->
                          <div class="review-cell left-cell" style="background: var(--sl-color-neutral-50); padding: 1rem; border-radius: 4px; border: 1px solid var(--sl-color-neutral-200);">
                            <!-- Render dynamic original baseline badges and dates -->
                            ${this.renderOriginalBaselineInfo()}
                          </div>

                          <!-- Right Column: Interactive Radio Cards Workspace -->
                          <div class="review-cell right-cell" style="display: flex; flex-direction: column; gap: 0.5rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                              <strong style="font-size: 0.95rem;">Final Baseline Status</strong>
                              <sl-button-group
                                label="Use original or suggested baseline status"
                              >
                                <sl-button
                                  size="small"
                                  @click=${this.useOriginalBaseline}
                                  ?disabled=${this.submitting || this.isLocked}
                                >
                                  Use Original
                                </sl-button>
                                <sl-button
                                  size="small"
                                  @click=${this.useAIBaseline}
                                  ?disabled=${this.submitting || this.isLocked}
                                >
                                  Use AI
                                </sl-button>
                              </sl-button-group>
                            </div>

                            <sl-radio-group
                              .value=${this.editingBaselineStatus || 'none'}
                            >
                              <div class="baseline-radio-group" style="display: flex; flex-direction: column; gap: 0.5rem;">
                                <!-- Option 1: None (No Baseline Status) -->
                                <div
                                  class="baseline-card ${
                                    this.editingBaselineStatus === 'none'
                                      ? 'selected'
                                      : ''
                                  }"
                                  @click=${() => this.selectBaselineStatus('none')}
                                  style="border: 1px solid var(--sl-color-neutral-200); padding: 0.75rem; border-radius: 4px; cursor: pointer; transition: all 0.15s ease;"
                                >
                                  <div class="baseline-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                                    <div class="baseline-card-label-left">
                                      <sl-radio
                                        value="none"
                                        ?disabled=${this.submitting || this.isLocked}
                                        @click=${() => this.selectBaselineStatus('none')}
                                      >
                                        None (No Baseline Status)
                                      </sl-radio>
                                    </div>
                                    ${
                                      this.suggestion?.original_baseline_status ===
                                        'none' ||
                                      !this.suggestion?.original_baseline_status
                                        ? html`<sl-tag
                                            size="small"
                                            variant="neutral"
                                            class="baseline-card-badge"
                                            >Original</sl-tag
                                          >`
                                        : nothing
                                    }
                                  </div>
                                  <div class="baseline-card-description" style="font-size: 0.85rem; color: var(--sl-color-neutral-500); margin-top: 0.25rem;">
                                    Keep this feature without a baseline status, or
                                    reject the suggestion.
                                  </div>
                                </div>

                                <!-- Option 2: Baseline Limited -->
                                <div
                                  class="baseline-card ${
                                    this.editingBaselineStatus === 'limited'
                                      ? 'selected'
                                      : ''
                                  } ${
                                    this.suggestion?.baseline_status === 'limited'
                                      ? 'ai-suggested'
                                      : ''
                                  }"
                                  @click=${() => this.selectBaselineStatus('limited')}
                                  style="border: 1px solid var(--sl-color-neutral-200); padding: 0.75rem; border-radius: 4px; cursor: pointer; transition: all 0.15s ease;"
                                >
                                  <div class="baseline-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                                    <div class="baseline-card-label-left">
                                      <sl-radio
                                        value="limited"
                                        ?disabled=${this.submitting || this.isLocked}
                                        @click=${() => this.selectBaselineStatus('limited')}
                                      >
                                        <span
                                          style="display: inline-flex; align-items: center; gap: 6px;"
                                        >
                                          <img
                                            src="/static/img/baseline-limited-icon.svg"
                                            class="baseline-card-icon"
                                            alt=""
                                            style="width: 16px; height: 16px;"
                                          />
                                          Baseline Limited
                                        </span>
                                      </sl-radio>
                                    </div>
                                    <div style="display: flex; gap: 4px;">
                                      ${
                                        this.suggestion?.baseline_status === 'limited'
                                          ? html`<sl-tag
                                              size="small"
                                              variant="primary"
                                              class="baseline-card-badge"
                                              >AI Suggested</sl-tag
                                            >`
                                          : nothing
                                      }
                                      ${
                                        this.suggestion?.original_baseline_status ===
                                        'limited'
                                          ? html`<sl-tag
                                              size="small"
                                              variant="neutral"
                                              class="baseline-card-badge"
                                              >Original</sl-tag
                                            >`
                                          : nothing
                                      }
                                    </div>
                                  </div>
                                  <div class="baseline-card-description" style="font-size: 0.85rem; color: var(--sl-color-neutral-500); margin-top: 0.25rem;">
                                    The feature has limited support or is only available
                                    in some browsers.
                                  </div>
                                </div>

                                <!-- Option 3: Baseline Newly Available -->
                                <div
                                  class="baseline-card ${
                                    this.editingBaselineStatus === 'newly'
                                      ? 'selected'
                                      : ''
                                  } ${
                                    this.suggestion?.baseline_status === 'newly'
                                      ? 'ai-suggested'
                                      : ''
                                  }"
                                  @click=${() => this.selectBaselineStatus('newly')}
                                  style="border: 1px solid var(--sl-color-neutral-200); padding: 0.75rem; border-radius: 4px; cursor: pointer; transition: all 0.15s ease;"
                                >
                                  <div class="baseline-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                                    <div class="baseline-card-label-left">
                                      <sl-radio
                                        value="newly"
                                        ?disabled=${this.submitting || this.isLocked}
                                        @click=${() => this.selectBaselineStatus('newly')}
                                      >
                                        <span
                                          style="display: inline-flex; align-items: center; gap: 6px;"
                                        >
                                          <img
                                            src="/static/img/baseline-newly-icon.svg"
                                            class="baseline-card-icon"
                                            alt=""
                                            style="width: 16px; height: 16px;"
                                          />
                                          Baseline Newly Available
                                        </span>
                                      </sl-radio>
                                    </div>
                                    <div style="display: flex; gap: 4px;">
                                      ${
                                        this.suggestion?.baseline_status === 'newly'
                                          ? html`<sl-tag
                                              size="small"
                                              variant="primary"
                                              class="baseline-card-badge"
                                              >AI Suggested</sl-tag
                                            >`
                                          : nothing
                                      }
                                      ${
                                        this.suggestion?.original_baseline_status ===
                                        'newly'
                                          ? html`<sl-tag
                                              size="small"
                                              variant="neutral"
                                              class="baseline-card-badge"
                                              >Original</sl-tag
                                            >`
                                          : nothing
                                      }
                                    </div>
                                  </div>
                                  <div class="baseline-card-description" style="font-size: 0.85rem; color: var(--sl-color-neutral-500); margin-top: 0.25rem;">
                                    Supported across all major browser engines. Requires
                                    newly available date.
                                  </div>

                                  <!-- Embedded Conditional Newly Available Date Picker -->
                                  ${
                                    this.editingBaselineStatus === 'newly'
                                      ? html`
                                          <div
                                            class="baseline-card-dates"
                                            @click=${(e: Event) => e.stopPropagation()}
                                            style="margin-top: 0.5rem; display: flex; gap: 0.5rem;"
                                          >
                                            <sl-input
                                              type="date"
                                              size="small"
                                              label="Newly Available Date"
                                              .value=${this.editingBaselineNewlyDate ||
                                              ''}
                                              ?disabled=${this.submitting || this.isLocked}
                                              @sl-input=${this.handleNewlyDateChange}
                                              required
                                              style="width: 100%;"
                                            ></sl-input>
                                          </div>
                                        `
                                      : nothing
                                  }
                                </div>

                                <!-- Option 4: Baseline Widely Available -->
                                <div
                                  class="baseline-card ${
                                    this.editingBaselineStatus === 'widely'
                                      ? 'selected'
                                      : ''
                                  } ${
                                    this.suggestion?.baseline_status === 'widely'
                                      ? 'ai-suggested'
                                      : ''
                                  }"
                                  @click=${() => this.selectBaselineStatus('widely')}
                                  style="border: 1px solid var(--sl-color-neutral-200); padding: 0.75rem; border-radius: 4px; cursor: pointer; transition: all 0.15s ease;"
                                >
                                  <div class="baseline-card-header" style="display: flex; justify-content: space-between; align-items: center;">
                                    <div class="baseline-card-label-left">
                                      <sl-radio
                                        value="widely"
                                        ?disabled=${this.submitting || this.isLocked}
                                        @click=${() => this.selectBaselineStatus('widely')}
                                      >
                                        <span
                                          style="display: inline-flex; align-items: center; gap: 6px;"
                                        >
                                          <img
                                            src="/static/img/baseline-widely-icon.svg"
                                            class="baseline-card-icon"
                                            alt=""
                                            style="width: 16px; height: 16px;"
                                          />
                                          Baseline Widely Available
                                        </span>
                                      </sl-radio>
                                    </div>
                                    <div style="display: flex; gap: 4px;">
                                      ${
                                        this.suggestion?.baseline_status === 'widely'
                                          ? html`<sl-tag
                                              size="small"
                                              variant="primary"
                                              class="baseline-card-badge"
                                              >AI Suggested</sl-tag
                                            >`
                                          : nothing
                                      }
                                      ${
                                        this.suggestion?.original_baseline_status ===
                                        'widely'
                                          ? html`<sl-tag
                                              size="small"
                                              variant="neutral"
                                              class="baseline-card-badge"
                                              >Original</sl-tag
                                            >`
                                          : nothing
                                      }
                                    </div>
                                  </div>
                                  <div class="baseline-card-description" style="font-size: 0.85rem; color: var(--sl-color-neutral-500); margin-top: 0.25rem;">
                                    Supported in all major engines for 30+ months.
                                    Requires newly and widely available dates.
                                  </div>

                                  <!-- Embedded Conditional Widely Available Date Pickers -->
                                  ${
                                    this.editingBaselineStatus === 'widely'
                                      ? html`
                                          <div
                                            class="baseline-card-dates"
                                            @click=${(e: Event) => e.stopPropagation()}
                                            style="margin-top: 0.5rem; display: flex; gap: 0.5rem;"
                                          >
                                            <sl-input
                                              type="date"
                                              size="small"
                                              label="Newly Available Date"
                                              .value=${this.editingBaselineNewlyDate ||
                                              ''}
                                              ?disabled=${this.submitting || this.isLocked}
                                              @sl-input=${this.handleNewlyDateChange}
                                              required
                                              style="flex: 1;"
                                            ></sl-input>
                                            <sl-input
                                              type="date"
                                              size="small"
                                              label="Widely Available Date"
                                              .value=${this.editingBaselineWidelyDate ||
                                              ''}
                                              ?disabled=${this.submitting || this.isLocked}
                                              @sl-input=${this.handleWidelyDateChange}
                                              required
                                              style="flex: 1;"
                                            ></sl-input>
                                          </div>
                                        `
                                      : nothing
                                  }
                                </div>
                              </div>
                            </sl-radio-group>
                          </div>
                        </div>
                      </fieldset>
                    `}
              </div>

              <!-- AI Rationale Expandable Details (Full-Width) -->
              ${
                this.suggestion?.generation_rationale
                  ? html`
                      <details class="rationale-details" open style="border: 1px solid var(--sl-color-neutral-200); border-radius: 4px; margin-bottom: 1.5rem; background: var(--sl-color-neutral-50);">
                        <summary class="rationale-summary" style="padding: 0.75rem; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                          <sl-icon
                            class="rationale-icon"
                            name="lightbulb-fill"
                            style="color: var(--sl-color-warning-500);"
                          ></sl-icon>
                          💡 AI Generation & Enrichment Rationale
                        </summary>
                        <div class="rationale-content" style="padding: 0 0.75rem 0.75rem 0.75rem; border-top: 1px solid var(--sl-color-neutral-200); background: #fff; font-size: 0.9rem;">
                          <div class="rationale-markdown-body">
                            ${autolink(
                              this.suggestion.generation_rationale,
                              [],
                              true
                            )}
                          </div>
                        </div>
                      </details>
                    `
                  : nothing
              }

              <!-- Traceability Details & Console Logs (Bottom-Level, Full-Width) -->
              <details class="traceability-details" style="border: 1px solid var(--sl-color-neutral-200); border-radius: 4px; margin-bottom: 1.5rem;">
                  <summary class="traceability-summary" style="padding: 0.75rem; font-weight: bold; cursor: pointer;">
                    🔍 View Generation & Traceability Logs
                  </summary>
                  <div class="traceability-content" style="padding: 0.75rem; border-top: 1px solid var(--sl-color-neutral-200);">
                    <!-- Prompt Improvement CTA -->
                    <div class="cta-improve-prompt" style="display: flex; gap: 0.5rem; align-items: center; background: var(--sl-color-neutral-50); padding: 0.5rem; border-radius: 4px; margin-bottom: 0.75rem; font-size: 0.85rem;">
                      <sl-icon class="cta-icon" name="info-circle" style="color: var(--sl-color-primary-500);"></sl-icon>
                      <div>
                        <strong
                          >Want to improve the AI release notes
                          summaries?</strong
                        >
                        You can edit the system guidelines and prompt template
                        in the codebase at
                        <code>framework/prompts/v2.md</code>, or read the
                        guidelines in the <code>README.md</code>. Work with
                        DevRel and writing experts to iterate on prompt styling!
                      </div>
                    </div>

                    <!-- Trace logs console -->
                    <div class="traceability-logs-tray" style="background: #1e1e1e; color: #d4d4d4; font-family: monospace; font-size: 0.8rem; padding: 0.5rem; border-radius: 4px; max-height: 200px; overflow-y: auto;">
                      ${
                        this.suggestion?.progress_steps?.length
                          ? this.suggestion.progress_steps.map(step => {
                              const is_success = step.status === 'success';
                              const is_failed = step.status === 'failed';
                              const is_in_progress =
                                step.status === 'in_progress';
                              const is_retrying = step.status === 'retrying';

                              // Format duration
                              let elapsed = '';
                              if (step.start_timestamp) {
                                const start = new Date(
                                  step.start_timestamp
                                ).getTime();
                                const end = step.end_timestamp
                                  ? new Date(step.end_timestamp).getTime()
                                  : Date.now();
                                const diffMs = end - start;
                                elapsed =
                                  diffMs < 100
                                    ? '+0.1s'
                                    : `+${(diffMs / 1000).toFixed(1)}s`;
                              }

                              // Format time with YYYY-MM-DD HH:MM:SS
                              let formattedTime = '';
                              if (step.start_timestamp) {
                                const d = new Date(step.start_timestamp);
                                const yr = d.getFullYear();
                                const mo = String(d.getMonth() + 1).padStart(
                                  2,
                                  '0'
                                );
                                const dy = String(d.getDate()).padStart(2, '0');
                                const time = d.toLocaleTimeString([], {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                  second: '2-digit',
                                  hour12: false,
                                });
                                formattedTime = `${yr}-${mo}-${dy} ${time}`;
                              }

                              return html`
                                <div class="trace-line ${step.status}" style="display: flex; gap: 0.5rem; margin-bottom: 0.25rem;">
                                  <span class="trace-icon" style="color: ${is_success ? '#4caf50' : is_failed ? '#f44336' : '#2196f3'};">
                                    ${is_in_progress
                                      ? html`<div
                                          class="timeline-spinner"
                                        ></div>`
                                      : nothing}
                                    ${is_retrying
                                      ? html`<div
                                          class="timeline-spinner"
                                          style="border-style: dotted;"
                                        ></div>`
                                      : nothing}
                                    ${is_success
                                      ? html`
                                          <svg
                                            width="12"
                                            height="12"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            stroke-width="3"
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                          >
                                            <polyline
                                              points="20 6 9 17 4 12"
                                            ></polyline>
                                          </svg>
                                        `
                                      : nothing}
                                    ${is_failed
                                      ? html`
                                          <svg
                                            width="12"
                                            height="12"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            stroke-width="3"
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                          >
                                            <line
                                              x1="18"
                                              y1="6"
                                              x2="6"
                                              y2="18"
                                            ></line>
                                            <line
                                              x1="6"
                                              y1="6"
                                              x2="18"
                                              y2="18"
                                            ></line>
                                          </svg>
                                        `
                                      : nothing}
                                  </span>
                                  <span class="trace-time" style="color: #858585;"
                                    >${formattedTime}</span
                                  >
                                  <span class="trace-msg">${step.message}</span>
                                  <span class="trace-elapsed" style="margin-left: auto; color: #858585;">
                                    ${is_in_progress || is_retrying
                                      ? 'active'
                                      : elapsed}
                                  </span>
                                </div>
                              `;
                            })
                          : html`<div
                              style="color: var(--sl-color-neutral-500); font-style: italic;"
                            >
                              No logs available for this suggestion.
                            </div>`
                      }
                    </div>
                  </div>
              </details>

              ${
                this.showBypassUI
                  ? html`
                      <div class="bypass-container" style="margin-bottom: 1.5rem;">
                        <sl-textarea
                          name="bypass_justification"
                          data-testid="bypass-justification-textarea"
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
                  : nothing
              }

              <div slot="footer">
                <div class="dialog-footer-container" style="display: flex; flex-direction: column; gap: 0.5rem; width: 100%;">
                  ${
                    this.errorMessage
                      ? html`<div class="error-message" style="color: var(--sl-color-danger-600); font-weight: bold; font-size: 0.9rem;">
                          ${this.errorMessage}
                        </div>`
                      : nothing
                  }
                  <div class="dialog-footer" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    ${this.isLocked
                      ? html`
                          ${this.suggestion?.status === 'disputed'
                            ? html`
                                <div class="conflict-banner" style="margin: 0; background: var(--sl-color-danger-50); color: var(--sl-color-danger-800); border: 1px solid var(--sl-color-danger-200); font-weight: bold; padding: 0.5rem 1rem; border-radius: 4px; display: flex; align-items: center; gap: 0.5rem;">
                                  ⚠️ DISPUTED: Curation locked to owner's original version.
                                </div>
                                <sl-button
                                  variant="warning"
                                  href="https://b.corp.google.com/issues/new?component=1456399"
                                  target="_blank"
                                  style="margin-left: auto; margin-right: 0.5rem;"
                                >
                                  Resolve Dispute ↗
                                </sl-button>
                              `
                            : html`
                                <div class="conflict-banner" style="margin: 0; background: var(--sl-color-neutral-100); color: var(--sl-color-neutral-700); border: 1px solid var(--sl-color-neutral-300); padding: 0.5rem 1rem; border-radius: 4px; font-weight: bold;">
                                  Milestone is finalized. Curation is locked.
                                </div>
                              `}
                          <sl-button @click=${this.hide} style="${this.suggestion?.status !== 'disputed' ? 'margin-left: auto;' : ''}">Close</sl-button>
                        `
                      : html`
                          <div class="dialog-footer" style="display: flex; gap: 0.5rem; align-items: center; width: 100%;">
                            ${this.suggestion?.status === 'out_of_date'
                              ? html`
                                  <sl-button
                                    variant="warning"
                                    ?disabled=${this.submitting || this.suggestion.drift_detected === 'major'}
                                    @click=${this.keepCuratedVersion}
                                    style="margin-right: auto;"
                                  >
                                    Keep Curated Version
                                  </sl-button>
                                `
                              : nothing}
                            
                            <div class="dialog-footer-actions" style="margin-left: ${this.suggestion?.status === 'out_of_date' ? '0' : 'auto'}; display: flex; gap: 0.5rem; align-items: center;">
                              ${
                                this.suggestion?.status !== 'skipped'
                                  ? html`
                                      <sl-button
                                        variant="danger"
                                        outline
                                        ?loading=${this.submitting}
                                        ?disabled=${this.submitting ||
                                        this.showBypassUI}
                                        @click=${this.discardSuggestion}
                                      >
                                        Discard Suggestion
                                      </sl-button>
                                    `
                                  : nothing
                              }
                              
                              <sl-button
                                ?disabled=${this.submitting}
                                @click=${this.hide}
                              >
                                ${this.suggestion?.status === 'skipped' ? 'Acknowledge Skip' : 'Cancel'}
                              </sl-button>
                              
                              ${
                                this.showBypassUI
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
                                        variant=${this.bypassAction === 'discard'
                                          ? 'danger'
                                          : 'primary'}
                                        ?loading=${this.submitting}
                                        ?disabled=${this.submitting ||
                                        !this.bypassJustification.trim()}
                                        @click=${this.bypassAction === 'discard'
                                          ? this.discardSuggestion
                                          : this.applySuggestion}
                                      >
                                        Confirm
                                        ${this.bypassAction === 'discard'
                                          ? 'Discard'
                                          : 'Apply'}
                                        Bypass
                                      </sl-button>
                                    `
                                  : html`
                                      <sl-button
                                        variant="primary"
                                        ?loading=${this.submitting}
                                        ?disabled=${this.submitting}
                                        @click=${this.applySuggestion}
                                      >
                                        ${this.suggestion?.status === 'skipped'
                                          ? 'Save & Apply Manual'
                                          : 'Save & Apply'}
                                      </sl-button>
                                    `
                              }
                            </div>
                          </div>
                        `}
                  </div>
                </div>
              </div>
            `}
      </sl-dialog>
    `;
  }
}
