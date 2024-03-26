import {html} from 'lit';
// LINK_TYPES should be consistent with the server link_helpers.py
const LINK_TYPE_CHROMIUM_BUG = 'chromium_bug';
const LINK_TYPE_GITHUB_ISSUE = 'github_issue';
const LINK_TYPE_GITHUB_PULL_REQUEST = 'github_pull_request';
const LINK_TYPE_GITHUB_MARKDOWN = 'github_markdown';
const LINK_TYPE_MDN_DOCS = 'mdn_docs';
const LINK_TYPE_GOOGLE_DOCS = 'google_docs';
const LINK_TYPE_MOZILLA_BUG = 'mozilla_bug';
const LINK_TYPE_WEBKIT_BUG = 'webkit_bug';
const LINK_TYPE_SPECS = 'specs';

function _formatLongText(text, maxLength = 50) {
  if (text.length > maxLength) {
    return text.substring(0, 35) + '...' + text.substring(text.length - 15, text.length);
  }
  return text;
}

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
        <sl-tag>
          <img src="https://bugs.chromium.org/static/images/monorail.ico" alt="icon" class="icon" />
          <sl-badge size="small" variant="${statusRef.meansOpen ? 'success' : 'neutral'}">${statusRef.status}</sl-badge>
          ${_formatLongText(text)}
        </sl-tag>
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
  const repo = information.url.split('/').slice(4, 6).join('/');
  const typePath = featureLink.url.split('/').slice(-2)[0];
  const type = typePath === 'issues' ? 'Issue' : typePath === 'pull' ? 'Pull Request' : typePath;

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
    ${repo && html`
      <div>
        <strong>Repo:</strong>
        <span>${repo}</span>
      </div>
    `}
    ${type && html`
    <div>
      <strong>Type:</strong>
      <span>${type}</span>
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
        <sl-tag>
          <img src="https://docs.github.com/assets/cb-600/images/site/favicon.png" alt="icon" class="icon" />
          <sl-badge size="small" variant="${state === 'open' ? 'success' : 'neutral'}">${state}</sl-badge>
          ${_formatLongText(`#${number} ` + text)}
        </sl-tag>
    </sl-tooltip>
  </a>`;
}

function enhanceGithubMarkdownLink(featureLink, text) {
  const information = featureLink.information;
  const path = information.path;
  const title = information._parsed_title;
  const size = information.size;
  const readableSize = (size / 1024).toFixed(2) + ' KB';
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
    ${path && html`
      <div>
        <strong>File:</strong>
        <span>${path}</span>
      </div>
    `}
    ${size && html`
    <div>
      <strong>Size:</strong>
      <span>${readableSize}</span>
    </div>
    `}
    </div>`;
  }
  return html`<a class="feature-link" href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;--max-width: 50vw;">
        <div slot="content">${renderTooltipContent()}</div>
        <sl-tag>
          <img src="https://docs.github.com/assets/cb-600/images/site/favicon.png" alt="icon" class="icon" />
          ${_formatLongText('Markdown: ' + text)}
        </sl-tag>
    </sl-tooltip>
  </a>`;
}

function _enhanceLinkWithTitleAndDescription(featureLink, iconUrl) {
  const information = featureLink.information;
  const title = information.title;
  const description = information.description;

  function renderTooltipContent() {
    return html`<div class="feature-link-tooltip">
    ${title && html`
    <div>
      <strong>Title:</strong>
      <span>${title}</span>
    </div>
  `}
    ${description && html`
      <div>
        <strong>Description:</strong>
        <span>${description}</span>
      </div>
    `}
    </div>`;
  }
  return html`<a class="feature-link" href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;--max-width: 50vw;">
        <div slot="content">${renderTooltipContent()}</div>
        <sl-tag>
          <img src="${iconUrl}" alt="icon" class="icon" />
          ${_formatLongText(title)}
        </sl-tag>
    </sl-tooltip>
  </a>`;
}

