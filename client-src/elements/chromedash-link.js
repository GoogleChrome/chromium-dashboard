// @ts-check

import {css, html, LitElement} from 'lit';
import {ifDefined} from 'lit/directives/if-defined.js';
import {SHARED_STYLES} from '../css/shared-css';

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

const dateTimeFormat = new Intl.DateTimeFormat('en-US', {
  weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  hour: 'numeric', minute: 'numeric', // No seconds
});

function enhanceChromeStatusLink(featureLink, text) {
  function _formatTimestamp(timestamp) {
    return dateTimeFormat.format(new Date(timestamp * 1000));
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
    return html`<div class="tooltip">
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
  return html`<a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
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
    return dateTimeFormat.format(new Date(dateString));
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
    return html`<div class="tooltip">
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
  return html`<a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
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
    return html`<div class="tooltip">
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
  return html`<a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
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
    return html`<div class="tooltip">
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
  return html`<a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
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
    return html`<div class="tooltip">
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
    ${hashtag && html`
      <div>
        <strong>Hashtag:</strong>
        <span>#${hashtag}</span>
      </div>
    `}
    </div>`;
  }
  return html`<a href="${featureLink.url}" target="_blank" rel="noopener noreferrer">
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

export class ChromedashLink extends LitElement {
  static styles = [
    ...SHARED_STYLES,
    css`
    :host {
      display: inline;
      white-space: normal;
      line-break: anywhere;
      color: var(--default-font-color);
    }

    a:hover {
      text-decoration: none;
    }

    sl-badge::part(base) {
      height: 14px;
      padding: 4px;
      border-width: 0;
      text-transform: capitalize;
      font-weight: 400;
    }

    sl-tag::part(base) {
      vertical-align: middle;
      height: 18px;
      background-color: rgb(232,234,237);
      color: var(--default-font-color);
      border: none;
      border-radius: 500px;
      display: inline-flex;
      align-items: center;
      column-gap: 0.3em;
      padding: 1px 5px;
      margin: 1px 0;
    }

    sl-tag::part(base):hover {
      background-color: rgb(209,211,213);
    }

    .icon {
      display: block;
      width: 12px;
      height: 12px;
    }

    .tooltip {
      display: flex;
      flex-direction: column;
      row-gap: 0.5em;
    }
    `];

  static get properties() {
    return {
      href: {type: String},
      class: {type: String},
      featureLinks: {type: Array},
      _featureLink: {state: true},
      ignoreHttpErrorCodes: {type: Array},
      /** Normally, if there's a feature link, this element displays as a <sl-tag>, and if there
       * isn't, it displays as a normal <a> link. If [alwaysInTag] is set, it always uses the
       * <sl-tag>.
       */
      alwaysInTag: {type: Boolean},
    };
  }

  constructor() {
    super();
    /** @type {string | undefined} */
    this.href = undefined;
    /** @type {string} */
    this.class = '';
    /** @type {import("../js-src/cs-client").FeatureLink[]} */
    this.featureLinks = [];
    /** @type {import ("../js-src/cs-client").FeatureLink | undefined} */
    this._featureLink = undefined;
    /** @type {number[]} */
    this.ignoreHttpErrorCodes = [];
    /** @type {boolean} */
    this.alwaysInTag = false;
  }

  willUpdate(changedProperties) {
    if (changedProperties.has('href') || changedProperties.has('featureLinks')) {
      this._featureLink = this.featureLinks.find(fe => fe.url === this.href);
    }
  }

  fallback() {
    const slot = html`<slot>${this.href}</slot>`;
    return html`<a
      href=${ifDefined(this.href)}
      target="_blank"
      rel="noopener noreferrer"
      class=${this.class}
    >${this.alwaysInTag ? html`<sl-tag>${slot}</sl-tag>` : slot}</a>`;
  }

  render() {
    if (!this.href) {
      console.error('Missing [href] attribute in', this);
      return html`<slot></slot>`;
    }

    const featureLink = this._featureLink;
    if (!featureLink) {
      return this.fallback();
    }
    if (!featureLink.information) {
      if (featureLink.http_error_code &&
        !this.ignoreHttpErrorCodes.includes(featureLink.http_error_code)) {
        return html`<sl-tag>
            <sl-icon library="material" name="link"></sl-icon>
            <sl-badge size="small" variant="${featureLink.http_error_code >= 500 ? 'danger' : 'warning'}">
              ${featureLink.http_error_code}
            </sl-badge>
            ${this.fallback()}
          </sl-tag>`;
      }
      return this.fallback();
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
          return this.fallback();
      }
    } catch (e) {
      console.log('feature link render error:', e);
      return this.fallback();
    }
  }
}

export function enhanceUrl(url, featureLinks = [], fallback, text) {
  return html`<chromedash-link href=${url} .featureLinks=${featureLinks}
    >${text ?? url}</chromedash-link>`;
}

export function enhanceAutolink(part, featureLinks) {
  return html`<chromedash-link href=${part.href} .featureLinks=${featureLinks} .ignoreHttpErrorCodes=${[404]}>${part.content}</chromedash-link>`;
}

customElements.define('chromedash-link', ChromedashLink);
