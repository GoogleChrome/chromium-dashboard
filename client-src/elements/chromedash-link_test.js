import {expect, fixture} from '@open-wc/testing';
import {html} from 'lit';
import './chromedash-link';
import {_dateTimeFormat} from './chromedash-link';

const DAY = 24 * 60 * 60 * 1000;

it('shows a plain link for non-cached links', async () => {
  const el = await fixture(
    html`<chromedash-link
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${[]}
      >Content</chromedash-link
    >`
  );
  expect(el).shadowDom.to.equal(
    `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank"><slot>...</slot></a>`,
    {ignoreChildren: ['slot']}
  );
});

it('wraps the text in sl-tag when requested', async () => {
  const el = await fixture(
    html`<chromedash-link
      alwaysInTag
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${[]}
      >Content</chromedash-link
    >`
  );
  expect(el).shadowDom.to.equal(
    `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank"><sl-tag><slot>...</slot></sl-tag></a>`,
    {ignoreChildren: ['slot']}
  );
});

it('shows content as label when requested', async () => {
  const yesterday = new Date(Date.now() - DAY);
  const featureLinks = [
    {
      url: 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
      type: 'github_issue',
      information: {
        url: 'https://api.github.com/repos/GoogleChrome/chromium-dashboard/issues/3007',
        state: 'open',
        created_at: yesterday.toISOString(),
      },
    },
  ];

  const elWithLabel = await fixture(
    html`<chromedash-link
      showContentAsLabel
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${featureLinks}
      >Content</chromedash-link
    >`
  );
  expect(elWithLabel).shadowDom.to.equal(
    `<slot>...</slot>:
     <a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank">...</a>`,
    {ignoreChildren: ['slot', 'a']}
  );

  const elWithoutLabel = await fixture(
    html`<chromedash-link
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${featureLinks}
      >Content</chromedash-link
    >`
  );
  expect(elWithoutLabel).shadowDom.to.equal(
    `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank">...</a>`,
    {ignoreChildren: ['slot', 'a']}
  );
});

it('shows content as label when requested', async () => {
  const yesterday = new Date(Date.now() - DAY);
  const featureLinks = [
    {
      url: 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
      type: 'github_issue',
      information: {
        url: 'https://api.github.com/repos/GoogleChrome/chromium-dashboard/issues/3007',
        state: 'open',
        created_at: yesterday.toISOString(),
      },
    },
  ];

  const elWithLabel = await fixture(
    html`<chromedash-link
      showContentAsLabel
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${featureLinks}
      >Content</chromedash-link
    >`
  );
  expect(elWithLabel).shadowDom.to.equal(
    `<slot>...</slot>:
     <a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank">...</a>`,
    {ignoreChildren: ['slot', 'a']}
  );

  const elWithoutLabel = await fixture(
    html`<chromedash-link
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${featureLinks}
      >Content</chromedash-link
    >`
  );
  expect(elWithoutLabel).shadowDom.to.equal(
    `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank">...</a>`,
    {ignoreChildren: ['slot', 'a']}
  );
});

