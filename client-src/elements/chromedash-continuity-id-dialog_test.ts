import {html} from 'lit';
import {fixture, assert, expect} from '@open-wc/testing';
import sinon from 'sinon';
import './chromedash-continuity-id-dialog.js';
import {
  ChromedashIdVerificationDialog,
  openIdVerificationDialog,
} from './chromedash-continuity-id-dialog.js';

// Mock the showToastMessage function.
const showToastMessage = sinon.spy();

// Mock window.csClient.
const csClient = {
  createSecurityLaunchIssue: sinon.stub(),
};

// Assign the mocks to the window object.
(window as any).csClient = csClient;
(window as any).showToastMessage = showToastMessage;

describe('chromedash-continuity-id-dialog', () => {
  let component: ChromedashIdVerificationDialog;

  beforeEach(async () => {
    component = await fixture<ChromedashIdVerificationDialog>(html`
      <chromedash-continuity-id-dialog></chromedash-continuity-id-dialog>
    `);
  });

  afterEach(() => {
    // Reset the spies and stubs.
    sinon.restore();
  });

  it('is an instance of ChromedashIdVerificationDialog', () => {
    assert.instanceOf(component, ChromedashIdVerificationDialog);
  });

  it('renders the dialog with the correct initial state', async () => {
    // Check that the dialog is rendered.
    const dialog = component.shadowRoot!.querySelector('sl-dialog');
    assert.exists(dialog);

    // Check the initial state of the component.
    assert.equal(component._verificationState, 'idle');
    assert.equal(component._idValue, '');
    assert.equal(
      component._verificationMessage,
      'Please enter a Continuity ID.'
    );
    assert.isFalse(component._canCheck);

    // Check the initial text of the verification button.
    const verifyButton = component.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    );
    assert.exists(verifyButton);
    expect(verifyButton!.textContent).to.contain('Verify and Submit');
  });

  it('updates the _idValue and _canCheck properties on input', async () => {
    const input = component.shadowRoot!.querySelector('sl-input');
    assert.exists(input);

    // Simulate user input.
    input!.value = '12345';
    input!.dispatchEvent(new Event('sl-input'));

    await component.updateComplete;

    // Check that the state has been updated.
    assert.equal(component._idValue, '12345');
    assert.isTrue(component._canCheck);
  });

  it('disables the "Verify and Submit" button when the input is empty', async () => {
    const verifyButton = component.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    );
    assert.exists(verifyButton);
    assert.isTrue(verifyButton!.hasAttribute('disabled'));

    // Enter some text to enable the button.
    const input = component.shadowRoot!.querySelector('sl-input');
    input!.value = '12345';
    input!.dispatchEvent(new Event('sl-input'));
    await component.updateComplete;

    // Check that the button is enabled.
    assert.isFalse(verifyButton!.hasAttribute('disabled'));

    // Clear the input to disable the button again.
    input!.value = '';
    input!.dispatchEvent(new Event('sl-input'));
    await component.updateComplete;

    // Check that the button is disabled again.
    assert.isTrue(verifyButton!.hasAttribute('disabled'));
  });

  it('handles successful verification', async () => {
    csClient.createSecurityLaunchIssue.resolves({});

    const input = component.shadowRoot!.querySelector('sl-input');
    input!.value = '12345';
    input!.dispatchEvent(new Event('sl-input'));
    await component.updateComplete;

    const verifyButton = component.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    ) as HTMLButtonElement;
    verifyButton!.click();

    await component.updateComplete;

    // Check the loading state.
    assert.equal(component._verificationState, 'loading');
    assert.equal(component._verificationMessage, 'Verifying...');

    // Wait for the API call to resolve.
    await component.updateComplete;
    await new Promise(resolve => setTimeout(resolve, 0)); // Wait for the next tick.

    // Check the success state.
    assert.equal(component._verificationState, 'success');
    assert.equal(component._verificationMessage, 'Verification success!');
    assert.isTrue(showToastMessage.calledWith('Success!'));
  });

  it('handles verification failure', async () => {
    csClient.createSecurityLaunchIssue.rejects(new Error('API Error'));

    const input = component.shadowRoot!.querySelector('sl-input');
    input!.value = '12345';
    input!.dispatchEvent(new Event('sl-input'));
    await component.updateComplete;

    const verifyButton = component.shadowRoot!.querySelector(
      'sl-button[variant="primary"]'
    ) as HTMLButtonElement;
    verifyButton!.click();

    await component.updateComplete;

    // Check the loading state.
    assert.equal(component._verificationState, 'loading');

    // Wait for the API call to reject.
    await new Promise(resolve => setTimeout(resolve, 0));
    await component.updateComplete;

    // The component should show a toast message on error.
    assert.isTrue(
      showToastMessage.calledWith(
        'Some errors occurred. Please refresh the page or try again later.'
      )
    );
    assert.equal(component._verificationState, 'error');
    assert.equal(
      component._verificationMessage,
      'Some errors occurred. Please refresh the page or try again later.'
    );
  });

  it('handles submission without a Continuity ID', async () => {
    csClient.createSecurityLaunchIssue.resolves({});

    const noIdButton = component.shadowRoot!.querySelector('.no-id-btn');
    assert.exists(noIdButton);

    (noIdButton as HTMLElement)!.click();

    await component.updateComplete;
    await new Promise(resolve => setTimeout(resolve, 0));

    // Check that the API was called without a continuity_id.
    assert.isTrue(
      csClient.createSecurityLaunchIssue.calledWith({
        feature_id: component.featureId,
        gate_id: component.gateId,
      })
    );

    assert.equal(component._verificationState, 'success');
    assert.isTrue(showToastMessage.calledWith('Success!'));
  });

  it('resets the state when the dialog is hidden', async () => {
    component._idValue = '123';
    component._verificationState = 'success';
    component._canCheck = true;
    await component.updateComplete;

    // Dispatch the hide event.
    component.dialog.dispatchEvent(new Event('sl-hide'));
    await component.updateComplete;

    // Check that the state has been reset.
    assert.equal(component._idValue, '');
    assert.equal(component._verificationState, 'idle');
    assert.isFalse(component._canCheck);
  });

  it('renders the correct suffix icon for each verification state', async () => {
    // Loading state
    component._verificationState = 'loading';
    await component.updateComplete;
    let icon = component.shadowRoot!.querySelector('sl-spinner[slot="suffix"]');
    assert.exists(icon);

    // Success state
    component._verificationState = 'success';
    await component.updateComplete;
    icon = component.shadowRoot!.querySelector(
      'sl-icon[name="check_circle_outline"]'
    );
    assert.exists(icon);
    expect(icon!.getAttribute('style')).to.contain(
      'color: var(--sl-color-success-500)'
    );

    // Error state
    component._verificationState = 'error';
    await component.updateComplete;
    icon = component.shadowRoot!.querySelector('sl-icon[name="highlight_off"]');
    assert.exists(icon);
    expect(icon!.getAttribute('style')).to.contain(
      'color: var(--sl-color-danger-500)'
    );
  });

  describe('openIdVerificationDialog', () => {
    it('creates and appends the dialog if it does not exist', async () => {
      // Ensure the dialog is not in the DOM.
      let dialogEl = document.querySelector('chromedash-continuity-id-dialog');
      if (dialogEl) {
        dialogEl.remove();
      }

      await openIdVerificationDialog(1, 2, 3);
      dialogEl = document.querySelector('chromedash-continuity-id-dialog');
      assert.exists(dialogEl);
      assert.equal((dialogEl as ChromedashIdVerificationDialog).featureId, 1);
      assert.equal((dialogEl as ChromedashIdVerificationDialog).gateId, 2);
      assert.equal(
        (dialogEl as ChromedashIdVerificationDialog).continuityId,
        3
      );
      dialogEl.remove();
    });

    it('reuses the existing dialog', async () => {
      // Ensure the dialog is not in the DOM.
      let dialogEl = document.querySelector(
        'chromedash-continuity-id-dialog'
      ) as ChromedashIdVerificationDialog;
      if (dialogEl) {
        dialogEl.remove();
      }
      assert.isNull(dialogEl);
      await openIdVerificationDialog(1, 2, 3);

      dialogEl = document.querySelector(
        'chromedash-continuity-id-dialog'
      ) as ChromedashIdVerificationDialog;
      const showSpy = sinon.spy(dialogEl, 'show');

      await openIdVerificationDialog(4, 5, 6);

      assert.equal(dialogEl.featureId, 4);
      assert.equal(dialogEl.gateId, 5);
      assert.equal(dialogEl.continuityId, 6);
      assert.isTrue(showSpy.calledOnce);

      dialogEl.remove();
    });
  });
});
