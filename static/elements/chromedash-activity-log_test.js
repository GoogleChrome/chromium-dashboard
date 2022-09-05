import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashActivity, ChromedashActivityLog} from './chromedash-activity-log';
import '../js-src/cs-client';
import sinon from 'sinon';

const nonAdminUser = {
  can_approve: false,
  can_create_feature: true,
  can_edit_all: true,
  is_admin: false,
  email: 'non-admin@google.com',
};

const featureOne = {
  id: 123456,
};

const actOne = {
  comment_id: 1,
  author: 'non-admin@google.com',
  created: '2022-08-30 12:34:45.567',
  content: 'hey, nice feature',
};

const actTwo = {
  comment_id: 2,
  author: 'troll@example.com',
  created: '2022-08-30 12:34:45.567',
  content: 'mean stuff',
};


describe('chromedash-activity', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-activity></chromedash-activity>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivity);
    assert.notExists(component.shadowRoot.querySelector('sl-relative-time'));
    assert.notExists(component.shadowRoot.querySelector('sl-menu'));
  });

  it('renders an activity when signed out', async () => {
    const anonUser = null;
    const component = await fixture(
      html`<chromedash-activity
              .user=${anonUser}
              .feature=${featureOne}
              .activity=${actOne}>
             </chromedash-activity>`);
    const commentDiv = component.shadowRoot.querySelector('.comment');
    assert.include(commentDiv.innerHTML, actOne.author);
    assert.include(commentDiv.innerHTML, '2022-08-30 12:34:45');
    assert.include(commentDiv.innerHTML, 'hey, nice feature');
    // TODO: Fails on firefox.  See issue #2186.
    // assert.exists(component.shadowRoot.querySelector('sl-relative-time'));
    assert.notExists(component.shadowRoot.querySelector('.edit-menu'));
    assert.notExists(component.shadowRoot.querySelector('sl-menu'));
  });

  it('renders an activity when signed in', async () => {
    const component = await fixture(
      html`<chromedash-activity
              .user=${nonAdminUser}
              .feature=${featureOne}
              .activity=${actOne}>
             </chromedash-activity>`);
    const commentDiv = component.shadowRoot.querySelector('.comment');
    assert.include(commentDiv.innerHTML, 'hey, nice feature');
    assert.exists(component.shadowRoot.querySelector('#comment-menu'));
  });

  // Note: It does not hide or prefix a deleted comment for users who don't
  // have permission to view that comment because that is done by the API.

  it('prefixes a undeleteable activity', async () => {
    const deletedComment = {
      comment_id: 3,
      author: 'non-admin@google.com',
      created: '2022-08-30 12:34:45.567',
      content: 'better left unsaid',
      deleted_by: 'non-admin@google.com',
    };
    const component = await fixture(
      html`<chromedash-activity
              .user=${nonAdminUser}
              .feature=${featureOne}
              .activity=${deletedComment}>
             </chromedash-activity>`);
    const commentDiv = component.shadowRoot.querySelector('.comment');
    assert.include(commentDiv.innerHTML, '[Deleted]');
    assert.include(commentDiv.innerHTML, 'better left unsaid');
    assert.exists(component.shadowRoot.querySelector('#comment-menu'));
    assert.exists(component.shadowRoot.querySelector('sl-menu'));
  });

  it('can delete an activity', async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'deleteComment');
    window.csClient.deleteComment.returns(Promise.resolve({message: 'Done'}));

    const doomedComment = {
      comment_id: 4,
      author: 'non-admin@google.com',
      created: '2022-08-30 12:34:45.567',
      content: 'something off the cuff',
    };
    const component = await fixture(
      html`<chromedash-activity
              .user=${nonAdminUser}
              .feature=${featureOne}
              .activity=${doomedComment}>
             </chromedash-activity>`);
    const before = component.shadowRoot.querySelector('.comment');
    assert.notInclude(before.innerHTML, '[Deleted]');
    assert.include(before.innerHTML, 'something off the cuff');

    await component.handleDeleteToggle(false);
    assert.equal(doomedComment.deleted_by, nonAdminUser.email);
    const after = component.shadowRoot.querySelector('.comment');
    assert.include(after.innerHTML, '[Deleted]');
    assert.include(after.innerHTML, 'something off the cuff');
  });

  it('can undelete an activity', async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'undeleteComment');
    window.csClient.undeleteComment.returns(Promise.resolve({message: 'Done'}));

    const blessedComment = {
      comment_id: 4,
      author: 'non-admin@google.com',
      created: '2022-08-30 12:34:45.567',
      content: 'lucky guess',
      deleted_by: 'non-admin@google.com',
    };
    const component = await fixture(
      html`<chromedash-activity
              .user=${nonAdminUser}
              .feature=${featureOne}
              .activity=${blessedComment}>
             </chromedash-activity>`);
    const before = component.shadowRoot.querySelector('.comment');
    assert.include(before.innerHTML, '[Deleted]');
    assert.include(before.innerHTML, 'lucky guess');

    await component.handleDeleteToggle(true);
    assert.equal(blessedComment.deleted_by, null);
    const after = component.shadowRoot.querySelector('.comment');
    assert.notInclude(after.innerHTML, '[Deleted]');
    assert.include(after.innerHTML, 'lucky guess');
  });

  it('formats comment date relative to the current date', async () => {
    window.csClient = new ChromeStatusClient('fake_token', 1);
    sinon.stub(window.csClient, 'undeleteComment');

    const component = await fixture(
      html`<chromedash-activity-log
              .user=${nonAdminUser}
              .feature=${featureOne}
              .comments=${[commentOne]}>
             </chromedash-activity-log>`);

    const relativeDate = component.shadowRoot.querySelector('sl-relative-time');
    assert.exists(relativeDate);
    const dateStr = relativeDate.getAttribute('date');
    assert.equal(dateStr, '2022-08-30T12:34:45.567Z');
    const dateObj = new Date(dateStr);
    assert.isFalse(isNaN(dateObj));
  });
});


describe('chromedash-activity-log', () => {
  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-activity-log></chromedash-activity-log>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivityLog);
    assert.notExists(component.shadowRoot.querySelector('chromedash-activity'));
  });

  it('renders with some data', async () => {
    const component = await fixture(
      html`<chromedash-activity-log
            .user=${nonAdminUser}
            .feature=${featureOne}
            .comments=${[actOne, actTwo]}>
            </chromedash-activity-log>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivityLog);
    assert.lengthOf(
      component.shadowRoot.querySelectorAll('chromedash-activity'),
      2);
  });
});
