import {html} from 'lit';
// LINK_TYPES should be consistent with the server link_helpers.py
const LINK_TYPE_CHROMIUM_BUG = 'chromium_bug';

function enhanceChromeStatusLink(featureLink) {
  const information = featureLink.information;
  return html`<a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">${information.summary}</a>`;
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

export function enhanceUrl(url, featureLinks = []) {
  const featureLink = featureLinks.find(fe => fe.url === url);
  function fallback() {
    const LONG_TEXT = 60;
    return html`
    <a href=${url} target="_blank"
       class="url ${url.length > LONG_TEXT ? 'longurl' : ''}"
       >${url}</a>
    `;
  }

  if (!featureLink) {
    return fallback();
  }

  return _enhanceLink(featureLink, fallback);
}

export function enhanceAutolink(part, featureLink) {
  return _enhanceLink(featureLink, () => {
    return html`<a href="${part.href}" target="_blank" rel="noopener noreferrer">${part.content}</a>`;
  });
}
