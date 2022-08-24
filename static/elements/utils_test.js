import {html} from 'lit';
import {autolink} from './utils';
import {assert} from '@open-wc/testing';

describe('utils', () => {
  describe('autolink', () => {
    it('creates a tags for links', () => {
      const before = `
This is a test of the autolinking. go/this-is-a-test.
A bug cr/1234 exists and also cl/1234. Info at issue 1234 comment 3.
AKA issue 1234 #c3. https://example.com/ --- testing. bug 1234 also.`;
      const expected = html`
This is a test of the autolinking. <a href="http://go/this-is-a-test" target="_blank" rel="noopener noreferrer">go/this-is-a-test</a>.
A bug <a href="http://cr/1234" target="_blank" rel="noopener noreferrer">cr/1234</a> exists and also <a href="http://cl/1234" target="_blank" rel="noopener noreferrer">cl/1234</a>. Info at <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3" target="_blank" rel="noopener noreferrer">issue 1234 comment 3</a>.
AKA <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1234#c3" target="_blank" rel="noopener noreferrer">issue 1234 #c3</a>. <a href="https://example.com/" target="_blank" rel="noopener noreferrer">https://example.com/</a> --- testing. <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1234" target="_blank" rel="noopener noreferrer">bug 1234</a> also.`;
      const result = autolink(before);
      assert.equal(result, expected);
    });

    it('does not change text with no links', () => {
      const before = `
This is a test of the autolinking. go this-is-a-test.
A bug cr /1234 exists and also /1234. This is an example sentence.
AKA issue here 1234. example com --- testing.`;
      const expected = html`
This is a test of the autolinking. go this-is-a-test.
A bug cr /1234 exists and also /1234. This is an example sentence.
AKA issue here 1234. example com --- testing.`;
      const result = autolink(before);
      assert.equal(result, expected);
    });
  });
});
