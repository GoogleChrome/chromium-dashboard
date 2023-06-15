import {html} from 'lit';
// LINK_TYPES should be consistent with the server link_helpers.py
const LINK_TYPE_CHROMIUM_BUG = 'chromium_bug';


function enhanceChromeStatusLink(featureLink) {
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
  return html`<div class="feature-link">
    <sl-badge class="badge" pill variant="${statusRef.meansOpen ? 'success' : 'neutral'}">${statusRef.status}</sl-badge>
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;--max-width: 50vw;">
        <div slot="content">${renderTooltipContent()}</div>
        <a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
        ${featureLink.url}
        </a>
    </sl-tooltip>
  </div>`;
}

function _enhanceLink(featureLink, fallback) {
  if (!fallback) {
    throw new Error('fallback html is required');
  }
  if (!featureLink) {
    return fallback;
  }
  switch (featureLink.type) {
    case LINK_TYPE_CHROMIUM_BUG:
      return enhanceChromeStatusLink(featureLink);
    default:
      return fallback;
  }
}

export function enhanceUrl(url, featureLinks = [], fallback) {
  const featureLink = featureLinks.find(fe => fe.url === url);
  if (!fallback) {
    fallback = html`<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  }

  return _enhanceLink(featureLink, fallback);
}

export function enhanceAutolink(part, featureLink) {
  const fallback = html`<a href="${part.href}" target="_blank" rel="noopener noreferrer">${part.content}</a>`;
  return _enhanceLink(featureLink, fallback);
}
