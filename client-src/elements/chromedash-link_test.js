import {expect, fixture} from '@open-wc/testing';
import {html} from 'lit';
import './chromedash-link';
import {_dateTimeFormat} from './chromedash-link';

it('shows a plain link for non-cached links', async () => {
  const el = await fixture(html`<chromedash-link
    href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
    .featureLinks=${[]}>Content</chromedash-link>`);
  expect(el).shadowDom.to.equal(
    `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank"><slot>...</slot></a>`,
    {ignoreChildren: ['slot']});
});

it('wraps the text in sl-tag when requested', async () => {
  const el = await fixture(html`<chromedash-link
    alwaysInTag
    href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
    .featureLinks=${[]}>Content</chromedash-link>`);
  expect(el).shadowDom.to.equal(
    `<a href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
        rel="noopener noreferrer"
        target="_blank"><sl-tag><slot>...</slot></sl-tag></a>`,
    {ignoreChildren: ['slot']});
});

describe('Github issue links', () => {
  it('shows tooltip, open state, and title', async () => {
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const featureLinks = [{
      url: 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
      type: 'github_issue',
      information: {
        'url': 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
        'number': 3007,
        'title': 'Issue Title',
        'user_login': 'user',
        'state': 'open',
        'assignee_login': 'assignee',
        'created_at': yesterday.toISOString(),
        'updated_at': yesterday.toISOString(),
        'closed_at': yesterday.toISOString(),
        'labels': [],
      },
    }];
    const el = await fixture(html`<chromedash-link
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${featureLinks}>Content</chromedash-link>`);
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
                <span>chromium-dashboard/issues</span>
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
              open
            </sl-badge>
            #3007 Issue Title
          </sl-tag>
        </sl-tooltip>
      </a>`,
      {
        ignoreAttributes: ['style', 'title'],
      });
  });

  it('shows closed state and title', async () => {
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    const featureLinks = [{
      url: 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
      type: 'github_issue',
      information: {
        'url': 'https://github.com/GoogleChrome/chromium-dashboard/issues/3007',
        'number': 3007,
        'title': 'Issue Title',
        'user_login': 'user',
        'state': 'closed',
        'assignee_login': 'assignee',
        'created_at': yesterday.toISOString(),
        'updated_at': yesterday.toISOString(),
        'closed_at': yesterday.toISOString(),
        'labels': [],
      },
    }];
    const el = await fixture(html`<chromedash-link
      href="https://github.com/GoogleChrome/chromium-dashboard/issues/3007"
      .featureLinks=${featureLinks}>Content</chromedash-link>`);
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
              closed
            </sl-badge>
            #3007 Issue Title
          </sl-tag>
        </sl-tooltip>
      </a>`,
      {
        ignoreChildren: ['div'],
        ignoreAttributes: ['style', 'title'],
      });
  });
});
