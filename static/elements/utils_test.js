import {html} from 'lit';
import {autolink} from './utils';
import {assert} from '@open-wc/testing';

const compareAutolinkResult = (result, expected) => {
  assert.equal(result.length, expected.length);
  for (let i = 0; i < result.length; i++) {
    assert.equal(result[i], expected[i]);
  }
};

describe('utils', () => {
  describe('autolink', () => {
    it('creates anchor tags for links', () => {
      const before = `This is a test of the autolinking.
go/this-is-a-test.
A bug cr/1234 exists and also cl/1234. Info at issue 1234 comment 3.
AKA issue 1234 #c3. https://example.com/ --- testing. bug 1234 also.`;
      const expected = [
        'This is a test of the autolinking.',
        '\n',
        html`<a href="${'http://go/this-is-a-test'}" target="_blank" rel="noopener noreferrer">${'go/this-is-a-test'}</a>`,
        '.',
        '\nA bug',
        ' ',
        html`<a href="${'http://cr/1234'}" target="_blank" rel="noopener noreferrer">${'cr/1234'}</a>`,
        ' exists and also',
        ' ',
        html`<a href="${'http://cl/1234'}" target="_blank" rel="noopener noreferrer">${'cl/1234'}</a>`,
        '. Info at ',
        html`<a href="${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3'}" target="_blank" rel="noopener noreferrer">${'issue 1234 comment 3'}</a>`,
        '.\nAKA ',
        html`<a href="${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3'}" target="_blank" rel="noopener noreferrer">${'issue 1234 #c3'}</a>`,
        '. ',
        html`<a href="${'https://example.com/'}" target="_blank" rel="noopener noreferrer">${'https://example.com/'}</a>`,
        ' --- testing. ',
        html`<a href="${'https://bugs.chromium.org/p/chromium/issues/detail?id=1234'}" target="_blank" rel="noopener noreferrer">${'bug 1234'}</a>`,
        ' ',
        'also.',
      ];

      const result = autolink(before);
      compareAutolinkResult(result, expected);
    });

    it('does not change text with no links', () => {
      const before = `This is a test of the autolinking.
go this-is-a-test.
A bug cr /1234 exists and also /1234. This is an example sentence.
AKA issue here 1234. example com --- testing.`;
      const expected = [
        'This is a test of the autolinking.\n' +
          'go this-is-a-test.\n' +
          'A bug cr /1234 exists and also /1234. This is an example sentence.\n' +
          'AKA issue here 1234. example com --- testing.',
      ];

      const result = autolink(before);
      compareAutolinkResult(result, expected);
    });

    it('does not convert any other tags to html', () => {
      const before = `<b>Test</b>
go/this-is-a-test
<p>Do not convert this</p>
<script>Dangerous stuff</script>`;
      const expected = [
        '<b>Test</b>',
        '\n',
        html`<a href="${'http://go/this-is-a-test'}" target="_blank" rel="noopener noreferrer">${'go/this-is-a-test'}</a>`,
        '\n<p>Do not convert this</p>\n<script>Dangerous stuff</script>',
      ];

      const result = autolink(before);
      compareAutolinkResult(result, expected);
    });
  });
});
