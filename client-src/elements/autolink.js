// This is an implementation of autolinking pulled from Monorail and repurposed
// for use with text entries in WebStatus. Use this directly via './utils.js'
// See: https://chromium.googlesource.com/infra/infra/+/refs/heads/main/appengine/monorail/static_src/autolink.js

import {html} from 'lit';
import {enhanceAutolink} from './feature-link.js';
const CRBUG_DEFAULT_PROJECT = 'chromium';
const CRBUG_URL = 'https://bugs.chromium.org';
const CRBUG_LINK_RE = /(\b(https?:\/\/)?crbug\.com\/)((\b[-a-z0-9]+)(\/))?(\d+)\b(\#c[0-9]+)?/gi;
const CRBUG_LINK_RE_PROJECT_GROUP = 4;
const CRBUG_LINK_RE_ID_GROUP = 6;
const CRBUG_LINK_RE_COMMENT_GROUP = 7;
const ISSUE_TRACKER_RE = /(\b(issues?|bugs?)[ \t]*(:|=|\b)|\bfixed[ \t]*:)([ \t]*((\b[-a-z0-9]+)[:\#])?(\#?)(\d+)\b(,?[ \t]*(and|or)?)?)+/gi;
const PROJECT_LOCALID_RE = /((\b(issue|bug)[ \t]*(:|=)?[ \t]*|\bfixed[ \t]*:[ \t]*)?((\b[-a-z0-9]+)[:\#])?(\#?)(\d+))/gi;
const PROJECT_COMMENT_BUG_RE = /(((\b(issue|bug)[ \t]*(:|=)?[ \t]*)(\#?)(\d+)[ \t*])?((\b((comment)[ \t]*(:|=)?[ \t]*(\#?))|(\B((\#))(c)))(\d+)))/gi;
const PROJECT_LOCALID_RE_PROJECT_GROUP = 6;
const PROJECT_LOCALID_RE_ID_GROUP = 8;
const SHORT_LINK_RE = /(^|[^-\/._])\b(https?:\/\/|ftp:\/\/|mailto:)?(go|g|shortn|who|teams)\/([^\s<]+)/gi;
const NUMERIC_SHORT_LINK_RE = /(^|[^-\/._])\b(https?:\/\/|ftp:\/\/)?(b|t|o|omg|cl|cr|fxr|fxrev|fxb|tqr)\/([0-9]+)/gi;
const IMPLIED_LINK_RE = /(?!@)(^|[^-\/._])\b[a-z]((-|\.)?[a-z0-9])+\.(com|net|org|edu|dev)\b(\/[^\s<]*)?/gi;
const IS_LINK_RE = /()\b(https?:\/\/|ftp:\/\/|mailto:)([^\s<]+)/gi;
const LINK_TRAILING_CHARS = [
  [null, ':'],
  [null, '.'],
  [null, ','],
  [null, '>'],
  ['(', ')'],
  ['[', ']'],
  ['{', '}'],
  ['\'', '\''],
  ['"', '"'],
];
const GOOG_SHORT_LINK_RE = /^(b|t|o|omg|cl|cr|go|g|shortn|who|teams|fxr|fxrev|fxb|tqr)\/.*/gi;

const Components = new Map();
Components.set(
  '00-commentbug',
  {
    refRegs: [PROJECT_COMMENT_BUG_RE],
    replacer: replaceCommentBugRef,
  },
);
Components.set(
  '01-tracker-crbug',
  {
    refRegs: [CRBUG_LINK_RE],
    replacer: replaceCrbugIssueRef,
  },
);
Components.set(
  '02-full-urls',
  {
    refRegs: [IS_LINK_RE],
    replacer: replaceLinkRef,
  },
);
// 03-user-emails unused.
Components.set(
  '04-tracker-regular',
  {
    refRegs: [ISSUE_TRACKER_RE],
    replacer: replaceTrackerIssueRef,
  },
);
Components.set(
  '05-linkify-shorthand',
  {
    refRegs: [
      SHORT_LINK_RE,
      NUMERIC_SHORT_LINK_RE,
      IMPLIED_LINK_RE,
    ],
    replacer: replaceLinkRef,
  },
);
// 06-versioncontrol unused.

// Replace plain text references with links functions.
function replaceIssueRef(stringMatch, projectName, localId, commentId) {
  return createIssueRefRun(projectName, localId, stringMatch, commentId);
}

function replaceCrbugIssueRef(match) {
  // When crbug links don't specify a project, the default project is Chromium.
  const projectName =
    match[CRBUG_LINK_RE_PROJECT_GROUP] || CRBUG_DEFAULT_PROJECT;
  const localId = match[CRBUG_LINK_RE_ID_GROUP];
  let commentId = '';
  if (match[CRBUG_LINK_RE_COMMENT_GROUP] !== undefined) {
    commentId = match[CRBUG_LINK_RE_COMMENT_GROUP];
  }
  return [replaceIssueRef(match[0], projectName, localId,
    commentId)];
}

function replaceTrackerIssueRef(match, currentProjectName=CRBUG_DEFAULT_PROJECT) {
  const issueRefRE = PROJECT_LOCALID_RE;
  const commentId = '';
  const textRuns = [];
  let refMatch;
  let pos = 0;
  while ((refMatch = issueRefRE.exec(match[0])) !== null) {
    if (refMatch.index > pos) {
      // Create textrun for content between previous and current match.
      textRuns.push({content: match[0].slice(pos, refMatch.index)});
    }
    if (refMatch[PROJECT_LOCALID_RE_PROJECT_GROUP]) {
      currentProjectName = refMatch[PROJECT_LOCALID_RE_PROJECT_GROUP];
    }
    textRuns.push(replaceIssueRef(
      refMatch[0], currentProjectName,
      refMatch[PROJECT_LOCALID_RE_ID_GROUP], commentId));
    pos = refMatch.index + refMatch[0].length;
  }
  if (match[0].slice(pos) !== '') {
    textRuns.push({content: match[0].slice(pos)});
  }
  return textRuns;
}

function replaceCommentBugRef(match) {
  let textRun;
  const issueNum = match[7];
  const commentNum = match[18];
  if (issueNum && commentNum) {
    const href = (
      `${CRBUG_URL}/p/${CRBUG_DEFAULT_PROJECT}/issues/detail?id=${issueNum}#c${commentNum}`);
    textRun = {content: match[0], tag: 'a', href};
  } else if (commentNum) {
    const href = `${CRBUG_URL}/p/${CRBUG_DEFAULT_PROJECT}/issues/detail#c${commentNum}`;
    textRun = {content: match[0], tag: 'a', href};
  } else {
    textRun = {content: match[0]};
  }
  return [textRun];
}

function replaceLinkRef(match) {
  const textRuns = [];
  let content = match[0];
  let trailing = '';
  if (match[1]) {
    textRuns.push({content: match[1]});
    content = content.slice(match[1].length);
  }
  LINK_TRAILING_CHARS.forEach(([begin, end]) => {
    if (content.endsWith(end)) {
      if (!begin || !content.slice(0, -end.length).includes(begin)) {
        trailing = end + trailing;
        content = content.slice(0, -end.length);
      }
    }
  });
  let href = content;
  const lowerHref = href.toLowerCase();
  if (!lowerHref.startsWith('http') && !lowerHref.startsWith('ftp') &&
      !lowerHref.startsWith('mailto')) {
    // Prepend google-internal short links with http to
    // prevent HTTPS error interstitial.
    // SHORT_LINK_RE should not be used here as it might be
    // in the middle of another match() process in an outer loop.
    if (GOOG_SHORT_LINK_RE.test(lowerHref)) {
      href = 'http://' + href;
    } else {
      href = 'https://' + href;
    }
    GOOG_SHORT_LINK_RE.lastIndex = 0;
  }
  textRuns.push({content: content, tag: 'a', href: href});
  if (trailing.length) {
    textRuns.push({content: trailing});
  }
  return textRuns;
}

// Create custom textrun functions.
function createIssueRefRun(projectName, localId, content, commentId) {
  return {
    tag: 'a',
    content: content,
    href: `${CRBUG_URL}/p/${projectName}/issues/detail?id=${localId}${commentId}`,
  };
}

export function markupAutolinks(plainString, featureLinks = []) {
  plainString = plainString || '';
  const chunks = [plainString.trim()];
  const textRuns = [];
  chunks.filter(Boolean).forEach((chunk) => {
    textRuns.push(
      ...autolinkChunk(chunk));
  });
  const result = textRuns.map(part => {
    if (part.tag === 'a') {
      const featureLink = featureLinks.find(fe => fe.url === part.href);
      if (featureLink) {
        // if the link is a feature link, enhance it to provide more information
        return enhanceAutolink(part, featureLink);
      }
      return html`<a href="${part.href}" target="_blank" rel="noopener noreferrer">${part.content}</a>`;
    }
    return part.content;
  });
  return result;
}

function autolinkChunk(chunk) {
  let textRuns = [{content: chunk}];
  Components.forEach(({refRegs, replacer}) => {
    refRegs.forEach((re) => {
      textRuns = applyLinks(
        textRuns, replacer, re);
    });
  });
  return textRuns;
}

function applyLinks(
  textRuns, replacer, re) {
  const resultRuns = [];
  textRuns.forEach((textRun) => {
    if (textRun.tag) {
      resultRuns.push(textRun);
    } else {
      const content = textRun.content;
      let pos = 0;
      let match;
      while ((match = re.exec(content)) !== null) {
        if (match.index > pos) {
          // Create textrun for content between previous and current match.
          resultRuns.push({content: content.slice(pos, match.index)});
        }
        resultRuns.push(
          ...replacer(match));
        pos = match.index + match[0].length;
      }
      if (content.slice(pos) !== '') {
        resultRuns.push({content: content.slice(pos)});
      }
    }
  });
  return resultRuns;
}
