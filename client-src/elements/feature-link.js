import {html} from 'lit';
// LINK_TYPES should be consistent with the server link_helpers.py
const LINK_TYPE_CHROMIUM_BUG = 'chromium_bug';
const LINK_TYPE_GITHUB_ISSUE = 'github_issue';

function enhanceChromeStatusLink(featureLink, text) {
  function _formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const formatOptions = {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      hour: 'numeric', minute: 'numeric'}; // No seconds
    return date.toLocaleString('en-US', formatOptions);
  }

  const information = featureLink.information;
  const summary = information.summary;
  const statusRef = information.statusRef;
  const reporterRef = information.reporterRef;
  const ownerRef = information.ownerRef;
  // const ccRefs = information.ccRefs;
  const openedTimestamp = information.openedTimestamp;
  const closedTimestamp = information.closedTimestamp;

  if (!text) {
    text = summary;
  }

  function renderTooltipContent() {
    return html`<div class="feature-link-tooltip">
    ${summary && html`
    <div>
      <strong>Summary:</strong>
      <span>${summary}</span>
    </div>
  `}
    ${openedTimestamp && html`
      <div>
        <strong>Opened:</strong>
        <span>${_formatTimestamp(openedTimestamp)}</span>
      </div>
    `}
    ${closedTimestamp && html`
      <div>
        <strong>Closed:</strong>
        <span>${_formatTimestamp(closedTimestamp)}</span>
      </div>
    `}
    ${reporterRef && html`
      <div>
        <strong>Reporter:</strong>
        <span>${reporterRef.displayName}</span>
      </div>
    `}
    ${ownerRef && html`
        <div>
          <strong>Owner:</strong>
          <span>${ownerRef.displayName}</span>
        </div>
    `}
    </div>`;
  }
  return html`<a class="feature-link" href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;--max-width: 50vw;">
        <div slot="content">${renderTooltipContent()}</div>
        <sl-badge class="tag">
          <sl-tag size="small" class="badge" variant="${statusRef.meansOpen ? 'success' : 'neutral'}">${statusRef.status}</sl-tag>
          <img src="https://bugs.chromium.org/static/images/monorail.ico" alt="icon" class="icon" />
          ${text}
        </sl-badge>
    </sl-tooltip>
  </a>`;
}
function enhanceGithubIssueLink(featureLink, text) {
  function _formatISOTime(dateString) {
    const date = new Date(dateString);
    const formatOptions = {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      hour: 'numeric', minute: 'numeric'}; // No seconds
    return date.toLocaleString('en-US', formatOptions);
  }
  const information = featureLink.information;
  const assignee = information.assignee_login;
  const createdAt = information.created_at;
  const closedAt = information.closed_at;
  const updatedAt = information.updated_at;
  const state = information.state;
  // const stateReason = information.state_reason;
  const title = information.title;
  const owner = information.user_login;
  const number = information.number;
  if (!text) {
    text = title;
  }

  function renderTooltipContent() {
    return html`<div class="feature-link-tooltip">
    ${title && html`
    <div>
      <strong>Title:</strong>
      <span>${title}</span>
    </div>
  `}
    ${createdAt && html`
      <div>
        <strong>Opened:</strong>
        <span>${_formatISOTime(createdAt)}</span>
      </div>
    `}
    ${updatedAt && html`
    <div>
      <strong>Updated:</strong>
      <span>${_formatISOTime(updatedAt)}</span>
    </div>
    `}
    ${closedAt && html`
      <div>
        <strong>Closed:</strong>
        <span>${_formatISOTime(closedAt)}</span>
      </div>
    `}
    ${assignee && html`
      <div>
        <strong>Assignee:</strong>
        <span>${assignee}</span>
      </div>
    `}
    ${owner && html`
        <div>
          <strong>Owner:</strong>
          <span>${owner}</span>
        </div>
    `}
    </div>`;
  }
  return html`<a class="feature-link" href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;--max-width: 50vw;">
        <div slot="content">${renderTooltipContent()}</div>
        <sl-badge class="tag">
          <sl-tag size="small" class="badge" variant="${state === 'open' ? 'success' : 'neutral'}">${state}</sl-tag>
          <img src="https://docs.github.com/assets/cb-600/images/site/favicon.png" alt="icon" class="icon" />
          ${`#${number} ` + text}
        </sl-badge>
    </sl-tooltip>
  </a>`;
}
function _enhanceLink(featureLink, fallback, text) {
  if (!fallback) {
    throw new Error('fallback html is required');
  }
  if (!featureLink) {
    return fallback;
  }
  if (!featureLink.information) {
    // TODO: render 403/404 link empty information
    return fallback;
  }
  if (!text) {
    text = featureLink.url;
  }
  try {
    switch (featureLink.type) {
      case LINK_TYPE_CHROMIUM_BUG:
        return enhanceChromeStatusLink(featureLink);
      case LINK_TYPE_GITHUB_ISSUE:
        return enhanceGithubIssueLink(featureLink);
      default:
        return fallback;
    }
  } catch (e) {
    console.log('feature link render error:', e);
    return fallback;
  }
}

export function enhanceUrl(url, featureLinks = [], fallback, text) {
  const featureLink = featureLinks.find(fe => fe.url === url);
  if (!fallback) {
    fallback = html`<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  }

  return _enhanceLink(featureLink, fallback, text);
}

export function enhanceAutolink(part, featureLink) {
  const fallback = html`<a href="${part.href}" target="_blank" rel="noopener noreferrer">${part.content}</a>`;
  return _enhanceLink(featureLink, fallback);
}