function enhanceSpecsLink(featureLink) {
  const url = featureLink.url;
  const iconUrl = `https://www.google.com/s2/favicons?domain_url=${url}`;
  const hashtag = url.split('#')[1];
  const information = featureLink.information;
  const title = information.title;
  const description = information.description;

  function renderTooltipContent() {
    return html`<div class="feature-link-tooltip">
    ${title && html`
    <div>
      <strong>Title:</strong>
      <span>${title}</span>
    </div>
  `}
    ${description && html`
      <div>
        <strong>Description:</strong>
        <span>${description}</span>
      </div>
    `}
    </div>
    ${hashtag && html`
      <div>
        <strong>Hashtag:</strong>
        <span>#${hashtag}</span>
      `}
      </div>`;
  }
  return html`<a class="feature-link" href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
    <sl-tooltip style="--sl-tooltip-arrow-size: 0;--max-width: 50vw;">
        <div slot="content">${renderTooltipContent()}</div>
        <sl-tag>
          <img src="${iconUrl}" alt="icon" class="icon" />
          Spec: ${_formatLongText(title)}
        </sl-tag>
    </sl-tooltip>
  </a>`;
}

function enhanceMDNDocsLink(featureLink) {
  return _enhanceLinkWithTitleAndDescription(featureLink, 'https://developer.mozilla.org/favicon-48x48.png');
}

function enhanceMozillaBugLink(featureLink) {
  return _enhanceLinkWithTitleAndDescription(featureLink, 'https://bugzilla.mozilla.org/favicon.ico');
}

function enhanceWebKitBugLink(featureLink) {
  return _enhanceLinkWithTitleAndDescription(featureLink, 'https://bugs.webkit.org/images/favicon.ico');
}

function enhanceGoogleDocsLink(featureLink) {
  const url = featureLink.url;
  const type = url.split('/')[3];
  let iconUrl = 'https://ssl.gstatic.com/docs/documents/images/kix-favicon7.ico';

  if (type === 'spreadsheets') {
    iconUrl = 'https://ssl.gstatic.com/docs/spreadsheets/favicon3.ico';
  } else if (type === 'presentation') {
    iconUrl = 'https://ssl.gstatic.com/docs/presentations/images/favicon5.ico';
  } else if (type === 'forms') {
    iconUrl = 'https://ssl.gstatic.com/docs/spreadsheets/forms/favicon_qp2.png';
  }

  return _enhanceLinkWithTitleAndDescription(featureLink, iconUrl);
}

function _enhanceLink(featureLink, fallback, text, ignoreHttpErrorCodes = []) {
  if (!fallback) {
    throw new Error('fallback html is required');
  }
  if (!featureLink) {
    return fallback;
  }
  if (!featureLink.information) {
    if (featureLink.http_error_code &&
       !ignoreHttpErrorCodes.includes(featureLink.http_error_code)) {
      return html`<div class="feature-link">
        <sl-tag>
          <sl-icon library="material" name="link"></sl-icon>
          <sl-badge size="small" variant="${featureLink.http_error_code >= 500 ? 'danger' : 'warning'}">
            ${featureLink.http_error_code}
          </sl-badge>
          ${fallback}
        </sl-tag>
      </div>`;
    }
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
      case LINK_TYPE_GITHUB_PULL_REQUEST:
        // we use github issue api to get pull request information,
        // the result will be the similar to github issue
        return enhanceGithubIssueLink(featureLink);
      case LINK_TYPE_GITHUB_MARKDOWN:
        return enhanceGithubMarkdownLink(featureLink);
      case LINK_TYPE_MDN_DOCS:
        return enhanceMDNDocsLink(featureLink);
      case LINK_TYPE_GOOGLE_DOCS:
        return enhanceGoogleDocsLink(featureLink);
      case LINK_TYPE_MOZILLA_BUG:
        return enhanceMozillaBugLink(featureLink);
      case LINK_TYPE_WEBKIT_BUG:
        return enhanceWebKitBugLink(featureLink);
      case LINK_TYPE_SPECS:
        return enhanceSpecsLink(featureLink);
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
  return _enhanceLink(featureLink, fallback, part.content, [404]);
}
