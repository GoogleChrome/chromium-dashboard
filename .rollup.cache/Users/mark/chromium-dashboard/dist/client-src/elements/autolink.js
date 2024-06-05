// This is an implementation of autolinking pulled from Monorail and repurposed
// for use with text entries in WebStatus. Use this directly via './utils.js'
// See: https://chromium.googlesource.com/infra/infra/+/refs/heads/main/appengine/monorail/static_src/autolink.js
import { enhanceAutolink } from './chromedash-link.js';
var CRBUG_DEFAULT_PROJECT = 'chromium';
var CRBUG_URL = 'https://bugs.chromium.org';
var ISSUE_TRACKER_RE = /(\b(issues?|bugs?)[ \t]*(:|=|\b)|\bfixed[ \t]*:)([ \t]*((\b[-a-z0-9]+)[:\#])?(\#?)(\d+)\b(,?[ \t]*(and|or)?)?)+/gi;
var PROJECT_LOCALID_RE = /((\b(issue|bug)[ \t]*(:|=)?[ \t]*|\bfixed[ \t]*:[ \t]*)?((\b[-a-z0-9]+)[:\#])?(\#?)(\d+))/gi;
var PROJECT_COMMENT_BUG_RE = /(((\b(issue|bug)[ \t]*(:|=)?[ \t]*)(\#?)(\d+)[ \t*])?((\b((comment)[ \t]*(:|=)?[ \t]*(\#?))|(\B((\#))(c)))(\d+)))/gi;
var PROJECT_LOCALID_RE_PROJECT_GROUP = 6;
var PROJECT_LOCALID_RE_ID_GROUP = 8;
var SHORT_LINK_RE = /(^|[^-\/._])\b(https?:\/\/|ftp:\/\/|mailto:)?(go|g|shortn|who|teams)\/([^\s<]+)/gi;
var NUMERIC_SHORT_LINK_RE = /(^|[^-\/._])\b(https?:\/\/|ftp:\/\/)?(b|t|o|omg|cl|cr|fxr|fxrev|fxb|tqr)\/([0-9]+)/gi;
var IMPLIED_LINK_RE = /(?!@)(^|[^-\/._])\b[a-z]((-|\.)?[a-z0-9])+\.(com|net|org|edu|dev)\b(\/[^\s<]*)?/gi;
var IS_LINK_RE = /()\b(https?:\/\/|ftp:\/\/|mailto:)([^\s<]+)/gi;
var LINK_TRAILING_CHARS = [
    [null, ':'],
    [null, '.'],
    [null, ','],
    [null, '>'],
    ['(', ')'],
    ['[', ']'],
    ['{', '}'],
    ["'", "'"],
    ['"', '"'],
];
var GOOG_SHORT_LINK_RE = /^(b|t|o|omg|cl|cr|go|g|shortn|who|teams|fxr|fxrev|fxb|tqr)\/.*/gi;
var Components = new Map();
Components.set('00-commentbug', {
    refRegs: [PROJECT_COMMENT_BUG_RE],
    replacer: replaceCommentBugRef,
});
Components.set('02-full-urls', {
    refRegs: [IS_LINK_RE],
    replacer: replaceLinkRef,
});
// 03-user-emails unused.
Components.set('04-tracker-regular', {
    refRegs: [ISSUE_TRACKER_RE],
    replacer: replaceTrackerIssueRef,
});
Components.set('05-linkify-shorthand', {
    refRegs: [SHORT_LINK_RE, NUMERIC_SHORT_LINK_RE, IMPLIED_LINK_RE],
    replacer: replaceLinkRef,
});
// 06-versioncontrol unused.
// Replace plain text references with links functions.
function replaceIssueRef(stringMatch, projectName, localId, commentId) {
    return createIssueRefRun(projectName, localId, stringMatch, commentId);
}
function replaceTrackerIssueRef(match, currentProjectName) {
    if (currentProjectName === void 0) { currentProjectName = CRBUG_DEFAULT_PROJECT; }
    var issueRefRE = PROJECT_LOCALID_RE;
    var commentId = '';
    var textRuns = [];
    var refMatch;
    var pos = 0;
    while ((refMatch = issueRefRE.exec(match[0])) !== null) {
        if (refMatch.index > pos) {
            // Create textrun for content between previous and current match.
            textRuns.push({ content: match[0].slice(pos, refMatch.index) });
        }
        if (refMatch[PROJECT_LOCALID_RE_PROJECT_GROUP]) {
            currentProjectName = refMatch[PROJECT_LOCALID_RE_PROJECT_GROUP];
        }
        textRuns.push(replaceIssueRef(refMatch[0], currentProjectName, refMatch[PROJECT_LOCALID_RE_ID_GROUP], commentId));
        pos = refMatch.index + refMatch[0].length;
    }
    if (match[0].slice(pos) !== '') {
        textRuns.push({ content: match[0].slice(pos) });
    }
    return textRuns;
}
function replaceCommentBugRef(match) {
    var textRun;
    var issueNum = match[7];
    var commentNum = match[18];
    if (issueNum && commentNum) {
        var href = "".concat(CRBUG_URL, "/p/").concat(CRBUG_DEFAULT_PROJECT, "/issues/detail?id=").concat(issueNum, "#c").concat(commentNum);
        textRun = { content: match[0], tag: 'a', href: href };
    }
    else if (commentNum) {
        var href = "".concat(CRBUG_URL, "/p/").concat(CRBUG_DEFAULT_PROJECT, "/issues/detail#c").concat(commentNum);
        textRun = { content: match[0], tag: 'a', href: href };
    }
    else {
        textRun = { content: match[0] };
    }
    return [textRun];
}
function replaceLinkRef(match) {
    var textRuns = [];
    var content = match[0];
    var trailing = '';
    if (match[1]) {
        textRuns.push({ content: match[1] });
        content = content.slice(match[1].length);
    }
    LINK_TRAILING_CHARS.forEach(function (_a) {
        var begin = _a[0], end = _a[1];
        if (content.endsWith(end)) {
            if (!begin || !content.slice(0, -end.length).includes(begin)) {
                trailing = end + trailing;
                content = content.slice(0, -end.length);
            }
        }
    });
    var href = content;
    var lowerHref = href.toLowerCase();
    if (!lowerHref.startsWith('http') &&
        !lowerHref.startsWith('ftp') &&
        !lowerHref.startsWith('mailto')) {
        // Prepend google-internal short links with http to
        // prevent HTTPS error interstitial.
        // SHORT_LINK_RE should not be used here as it might be
        // in the middle of another match() process in an outer loop.
        if (GOOG_SHORT_LINK_RE.test(lowerHref)) {
            href = 'http://' + href;
        }
        else {
            href = 'https://' + href;
        }
        GOOG_SHORT_LINK_RE.lastIndex = 0;
    }
    textRuns.push({ content: content, tag: 'a', href: href });
    if (trailing.length) {
        textRuns.push({ content: trailing });
    }
    return textRuns;
}
// Create custom textrun functions.
function createIssueRefRun(projectName, localId, content, commentId) {
    return {
        tag: 'a',
        content: content,
        href: "".concat(CRBUG_URL, "/p/").concat(projectName, "/issues/detail?id=").concat(localId).concat(commentId),
    };
}
export function markupAutolinks(plainString, featureLinks) {
    if (featureLinks === void 0) { featureLinks = []; }
    plainString = plainString || '';
    var chunks = [plainString.trim()];
    var textRuns = [];
    chunks.filter(Boolean).forEach(function (chunk) {
        textRuns.push.apply(textRuns, autolinkChunk(chunk));
    });
    var result = textRuns.map(function (part) {
        if (part.tag === 'a') {
            // if the link is a feature link, enhance it to provide more information
            return enhanceAutolink(part, featureLinks);
        }
        return part.content;
    });
    return result;
}
function autolinkChunk(chunk) {
    var textRuns = [{ content: chunk }];
    Components.forEach(function (_a) {
        var refRegs = _a.refRegs, replacer = _a.replacer;
        refRegs.forEach(function (re) {
            textRuns = applyLinks(textRuns, replacer, re);
        });
    });
    return textRuns;
}
function applyLinks(textRuns, replacer, re) {
    var resultRuns = [];
    textRuns.forEach(function (textRun) {
        if (textRun.tag) {
            resultRuns.push(textRun);
        }
        else {
            var content = textRun.content;
            var pos = 0;
            var match = void 0;
            while ((match = re.exec(content)) !== null) {
                if (match.index > pos) {
                    // Create textrun for content between previous and current match.
                    resultRuns.push({ content: content.slice(pos, match.index) });
                }
                resultRuns.push.apply(resultRuns, replacer(match));
                pos = match.index + match[0].length;
            }
            if (content.slice(pos) !== '') {
                resultRuns.push({ content: content.slice(pos) });
            }
        }
    });
    return resultRuns;
}
//# sourceMappingURL=autolink.js.map