import {html} from 'lit';
import {assert, fixture} from '@open-wc/testing';
import {ChromedashActivityLog} from './chromedash-activity-log';
import '../js-src/cs-client';
import sinon from 'sinon';

describe('chromedash-activity-log', () => {
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
  const commentOne = {
    comment_id: 1,
    author: 'non-admin@google.com',
    created: '2022-08-30 12:34:45.567',
    content: 'hey, nice feature',
  };
  const commentTwo = {
    comment_id: 2,
    author: 'troll@example.com',
    created: '2022-08-30 12:34:45.567',
    content: 'mean stuff',
  };

  it('renders with no data', async () => {
    const component = await fixture(
      html`<chromedash-activity-log></chromedash-activity-log>`);
    assert.exists(component);
    assert.instanceOf(component, ChromedashActivityLog);
    assert.notExists(component.shadowRoot.querySelector('sl-relative-time'));
    assert.notExists(component.shadowRoot.querySelector('sl-menu'));
  });

  it('renders a list of comments when signed out', async () => {
    const anonUser = null;
    const component = await fixture(
      html`<chromedash-activity-log
              .user=${anonUser}
              .feature=${featureOne}
              .comments=${[commentOne, commentTwo]}>
             </chromedash-activity-log>`);
    const commentSection = component.shadowRoot.querySelector('.comment_section');
    assert.include(commentSection.innerHTML, commentOne.author);
    assert.include(commentSection.innerHTML, '2022-08-30 12:34:45');
    assert.include(commentSection.innerHTML, 'hey, nice feature');
    assert.include(commentSection.innerHTML, commentTwo.author);
    assert.include(commentSection.innerHTML, '2022-08-30 12:34:45');
    assert.include(commentSection.innerHTML, 'mean stuff');
    // TODO: Fails on firefox.  See issue #2186.
    // assert.exists(component.shadowRoot.querySelector('sl-relative-time'));
    assert.notExists(component.shadowRoot.querySelector('.edit-menu'));
    assert.notExists(component.shadowRoot.querySelector('sl-menu'));
  });

  it('renders a list of comments when signed in', async () => {
    const component = await fixture(
      html`<chromedash-activity-log
              .user=${nonAdminUser}
              .feature=${featureOne}
              .comments=${[commentOne, commentTwo]}>
             </chromedash-activity-log>`);
    const commentSection = component.shadowRoot.querySelector('.comment_section');
    assert.include(commentSection.innerHTML, 'hey, nice feature');
    assert.exists(component.shadowRoot.querySelector('#comment-menu-1'));
    assert.include(commentSection.innerHTML, 'mean stuff');
    assert.notExists(component.shadowRoot.querySelector('#comment-menu-2'));
  });

  // Note: It does not hide or prefix a deleted comment for users who don't
  // have permission to view that comment because that is done by the API.

  it('prefixes a undeleteable comment', async () => {
    const deletedComment = {
      comment_id: 3,
      author: 'non-admin@google.com',
      created: '2022-08-30 12:34:45.567',
      content: 'better left unsaid',
      deleted_by: 'non-admin@google.com',
    };
    const component = await fixture(
      html`<chromedash-activity-log
              .user=${nonAdminUser}
              .feature=${featureOne}
              .comments=${[deletedComment]}>
             </chromedash-activity-log>`);
    const commentSection = component.shadowRoot.querySelector('.comment_section');
    assert.include(commentSection.innerHTML, '[Deleted]');
    assert.include(commentSection.innerHTML, 'better left unsaid');
    assert.exists(component.shadowRoot.querySelector('#comment-menu-3'));
    assert.exists(component.shadowRoot.querySelector('sl-menu'));
  });

  it('can delete a comment', async () => {
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
      html`<chromedash-activity-log
              .user=${nonAdminUser}
              .feature=${featureOne}
              .comments=${[doomedComment]}>
             </chromedash-activity-log>`);
    const before = component.shadowRoot.querySelector('.comment_section');
    assert.notInclude(before.innerHTML, '[Deleted]');
    assert.include(before.innerHTML, 'something off the cuff');

    await component.handleDeleteToggle(doomedComment, false);
    assert.equal(doomedComment.deleted_by, nonAdminUser.email);
    const after = component.shadowRoot.querySelector('.comment_section');
    assert.include(after.innerHTML, '[Deleted]');
    assert.include(after.innerHTML, 'something off the cuff');
  });

  it('can undelete a comment', async () => {
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
      html`<chromedash-activity-log
              .user=${nonAdminUser}
              .feature=${featureOne}
              .comments=${[blessedComment]}>
             </chromedash-activity-log>`);
    const before = component.shadowRoot.querySelector('.comment_section');
    assert.include(before.innerHTML, '[Deleted]');
    assert.include(before.innerHTML, 'lucky guess');

    await component.handleDeleteToggle(blessedComment, true);
    assert.equal(blessedComment.deleted_by, null);
    const after = component.shadowRoot.querySelector('.comment_section');
    assert.notInclude(after.innerHTML, '[Deleted]');
    assert.include(after.innerHTML, 'lucky guess');
  });
});
