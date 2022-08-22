// This file contains helper functions for our elements.

import {html} from 'lit';
import {unsafeHTML} from 'lit/directives/unsafe-html.js';

let toastEl;

/* eslint-disable max-len */
// When crbug links don't specify a project, the default project is Chromium.
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
const IMPLIED_EMAIL_RE = /\b[a-z]((-|\.)?[a-z0-9])+@[a-z]((-|\.)?[a-z0-9])+\.(com|net|org|edu|dev)\b/gi;
const SHORT_LINK_RE = /(^|[^-\/._])\b(https?:\/\/|ftp:\/\/|mailto:)?(go|g|shortn|who|teams)\/([^\s<]+)/gi;
const NUMERIC_SHORT_LINK_RE = /(^|[^-\/._])\b(https?:\/\/|ftp:\/\/)?(b|t|o|omg|cl|cr|fxr|fxrev|fxb|tqr)\/([0-9]+)/gi;
const IMPLIED_LINK_RE = /(^|[^-\/._])\b[a-z]((-|\.)?[a-z0-9])+\.(com|net|org|edu|dev)\b(\/[^\s<]*)?/gi;
const IS_LINK_RE = /()\b(https?:\/\/|ftp:\/\/|mailto:)([^\s<]+)/gi;
const GIT_HASH_RE = /\b(r(evision\s+#?)?)?([a-f0-9]{40})\b/gi;
const SVN_REF_RE = /\b(r(evision\s+#?)?)([0-9]{4,7})\b/gi;
// The revNum is in the same position for the above two Regexes. The
// extraction function uses this similar format to allow switching out
// Regexes easily, so be careful about changing GIT_HASH_RE and SVN_HASH_RE.
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
/* eslint-enable max-len */

const Components = new Map();
Components.set(
  '00-commentbug',
  {
    extractRefs: null,
    refRegs: [PROJECT_COMMENT_BUG_RE],
    replacer: ReplaceCommentBugRef,
  },
);
Components.set(
  '01-tracker-crbug',
  {
    extractRefs: ExtractCrbugProjectAndIssueIds,
    refRegs: [CRBUG_LINK_RE],
    replacer: ReplaceCrbugIssueRef,
  },
);
Components.set(
  '02-full-urls',
  {
    extractRefs: (match) => {
      return [match[0]];
    },
    refRegs: [IS_LINK_RE],
    replacer: ReplaceLinkRef,
  },
);
Components.set(
  '03-user-emails',
  {
    extractRefs: (match) => {
      return [match[0]];
    },
    refRegs: [IMPLIED_EMAIL_RE],
    replacer: ReplaceUserRef,
  },
);
Components.set(
  '04-tracker-regular',
  {
    extractRefs: ExtractTrackerProjectAndIssueIds,
    refRegs: [ISSUE_TRACKER_RE],
    replacer: ReplaceTrackerIssueRef,
  },
);
Components.set(
  '05-linkify-shorthand',
  {
    extractRefs: (match) => {
      return [match[0]];
    },
    refRegs: [
      SHORT_LINK_RE,
      NUMERIC_SHORT_LINK_RE,
      IMPLIED_LINK_RE,
    ],
    replacer: ReplaceLinkRef,
  },
);
Components.set(
  '06-versioncontrol',
  {
    extractRefs: (match) => {
      return [match[0]];
    },
    refRegs: [GIT_HASH_RE, SVN_REF_RE],
    replacer: ReplaceRevisionRef,
  },
);
// Extract referenced artifacts info functions.
function ExtractCrbugProjectAndIssueIds(match) {
  // When crbug links don't specify a project, the default project is Chromium.
  const projectName = match[CRBUG_LINK_RE_PROJECT_GROUP] ||
    CRBUG_DEFAULT_PROJECT;
  const localId = match[CRBUG_LINK_RE_ID_GROUP];
  return [{projectName: projectName, localId: localId}];
}
function ExtractTrackerProjectAndIssueIds(match, currentProjectName) {
  const issueRefRE = PROJECT_LOCALID_RE;
  let refMatch;
  const refs = [];
  while ((refMatch = issueRefRE.exec(match[0])) !== null) {
    if (refMatch[PROJECT_LOCALID_RE_PROJECT_GROUP]) {
      currentProjectName = refMatch[PROJECT_LOCALID_RE_PROJECT_GROUP];
    }
    refs.push({
      projectName: currentProjectName,
      localId: refMatch[PROJECT_LOCALID_RE_ID_GROUP],
    });
  }
  return refs;
}
// Replace plain text references with links functions.
function replaceIssueRef(stringMatch, projectName, localId, components,
  commentId) {
  return createIssueRefRun(projectName, localId, stringMatch, commentId);
}
function ReplaceCrbugIssueRef(match, components) {
  components = components || {};
  // When crbug links don't specify a project, the default project is Chromium.
  const projectName =
    match[CRBUG_LINK_RE_PROJECT_GROUP] || CRBUG_DEFAULT_PROJECT;
  const localId = match[CRBUG_LINK_RE_ID_GROUP];
  let commentId = '';
  if (match[CRBUG_LINK_RE_COMMENT_GROUP] !== undefined) {
    commentId = match[CRBUG_LINK_RE_COMMENT_GROUP];
  }
  return [replaceIssueRef(match[0], projectName, localId, components,
    commentId)];
}
function ReplaceTrackerIssueRef(match, components, currentProjectName=CRBUG_DEFAULT_PROJECT) {
  components = components || {};
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
      refMatch[PROJECT_LOCALID_RE_ID_GROUP], components, commentId));
    pos = refMatch.index + refMatch[0].length;
  }
  if (match[0].slice(pos) !== '') {
    textRuns.push({content: match[0].slice(pos)});
  }
  return textRuns;
}
function ReplaceUserRef(match, components) {
  components = components || {};
  const textRun = {content: match[0], tag: 'a'};
  if (components.users && components.users.length) {
    const existingUser = components.users.find((user) => {
      return user.displayName.toLowerCase() === match[0].toLowerCase();
    });
    if (existingUser) {
      textRun.href = `/u/${match[0]}`;
      return [textRun];
    }
  }
  textRun.href = `mailto:${match[0]}`;
  return [textRun];
}
function ReplaceCommentBugRef(match) {
  let textRun;
  const issueNum = match[7];
  const commentNum = match[18];
  if (issueNum && commentNum) {
    const href = `${CRBUG_URL}/p/${CRBUG_DEFAULT_PROJECT}/issues/detail?id=${issueNum}#c${commentNum}`;
    textRun = {content: match[0], tag: 'a', href};
  } else if (commentNum) {
    const href = `${CRBUG_URL}/p/${CRBUG_DEFAULT_PROJECT}/issues/detail#c${commentNum}`;
    textRun = {content: match[0], tag: 'a', href};
  } else {
    textRun = {content: match[0]};
  }
  return [textRun];
}
function ReplaceLinkRef(match) {
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
function ReplaceRevisionRef(match) {
  // TODO(danielrsmith): update to link to git hashes.
  return [{content: match[0]}];
}
// Create custom textrun functions.
function createIssueRefRun(projectName, localId, content, commentId) {
  return {
    tag: 'a',
    content: content,
    href: `${CRBUG_URL}/p/${projectName}/issues/detail?id=${localId}${commentId}`,
  };
}
function markupAutolinks(plainString) {
  plainString = plainString || '';
  const chunks = [plainString.trim()];
  const textRuns = [];
  chunks.filter(Boolean).forEach((chunk) => {
    textRuns.push(
      ...autolinkChunk(chunk));
  });
  const result = textRuns.map(part => {
    if (part.tag === 'a') {
      return `<a href="${part.href}" target="_blank" rel="noopener noreferrer">${part.content}</a>`;
    }
    return part.content;
  }).join('');
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

/* Convert user-entered text into safe HTML with clickable links
 * where appropriate.  Returns a lit-html TemplateResult.
 */
// TODO(jrobbins): autolink monorail-style issue references, go-links, etc.
export function autolink(s) {
  const markup = markupAutolinks(s);
  return html`${unsafeHTML(markup)}`;
}

export function showToastMessage(msg) {
  if (!toastEl) toastEl = document.querySelector('chromedash-toast');
  toastEl.showMessage(msg);
}

/**
 * Returns the rendered elements of the named slot of component.
 * @param {Element} component
 * @param {string} slotName
 * @return {Element}
 */
export function slotAssignedElements(component, slotName) {
  const slotSelector = slotName ? `slot[name=${slotName}]` : 'slot';
  return component.shadowRoot.querySelector(slotSelector).assignedElements({flatten: true});
}
