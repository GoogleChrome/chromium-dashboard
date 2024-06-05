// @ts-check
import { __extends, __makeTemplateObject, __spreadArray } from "tslib";
import { css, html, LitElement } from 'lit';
import { ifDefined } from 'lit/directives/if-defined.js';
import { SHARED_STYLES } from '../css/shared-css';
import { ExternalReviewer } from './external-reviewers';
// LINK_TYPES should be consistent with the server link_helpers.py
var LINK_TYPE_CHROMIUM_BUG = 'chromium_bug';
var LINK_TYPE_GITHUB_ISSUE = 'github_issue';
var LINK_TYPE_GITHUB_PULL_REQUEST = 'github_pull_request';
var LINK_TYPE_GITHUB_MARKDOWN = 'github_markdown';
var LINK_TYPE_MDN_DOCS = 'mdn_docs';
var LINK_TYPE_GOOGLE_DOCS = 'google_docs';
var LINK_TYPE_MOZILLA_BUG = 'mozilla_bug';
var LINK_TYPE_WEBKIT_BUG = 'webkit_bug';
var LINK_TYPE_SPECS = 'specs';
function _formatLongText(text, maxLength) {
    if (maxLength === void 0) { maxLength = 50; }
    if (text.length > maxLength) {
        return (text.substring(0, 35) +
            '...' +
            text.substring(text.length - 15, text.length));
    }
    return text;
}
export var _dateTimeFormat = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric', // No seconds
});
function enhanceChromeStatusLink(featureLink, text) {
    function _formatTimestamp(timestamp) {
        return _dateTimeFormat.format(new Date(timestamp * 1000));
    }
    var information = featureLink.information;
    var summary = information.summary;
    var statusRef = information.statusRef;
    var reporterRef = information.reporterRef;
    var ownerRef = information.ownerRef;
    // const ccRefs = information.ccRefs;
    var openedTimestamp = information.openedTimestamp;
    var closedTimestamp = information.closedTimestamp;
    if (!text) {
        text = summary;
    }
    function renderTooltipContent() {
        return html(templateObject_6 || (templateObject_6 = __makeTemplateObject(["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n    </div>"], ["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n    </div>"])), summary && html(templateObject_1 || (templateObject_1 = __makeTemplateObject(["\n        <div>\n          <strong>Summary:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Summary:</strong>\n          <span>", "</span>\n        </div>\n      "])), summary), openedTimestamp && html(templateObject_2 || (templateObject_2 = __makeTemplateObject(["\n        <div>\n          <strong>Opened:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Opened:</strong>\n          <span>", "</span>\n        </div>\n      "])), _formatTimestamp(openedTimestamp)), closedTimestamp && html(templateObject_3 || (templateObject_3 = __makeTemplateObject(["\n        <div>\n          <strong>Closed:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Closed:</strong>\n          <span>", "</span>\n        </div>\n      "])), _formatTimestamp(closedTimestamp)), reporterRef && html(templateObject_4 || (templateObject_4 = __makeTemplateObject(["\n        <div>\n          <strong>Reporter:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Reporter:</strong>\n          <span>", "</span>\n        </div>\n      "])), reporterRef.displayName), ownerRef && html(templateObject_5 || (templateObject_5 = __makeTemplateObject(["\n        <div>\n          <strong>Owner:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Owner:</strong>\n          <span>", "</span>\n        </div>\n      "])), ownerRef.displayName));
    }
    return html(templateObject_7 || (templateObject_7 = __makeTemplateObject(["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img\n          src=\"https://bugs.chromium.org/static/images/monorail.ico\"\n          alt=\"icon\"\n          class=\"icon\"\n        />\n        <sl-badge\n          size=\"small\"\n          variant=\"", "\"\n          >", "</sl-badge\n        >\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"], ["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img\n          src=\"https://bugs.chromium.org/static/images/monorail.ico\"\n          alt=\"icon\"\n          class=\"icon\"\n        />\n        <sl-badge\n          size=\"small\"\n          variant=\"", "\"\n          >", "</sl-badge\n        >\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"])), featureLink.url, renderTooltipContent(), statusRef.meansOpen ? 'success' : 'neutral', statusRef.status, _formatLongText(text));
}
function enhanceGithubIssueLink(featureLink, text) {
    var _a;
    function _formatISOTime(dateString) {
        return _dateTimeFormat.format(new Date(dateString));
    }
    var information = featureLink.information;
    var assignee = information.assignee_login;
    var createdAt = new Date(information.created_at);
    var closedAt = information.closed_at;
    var updatedAt = information.updated_at;
    var state = information.state;
    // const stateReason = information.state_reason;
    var title = information.title;
    var owner = information.user_login;
    var number = information.number;
    var repo = information.url.split('/').slice(4, 6).join('/');
    var typePath = featureLink.url.split('/').slice(-2)[0];
    var type = typePath === 'issues'
        ? 'Issue'
        : typePath === 'pull'
            ? 'Pull Request'
            : typePath;
    // If this issue is an external review of the feature, find the summary description.
    var externalReviewer = ExternalReviewer.get(repo);
    var stateDescription = undefined;
    var stateVariant = undefined;
    if (externalReviewer) {
        for (var _i = 0, _b = information.labels; _i < _b.length; _i++) {
            var label = _b[_i];
            var labelInfo = externalReviewer.label(label);
            if (labelInfo) {
                (stateDescription = labelInfo.description, stateVariant = labelInfo.variant);
                break;
            }
        }
    }
    if (stateVariant === undefined) {
        if (state === 'open') {
            var age = Date.now() - createdAt.getTime();
            stateDescription = html(templateObject_8 || (templateObject_8 = __makeTemplateObject(["Opened\n        <sl-relative-time date=", "\n          >on ", "</sl-relative-time\n        >"], ["Opened\n        <sl-relative-time date=", "\n          >on ", "</sl-relative-time\n        >"])), createdAt.toISOString(), _dateTimeFormat.format(createdAt));
            var week = 7 * 24 * 60 * 60 * 1000;
            stateVariant = 'success';
            if (externalReviewer) {
                // If this is an issue asking for external review, having it filed too recently is a warning
                // sign, which we'll indicate using the tag's color.
                if (age < 4 * week) {
                    stateVariant = 'warning';
                }
                else {
                    // Still only neutral if the reviewer hasn't given a position yet.
                    stateVariant = 'neutral';
                }
            }
        }
        else {
            console.assert(state === 'closed');
            stateDescription = 'Closed';
            stateVariant = 'neutral';
        }
    }
    if (!text) {
        text = title;
    }
    function renderTooltipContent() {
        return html(templateObject_17 || (templateObject_17 = __makeTemplateObject(["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n    </div>"], ["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n      ", "\n    </div>"])), title && html(templateObject_9 || (templateObject_9 = __makeTemplateObject(["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "])), title), repo && html(templateObject_10 || (templateObject_10 = __makeTemplateObject(["\n        <div>\n          <strong>Repo:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Repo:</strong>\n          <span>", "</span>\n        </div>\n      "])), repo), type && html(templateObject_11 || (templateObject_11 = __makeTemplateObject(["\n        <div>\n          <strong>Type:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Type:</strong>\n          <span>", "</span>\n        </div>\n      "])), type), createdAt && html(templateObject_12 || (templateObject_12 = __makeTemplateObject(["\n        <div>\n          <strong>Opened:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Opened:</strong>\n          <span>", "</span>\n        </div>\n      "])), _formatISOTime(createdAt)), updatedAt && html(templateObject_13 || (templateObject_13 = __makeTemplateObject(["\n        <div>\n          <strong>Updated:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Updated:</strong>\n          <span>", "</span>\n        </div>\n      "])), _formatISOTime(updatedAt)), closedAt && html(templateObject_14 || (templateObject_14 = __makeTemplateObject(["\n        <div>\n          <strong>Closed:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Closed:</strong>\n          <span>", "</span>\n        </div>\n      "])), _formatISOTime(closedAt)), assignee && html(templateObject_15 || (templateObject_15 = __makeTemplateObject(["\n        <div>\n          <strong>Assignee:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Assignee:</strong>\n          <span>", "</span>\n        </div>\n      "])), assignee), owner && html(templateObject_16 || (templateObject_16 = __makeTemplateObject(["\n        <div>\n          <strong>Owner:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Owner:</strong>\n          <span>", "</span>\n        </div>\n      "])), owner));
    }
    return html(templateObject_18 || (templateObject_18 = __makeTemplateObject(["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img\n          src=", "\n          alt=\"icon\"\n          class=\"icon\"\n        />\n        <sl-badge size=\"small\" variant=", "\n          >", "</sl-badge\n        >\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"], ["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img\n          src=", "\n          alt=\"icon\"\n          class=\"icon\"\n        />\n        <sl-badge size=\"small\" variant=", "\n          >", "</sl-badge\n        >\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"])), featureLink.url, renderTooltipContent(), (_a = externalReviewer === null || externalReviewer === void 0 ? void 0 : externalReviewer.icon) !== null && _a !== void 0 ? _a : 'https://docs.github.com/assets/cb-600/images/site/favicon.png', stateVariant, stateDescription, _formatLongText("#".concat(number, " ") + text));
}
function enhanceGithubMarkdownLink(featureLink, text) {
    var information = featureLink.information;
    var path = information.path;
    var title = information._parsed_title;
    var size = information.size;
    var readableSize = (size / 1024).toFixed(2) + ' KB';
    if (!text) {
        text = title;
    }
    function renderTooltipContent() {
        return html(templateObject_22 || (templateObject_22 = __makeTemplateObject(["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n    </div>"], ["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n    </div>"])), title && html(templateObject_19 || (templateObject_19 = __makeTemplateObject(["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "])), title), path && html(templateObject_20 || (templateObject_20 = __makeTemplateObject(["\n        <div>\n          <strong>File:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>File:</strong>\n          <span>", "</span>\n        </div>\n      "])), path), size && html(templateObject_21 || (templateObject_21 = __makeTemplateObject(["\n        <div>\n          <strong>Size:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Size:</strong>\n          <span>", "</span>\n        </div>\n      "])), readableSize));
    }
    return html(templateObject_23 || (templateObject_23 = __makeTemplateObject(["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img\n          src=\"https://docs.github.com/assets/cb-600/images/site/favicon.png\"\n          alt=\"icon\"\n          class=\"icon\"\n        />\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"], ["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img\n          src=\"https://docs.github.com/assets/cb-600/images/site/favicon.png\"\n          alt=\"icon\"\n          class=\"icon\"\n        />\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"])), featureLink.url, renderTooltipContent(), _formatLongText('Markdown: ' + text));
}
function _enhanceLinkWithTitleAndDescription(featureLink, iconUrl) {
    var information = featureLink.information;
    var title = information.title;
    var description = information.description;
    function renderTooltipContent() {
        return html(templateObject_26 || (templateObject_26 = __makeTemplateObject(["<div class=\"tooltip\">\n      ", "\n      ", "\n    </div>"], ["<div class=\"tooltip\">\n      ", "\n      ", "\n    </div>"])), title && html(templateObject_24 || (templateObject_24 = __makeTemplateObject(["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "])), title), description && html(templateObject_25 || (templateObject_25 = __makeTemplateObject(["\n        <div>\n          <strong>Description:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Description:</strong>\n          <span>", "</span>\n        </div>\n      "])), description));
    }
    return html(templateObject_27 || (templateObject_27 = __makeTemplateObject(["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img src=\"", "\" alt=\"icon\" class=\"icon\" />\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"], ["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img src=\"", "\" alt=\"icon\" class=\"icon\" />\n        ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"])), featureLink.url, renderTooltipContent(), iconUrl, _formatLongText(title));
}
function enhanceSpecsLink(featureLink) {
    var url = featureLink.url;
    var iconUrl = "https://www.google.com/s2/favicons?domain_url=".concat(url);
    var hashtag = url.split('#')[1];
    var information = featureLink.information;
    var title = information.title;
    var description = information.description;
    function renderTooltipContent() {
        return html(templateObject_31 || (templateObject_31 = __makeTemplateObject(["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n    </div>"], ["<div class=\"tooltip\">\n      ", "\n      ", "\n      ", "\n    </div>"])), title && html(templateObject_28 || (templateObject_28 = __makeTemplateObject(["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Title:</strong>\n          <span>", "</span>\n        </div>\n      "])), title), description && html(templateObject_29 || (templateObject_29 = __makeTemplateObject(["\n        <div>\n          <strong>Description:</strong>\n          <span>", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Description:</strong>\n          <span>", "</span>\n        </div>\n      "])), description), hashtag && html(templateObject_30 || (templateObject_30 = __makeTemplateObject(["\n        <div>\n          <strong>Hashtag:</strong>\n          <span>#", "</span>\n        </div>\n      "], ["\n        <div>\n          <strong>Hashtag:</strong>\n          <span>#", "</span>\n        </div>\n      "])), hashtag));
    }
    return html(templateObject_32 || (templateObject_32 = __makeTemplateObject(["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img src=\"", "\" alt=\"icon\" class=\"icon\" />\n        Spec: ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"], ["<a\n    href=\"", "\"\n    target=\"_blank\"\n    rel=\"noopener noreferrer\"\n  >\n    <sl-tooltip style=\"--sl-tooltip-arrow-size: 0;--max-width: 50vw;\">\n      <div slot=\"content\">", "</div>\n      <sl-tag>\n        <img src=\"", "\" alt=\"icon\" class=\"icon\" />\n        Spec: ", "\n      </sl-tag>\n    </sl-tooltip>\n  </a>"])), featureLink.url, renderTooltipContent(), iconUrl, _formatLongText(title));
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
    var url = featureLink.url;
    var type = url.split('/')[3];
    var iconUrl = 'https://ssl.gstatic.com/docs/documents/images/kix-favicon7.ico';
    if (type === 'spreadsheets') {
        iconUrl = 'https://ssl.gstatic.com/docs/spreadsheets/favicon3.ico';
    }
    else if (type === 'presentation') {
        iconUrl = 'https://ssl.gstatic.com/docs/presentations/images/favicon5.ico';
    }
    else if (type === 'forms') {
        iconUrl = 'https://ssl.gstatic.com/docs/spreadsheets/forms/favicon_qp2.png';
    }
    return _enhanceLinkWithTitleAndDescription(featureLink, iconUrl);
}
var ChromedashLink = /** @class */ (function (_super) {
    __extends(ChromedashLink, _super);
    function ChromedashLink() {
        var _this = _super.call(this) || this;
        /** @type {string | undefined} */
        _this.href = undefined;
        /** @type {boolean} */
        _this.showContentAsLabel = false;
        /** @type {string} */
        _this.class = '';
        /** @type {import("../js-src/cs-client").FeatureLink[]} */
        _this.featureLinks = [];
        /** @type {import ("../js-src/cs-client").FeatureLink | undefined} */
        _this._featureLink = undefined;
        /** @type {number[]} */
        _this.ignoreHttpErrorCodes = [];
        /** @type {boolean} */
        _this.alwaysInTag = false;
        return _this;
    }
    Object.defineProperty(ChromedashLink, "properties", {
        get: function () {
            return {
                href: { type: String },
                /** Says to show this element's content as <slot/>: [feature link] even if a feature link is
                 * available. If this is false, the content is only shown when no feature link is available.
                 */
                showContentAsLabel: { type: Boolean },
                class: { type: String },
                featureLinks: { type: Array },
                _featureLink: { state: true },
                ignoreHttpErrorCodes: { type: Array },
                /** Normally, if there's a feature link, this element displays as a <sl-tag>, and if there
                 * isn't, it displays as a normal <a> link. If [alwaysInTag] is set, it always uses the
                 * <sl-tag>.
                 */
                alwaysInTag: { type: Boolean },
            };
        },
        enumerable: false,
        configurable: true
    });
    ChromedashLink.prototype.willUpdate = function (changedProperties) {
        var _this = this;
        if (changedProperties.has('href') ||
            changedProperties.has('featureLinks')) {
            this._featureLink = this.featureLinks.find(function (fe) { return fe.url === _this.href; });
        }
    };
    ChromedashLink.prototype.fallback = function () {
        var slot = html(templateObject_33 || (templateObject_33 = __makeTemplateObject(["<slot>", "</slot>"], ["<slot>", "</slot>"])), this.href);
        return html(templateObject_35 || (templateObject_35 = __makeTemplateObject(["<a\n      href=", "\n      target=\"_blank\"\n      rel=\"noopener noreferrer\"\n      class=", "\n      >", "</a\n    >"], ["<a\n      href=", "\n      target=\"_blank\"\n      rel=\"noopener noreferrer\"\n      class=", "\n      >", "</a\n    >"])), ifDefined(this.href), this.class, this.alwaysInTag ? html(templateObject_34 || (templateObject_34 = __makeTemplateObject(["<sl-tag>", "</sl-tag>"], ["<sl-tag>", "</sl-tag>"])), slot) : slot);
    };
    ChromedashLink.prototype.withLabel = function (link) {
        if (this.showContentAsLabel) {
            return html(templateObject_36 || (templateObject_36 = __makeTemplateObject(["<slot></slot>: ", ""], ["<slot></slot>: ", ""])), link);
        }
        else {
            return link;
        }
    };
    ChromedashLink.prototype.render = function () {
        if (!this.href) {
            console.error('Missing [href] attribute in', this);
            return html(templateObject_37 || (templateObject_37 = __makeTemplateObject(["<slot></slot>"], ["<slot></slot>"])));
        }
        var featureLink = this._featureLink;
        if (!featureLink) {
            return this.fallback();
        }
        if (!featureLink.information) {
            if (featureLink.http_error_code &&
                !this.ignoreHttpErrorCodes.includes(featureLink.http_error_code)) {
                return html(templateObject_38 || (templateObject_38 = __makeTemplateObject(["<sl-tag>\n          <sl-icon library=\"material\" name=\"link\"></sl-icon>\n          <sl-badge\n            size=\"small\"\n            variant=\"", "\"\n          >\n            ", "\n          </sl-badge>\n          ", "\n        </sl-tag>"], ["<sl-tag>\n          <sl-icon library=\"material\" name=\"link\"></sl-icon>\n          <sl-badge\n            size=\"small\"\n            variant=\"", "\"\n          >\n            ", "\n          </sl-badge>\n          ", "\n        </sl-tag>"])), featureLink.http_error_code >= 500
                    ? 'danger'
                    : 'warning', featureLink.http_error_code, this.fallback());
            }
            return this.fallback();
        }
        try {
            switch (featureLink.type) {
                case LINK_TYPE_CHROMIUM_BUG:
                    return this.withLabel(enhanceChromeStatusLink(featureLink));
                case LINK_TYPE_GITHUB_ISSUE:
                    return this.withLabel(enhanceGithubIssueLink(featureLink));
                case LINK_TYPE_GITHUB_PULL_REQUEST:
                    // we use github issue api to get pull request information,
                    // the result will be the similar to github issue
                    return this.withLabel(enhanceGithubIssueLink(featureLink));
                case LINK_TYPE_GITHUB_MARKDOWN:
                    return this.withLabel(enhanceGithubMarkdownLink(featureLink));
                case LINK_TYPE_MDN_DOCS:
                    return this.withLabel(enhanceMDNDocsLink(featureLink));
                case LINK_TYPE_GOOGLE_DOCS:
                    return this.withLabel(enhanceGoogleDocsLink(featureLink));
                case LINK_TYPE_MOZILLA_BUG:
                    return this.withLabel(enhanceMozillaBugLink(featureLink));
                case LINK_TYPE_WEBKIT_BUG:
                    return this.withLabel(enhanceWebKitBugLink(featureLink));
                case LINK_TYPE_SPECS:
                    return this.withLabel(enhanceSpecsLink(featureLink));
                default:
                    return this.fallback();
            }
        }
        catch (e) {
            console.log('feature link render error:', this, e);
            return this.fallback();
        }
    };
    ChromedashLink.styles = __spreadArray(__spreadArray([], SHARED_STYLES, true), [
        css(templateObject_39 || (templateObject_39 = __makeTemplateObject(["\n      :host {\n        display: inline;\n        white-space: normal;\n        line-break: anywhere;\n        color: var(--default-font-color);\n      }\n\n      a:hover {\n        text-decoration: none;\n      }\n\n      sl-badge::part(base) {\n        display: inline;\n        padding: 0 4px;\n        border-width: 0;\n        text-transform: capitalize;\n        font-weight: 400;\n      }\n\n      sl-tag::part(base) {\n        vertical-align: middle;\n        height: 18px;\n        background-color: rgb(232, 234, 237);\n        color: var(--default-font-color);\n        border: none;\n        border-radius: 500px;\n        display: inline-flex;\n        align-items: center;\n        column-gap: 0.3em;\n        padding: 1px 5px;\n        margin: 1px 0;\n      }\n\n      sl-tag::part(base):hover {\n        background-color: rgb(209, 211, 213);\n      }\n\n      sl-relative-time {\n        margin: 0;\n      }\n\n      .icon {\n        display: block;\n        width: 12px;\n        height: 12px;\n      }\n\n      .tooltip {\n        display: flex;\n        flex-direction: column;\n        row-gap: 0.5em;\n      }\n    "], ["\n      :host {\n        display: inline;\n        white-space: normal;\n        line-break: anywhere;\n        color: var(--default-font-color);\n      }\n\n      a:hover {\n        text-decoration: none;\n      }\n\n      sl-badge::part(base) {\n        display: inline;\n        padding: 0 4px;\n        border-width: 0;\n        text-transform: capitalize;\n        font-weight: 400;\n      }\n\n      sl-tag::part(base) {\n        vertical-align: middle;\n        height: 18px;\n        background-color: rgb(232, 234, 237);\n        color: var(--default-font-color);\n        border: none;\n        border-radius: 500px;\n        display: inline-flex;\n        align-items: center;\n        column-gap: 0.3em;\n        padding: 1px 5px;\n        margin: 1px 0;\n      }\n\n      sl-tag::part(base):hover {\n        background-color: rgb(209, 211, 213);\n      }\n\n      sl-relative-time {\n        margin: 0;\n      }\n\n      .icon {\n        display: block;\n        width: 12px;\n        height: 12px;\n      }\n\n      .tooltip {\n        display: flex;\n        flex-direction: column;\n        row-gap: 0.5em;\n      }\n    "]))),
    ], false);
    return ChromedashLink;
}(LitElement));
export { ChromedashLink };
export function enhanceUrl(url, featureLinks, fallback, text) {
    if (featureLinks === void 0) { featureLinks = []; }
    return html(templateObject_40 || (templateObject_40 = __makeTemplateObject(["<chromedash-link href=", " .featureLinks=", "\n    >", "</chromedash-link\n  >"], ["<chromedash-link href=", " .featureLinks=", "\n    >", "</chromedash-link\n  >"])), url, featureLinks, text !== null && text !== void 0 ? text : url);
}
// prettier-ignore
export function enhanceAutolink(part, featureLinks) {
    return html(templateObject_41 || (templateObject_41 = __makeTemplateObject(["<chromedash-link href=", " .featureLinks=", " .ignoreHttpErrorCodes=", ">", "</chromedash-link>"], ["<chromedash-link href=", " .featureLinks=", " .ignoreHttpErrorCodes=", ">", "</chromedash-link>"])), part.href, featureLinks, [404], part.content);
}
customElements.define('chromedash-link', ChromedashLink);
var templateObject_1, templateObject_2, templateObject_3, templateObject_4, templateObject_5, templateObject_6, templateObject_7, templateObject_8, templateObject_9, templateObject_10, templateObject_11, templateObject_12, templateObject_13, templateObject_14, templateObject_15, templateObject_16, templateObject_17, templateObject_18, templateObject_19, templateObject_20, templateObject_21, templateObject_22, templateObject_23, templateObject_24, templateObject_25, templateObject_26, templateObject_27, templateObject_28, templateObject_29, templateObject_30, templateObject_31, templateObject_32, templateObject_33, templateObject_34, templateObject_35, templateObject_36, templateObject_37, templateObject_38, templateObject_39, templateObject_40, templateObject_41;
//# sourceMappingURL=chromedash-link.js.map