describe('Github issue links', () => {
  // Get the 'information' object by running
  // `curl -L https://api.github.com/repos/OWNER/REPO/issues/ISSUE_NUMBER`

  it('shows tooltip, open state, and title', async () => {
    const yesterday = new Date(Date.now() - DAY);
    const featureLinks = [
      {
        url: 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
        type: 'github_issue',
        information: {
          url: 'https://api.github.com/repos/GoogleChrome/chromium-dashboard/issues/3007',
          number: 3007,
          title: 'Issue Title',
          user_login: 'user',
          state: 'open',
          assignee_login: 'assignee',
          created_at: yesterday.toISOString(),
          updated_at: yesterday.toISOString(),
          closed_at: yesterday.toISOString(),
          labels: [],
        },
      },
    ];
    const el = await fixture(
      html`<chromedash-link
        href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        .featureLinks=${featureLinks}
        >Content</chromedash-link
      >`
    );
    expect(el).shadowDom.to.equal(
      `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
          rel="noopener noreferrer" target="_blank">
        <sl-tooltip>
          <div slot="content">
            <div class="tooltip">
              <div>
                <strong>Title:</strong>
                <span>Issue Title</span>
              </div>
              <div>
                <strong>Repo:</strong>
                <span>GoogleChrome/chromium-dashboard</span>
              </div>
              <div>
                <strong>Type:</strong>
                <span>Issue</span>
              </div>
              <div>
                <strong>Opened:</strong>
                <span>${_dateTimeFormat.format(yesterday)}</span>
              </div>
              <div>
                <strong>Updated:</strong>
                <span>${_dateTimeFormat.format(yesterday)}</span>
              </div>
              <div>
                <strong>Closed:</strong>
                <span>${_dateTimeFormat.format(yesterday)}</span>
              </div>
              <div>
                <strong>Assignee:</strong>
                <span>assignee</span>
              </div>
              <div>
                <strong>Owner:</strong>
                <span>user</span>
              </div>
            </div>
          </div>
          <sl-tag>
            <img
              alt="icon"
              class="icon"
              src="https://docs.github.com/assets/cb-600/images/site/favicon.png">
            <sl-badge size="small" variant="success">
              Opened
              <sl-relative-time date="${yesterday.toISOString()}">
                on ${_dateTimeFormat.format(yesterday)}
              </sl-relative-time>
            </sl-badge>
            #3007 Issue Title
          </sl-tag>
        </sl-tooltip>
      </a>`,
      {
        ignoreAttributes: ['style', 'title'],
      }
    );
  });

  it('shows closed state and title', async () => {
    const yesterday = new Date(Date.now() - DAY);
    const featureLinks = [
      {
        url: 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
        type: 'github_issue',
        information: {
          url: 'https://api.github.com/repos/GoogleChrome/chromium-dashboard/issues/3007',
          number: 3007,
          title: 'Issue Title',
          user_login: 'user',
          state: 'closed',
          assignee_login: 'assignee',
          created_at: yesterday.toISOString(),
          updated_at: yesterday.toISOString(),
          closed_at: yesterday.toISOString(),
          labels: [],
        },
      },
    ];
    const el = await fixture(
      html`<chromedash-link
        href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        .featureLinks=${featureLinks}
        >Content</chromedash-link
      >`
    );
    expect(el).shadowDom.to.equal(
      `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
          rel="noopener noreferrer" target="_blank">
        <sl-tooltip>
          <div slot="content">...</div>
          <sl-tag>
            <img
              alt="icon"
              class="icon"
              src="https://docs.github.com/assets/cb-600/images/site/favicon.png">
            <sl-badge size="small" variant="neutral">
              Closed
            </sl-badge>
            #3007 Issue Title
          </sl-tag>
        </sl-tooltip>
      </a>`,
      {
        ignoreChildren: ['div'],
        ignoreAttributes: ['style', 'title'],
      }
    );
  });

  describe('external reviewers', () => {
    it('shows TAG position', async () => {
      const featureLinks = [
        {
          url: 'https://github.com/w3ctag/design-reviews/issues/400',
          type: 'github_issue',
          information: {
            url: 'https://api.github.com/repos/w3ctag/design-reviews/issues/400',
            number: 400,
            title: 'Font Table Access API',
            user_login: 'user',
            state: 'closed',
            assignee_login: 'assignee',
            created_at: '2019-08-07T00:53:51Z',
            updated_at: '2022-08-15T16:40:59Z',
            closed_at: '2022-08-15T16:40:29Z',
            labels: [
              'Needs a venue',
              'Provenance: Fugu',
              'Resolution: unsatisfied',
              'Review type: CG early review',
              'Topic: fonts',
            ],
          },
        },
      ];
      const el = await fixture(
        html`<chromedash-link
          href="https://github.com/w3ctag/design-reviews/issues/400"
          .featureLinks=${featureLinks}
          >Content</chromedash-link
        >`
      );
      expect(el).shadowDom.to.equal(
        `<a href="https://github.com/w3ctag/design-reviews/issues/400"
            rel="noopener noreferrer" target="_blank">
          <sl-tooltip>
            <div slot="content">...</div>
            <sl-tag>
              <img
                alt="icon"
                class="icon"
                src="https://avatars.githubusercontent.com/u/3874462?s=48&amp;v=4">
              <sl-badge size="small" variant="danger">
                Unsatisfied
              </sl-badge>
              #400 Font Table Access API
            </sl-tag>
          </sl-tooltip>
        </a>`,
        {
          ignoreChildren: ['div'],
          ignoreAttributes: ['style', 'title'],
        }
      );
    });

    it('shows WebKit position', async () => {
      const featureLinks = [
        {
          url: 'https://github.com/WebKit/standards-positions/issues/268',
          type: 'github_issue',
          information: {
            url: 'https://api.github.com/repos/WebKit/standards-positions/issues/268',
            number: 268,
            title: 'Cross-Origin Embedder Policies - "credentialless"',
            user_login: 'user',
            state: 'closed',
            assignee_login: 'assignee',
            created_at: '2019-08-07T00:53:51Z',
            updated_at: '2022-08-15T16:40:59Z',
            closed_at: '2022-08-15T16:40:29Z',
            labels: [
              'from: Google',
              'position: support',
              'venue: WHATWG HTML Workstream',
            ],
          },
        },
      ];
      const el = await fixture(
        html`<chromedash-link
          href="https://github.com/WebKit/standards-positions/issues/268"
          .featureLinks=${featureLinks}
          >Content</chromedash-link
        >`
      );
      expect(el).shadowDom.to.equal(
        `<a href="https://github.com/WebKit/standards-positions/issues/268"
            rel="noopener noreferrer" target="_blank">
          <sl-tooltip>
            <div slot="content">...</div>
            <sl-tag>
              <img
                alt="icon"
                class="icon"
                src="https://avatars.githubusercontent.com/u/6458?s=48&amp;v=4">
              <sl-badge size="small" variant="success">
                Support
              </sl-badge>
              #268 Cross-Origin Embedder Policies...credentialless"
            </sl-tag>
          </sl-tooltip>
        </a>`,
        {
          ignoreChildren: ['div'],
          ignoreAttributes: ['style', 'title'],
        }
      );
    });

    function firefoxIssue() {
      return {
        url: 'https://github.com/mozilla/standards-positions/issues/975',
        type: 'github_issue',
        information: {
          url: 'https://api.github.com/repos/mozilla/standards-positions/issues/975',
          number: 975,
          title: 'The textInput event',
          user_login: 'user',
          state: 'closed',
          assignee_login: 'assignee',
          created_at: '2019-08-07T00:53:51Z',
          updated_at: '2022-08-15T16:40:59Z',
          closed_at: '2022-08-15T16:40:29Z',
          labels: ['position: neutral'],
        },
      };
    }

    it('shows Firefox position', async () => {
      const featureLinks = [firefoxIssue()];
      const el = await fixture(
        html`<chromedash-link
          href="https://github.com/mozilla/standards-positions/issues/975"
          .featureLinks=${featureLinks}
          >Content</chromedash-link
        >`
      );
      expect(el).shadowDom.to.equal(
        `<a href="https://github.com/mozilla/standards-positions/issues/975"
            rel="noopener noreferrer" target="_blank">
          <sl-tooltip>
            <div slot="content">...</div>
            <sl-tag>
              <img
                alt="icon"
                class="icon"
                src="https://avatars.githubusercontent.com/u/131524?s=48&amp;v=4">
              <sl-badge size="small" variant="neutral">
                Neutral
              </sl-badge>
              #975 The textInput event
            </sl-tag>
          </sl-tooltip>
        </a>`,
        {
          ignoreChildren: ['div'],
          ignoreAttributes: ['style', 'title'],
        }
      );
    });

    it('shows closed if no position', async () => {
      const issue = firefoxIssue();
      issue.information.labels = [];
      const featureLinks = [issue];
      const el = await fixture(
        html`<chromedash-link
          href="https://github.com/mozilla/standards-positions/issues/975"
          .featureLinks=${featureLinks}
          >Content</chromedash-link
        >`
      );
      expect(el).shadowDom.to.equal(
        `<a href="https://github.com/mozilla/standards-positions/issues/975"
            rel="noopener noreferrer" target="_blank">
          <sl-tooltip>
            <div slot="content">...</div>
            <sl-tag>
              <img
                alt="icon"
                class="icon"
                src="https://avatars.githubusercontent.com/u/131524?s=48&amp;v=4">
              <sl-badge size="small" variant="neutral">
                Closed
              </sl-badge>
              #975 The textInput event
            </sl-tag>
          </sl-tooltip>
        </a>`,
        {
          ignoreChildren: ['div'],
          ignoreAttributes: ['style', 'title'],
        }
      );
    });

    it('shows warning if open too short', async () => {
      const issue = firefoxIssue();
      issue.information.labels = [];
      const lastWeek = new Date(Date.now() - 3 * 7 * DAY);
      issue.information.state = 'open';
      issue.information.created_at = lastWeek.toISOString();
      const featureLinks = [issue];
      const el = await fixture(
        html`<chromedash-link
          href="https://github.com/mozilla/standards-positions/issues/975"
          .featureLinks=${featureLinks}
          >Content</chromedash-link
        >`
      );
      expect(el).shadowDom.to.equal(
        `<a href="https://github.com/mozilla/standards-positions/issues/975"
            rel="noopener noreferrer" target="_blank">
          <sl-tooltip>
            <div slot="content">...</div>
            <sl-tag>
              <img
                alt="icon"
                class="icon"
                src="https://avatars.githubusercontent.com/u/131524?s=48&amp;v=4">
              <sl-badge size="small" variant="warning">
                Opened
                <sl-relative-time date="${lastWeek.toISOString()}">
                  on ${_dateTimeFormat.format(lastWeek)}
                </sl-relative-time>
              </sl-badge>
              #975 The textInput event
            </sl-tag>
          </sl-tooltip>
        </a>`,
        {
          ignoreChildren: ['div'],
          ignoreAttributes: ['style', 'title'],
        }
      );
    });

    it('shows neutral if open a long time', async () => {
      const issue = firefoxIssue();
      issue.information.labels = [];
      const twoMonths = new Date(Date.now() - 8 * 7 * DAY);
      issue.information.state = 'open';
      issue.information.created_at = twoMonths.toISOString();
      const featureLinks = [issue];
      const el = await fixture(
        html`<chromedash-link
          href="https://github.com/mozilla/standards-positions/issues/975"
          .featureLinks=${featureLinks}
          >Content</chromedash-link
        >`
      );
      expect(el).shadowDom.to.equal(
        `<a href="https://github.com/mozilla/standards-positions/issues/975"
            rel="noopener noreferrer" target="_blank">
          <sl-tooltip>
            <div slot="content">...</div>
            <sl-tag>
              <img
                alt="icon"
                class="icon"
                src="https://avatars.githubusercontent.com/u/131524?s=48&amp;v=4">
              <sl-badge size="small" variant="neutral">
                Opened
                <sl-relative-time date="${twoMonths.toISOString()}">
                  on ${_dateTimeFormat.format(twoMonths)}
                </sl-relative-time>
              </sl-badge>
              #975 The textInput event
            </sl-tag>
          </sl-tooltip>
        </a>`,
        {
          ignoreChildren: ['div'],
          ignoreAttributes: ['style', 'title'],
        }
      );
    });
  });
});
