import {assert} from '@open-wc/testing';
import {ChromedashApprovalsDialog} from './chromedash-all-features-page';
import './chromedash-toast';
import '../js-src/cs-client';

describe('chromedash-all-features-page', () => {
  describe('formatRelativeDate', () => {
    it('formats comment date relative to now', () => {
      const commentDate = '2020-08-22 23:26:54';
      const now = '2022-08-23 00:00:00 UTC';
      const relative = ChromedashApprovalsDialog.formatRelativeDate(
          commentDate, new Date(now));
      assert.isTrue(relative.includes('days ago'));
    });
    it('handles an invalid date', () => {
      const commentDate = 'This is not a real date.';
      const now = '2022-08-23 00:00:00 UTC';
      const relative = ChromedashApprovalsDialog.formatRelativeDate(
          commentDate, new Date(now));
      assert.equal(relative, '');
    });
    it('formats a very recent date', () => {
      const commentDate = '2022-08-23 00:00:00';
      const now = '2022-08-23 00:00:30 UTC';
      const relative = ChromedashApprovalsDialog.formatRelativeDate(
          commentDate, new Date(now));
      assert.equal(relative, 'moments ago');
    });
  });
});
