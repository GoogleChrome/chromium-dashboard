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
  const statusRef = information.statusRef;
  const reporterRef = information.reporterRef;
  const ownerRef = information.ownerRef;
  // const ccRefs = information.ccRefs;
  const openedTimestamp = information.openedTimestamp;
  function renderTooltipContent() {
    return html`
    <div class="feature-link-tooltip">
    ${openedTimestamp && html`
      <div>
        <strong>Opened:</strong>
        <span>${_formatTimestamp(openedTimestamp)}</span>
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
    </div>
    `;
  }
  return html`
  <div class="feature-link">
    <sl-badge variant="${statusRef.meansOpen ? 'success' : 'danger'}">${statusRef.status}</sl-badge>
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;">
        <div slot="content">${renderTooltipContent()}</div>
        <a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
        ${information.summary}
        </a>
    </sl-tooltip>
  </div>
  `;
}

function _enhanceLink(featureLink, defaultFallback) {
  if (!defaultFallback) {
    throw new Error('defaultFallback html is required');
  }
  if (!featureLink) {
    return defaultFallback();
  }
  switch (featureLink.type) {
    case LINK_TYPE_CHROMIUM_BUG:
      return enhanceChromeStatusLink(featureLink);
    default:
      return defaultFallback();
  }
}

export function enhanceUrl(url, featureLinks = [], defaultFallback) {
  const featureLink = featureLinks.find(fe => fe.url === url);
  if (!defaultFallback) {
    defaultFallback = () => html`<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  }

  if (!featureLink) {
    return fallback();
  }

  return _enhanceLink(featureLink, defaultFallback);
}

export function enhanceAutolink(part, featureLink) {
  return _enhanceLink(featureLink, () => {
    return html`<a href="${part.href}" target="_blank" rel="noopener noreferrer">${part.content}</a>`;
  });
}
