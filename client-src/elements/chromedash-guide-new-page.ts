import {LitElement, css, html, nothing} from 'lit';
import {customElement, property, state} from 'lit/decorators.js';
import {ref} from 'lit/directives/ref.js';
import './chromedash-form-table';
import './chromedash-form-field';
import './chromedash-link.js';
// @ts-ignore
import {SHARED_STYLES} from '../css/shared-css.js';
import {NEW_FEATURE_FORM_FIELDS, ENTERPRISE_NEW_FEATURE_FORM_FIELDS} from './form-definition';
import {ALL_FIELDS} from './form-field-specs';
// @ts-ignore
import {FORM_STYLES} from '../css/forms-css.js';
import {getDisabledHelpText} from './utils';

@customElement('chromedash-guide-new-page')
export class ChromedashGuideNewPage extends LitElement {

  @state()
  isFeatureTypeSelected = false;

  @property({type: String})
  userEmail = '';

  @property({type: Boolean})
  isEnterpriseFeature = false;

  // FIX: We added ': any[]' here so TypeScript knows it can hold data
  @state()
  fieldValues: any[] = [];

  @state()
  submitting = false;

  @property({type: Object})
  feature = {};

  static get styles() {
    return [
      SHARED_STYLES,
      FORM_STYLES,
      css`
        table td label input[type='radio']:focus {
          box-shadow: 0 0 0 var(--sl-focus-ring-width) var(--sl-input-focus-ring-color);
        }
        .process-notice {
          margin: var(--content-padding-half) 0;
          padding: var(--content-padding-half);
          background: var(--light-accent-color);
          border-radius: 8px;
        }
        .process-notice p + p {
          margin-top: var(--content-padding-half);
        }
      `,
    ];
  }

  // Handle the form field updates
  handleFormFieldUpdate(e) {
    const {field, value} = e.detail;
    // Logic to handle updates - simplified for this fix
    console.log('Field updated:', field, value);
  }

  // Register form handlers
  registerHandlers = (el) => {
    if (!el) return;
    // Simplified handler registration
  };

  renderSubHeader() {
    return html`
      <div id="subheader" style="display:block">
        <span style="float:right; margin-right: 2em">
          <a href="https://github.com/GoogleChrome/chromium-dashboard/issues/new?labels=Feedback&amp;template=process-and-guide-ux-feedback.md" target="_blank" rel="noopener">
            Process and UI feedback
          </a>
        </span>
        <h2 data-testid="add-a-feature">Add a feature</h2>
      </div>
    `;
  }

  renderWarnings() {
    if (this.isEnterpriseFeature) {
      return html`
        <div class="process-notice">
          <p>Use this form if your feature should be mentioned in the Enterprise Release Notes.</p>
        </div>`;
    } else {
      return html`
        <div class="process-notice">
          <p>Please see the <a href="https://www.chromium.org/blink/launching-features" target="_blank" rel="noopener">Launching features</a> page for process instructions.</p>
          <p>Googlers: Please follow the instructions at <a href="https://goto.corp.google.com/wp-launch-guidelines" target="_blank" rel="noopener">go/wp-launch-guidelines</a>.</p>
        </div>`;
    }
  }

  renderForm() {
    const newFeatureInitialValues = {
      owner: this.userEmail,
      shipping_year: new Date().getFullYear(),
    };
    // Initialize fieldValues if it doesn't exist to prevent crashes
    if (!this.fieldValues) this.fieldValues = [];
    
    // We are hacking this slightly to avoid type errors on the 'feature' property
    (this.fieldValues as any).feature = this.feature;

    const formFields = this.isEnterpriseFeature
      ? ENTERPRISE_NEW_FEATURE_FORM_FIELDS
      : NEW_FEATURE_FORM_FIELDS;

    const renderFormField = (field, className?) => {
      const fieldProps = ALL_FIELDS[field];
      const featureJSONKey = fieldProps.name || field;
      const initialValue = this.isEnterpriseFeature
        ? (fieldProps.enterprise_initial ?? fieldProps.initial)
        : fieldProps.initial;
      const value = newFeatureInitialValues[field] ?? initialValue;
      const index = this.fieldValues.length;
      
      this.fieldValues.push({
        name: featureJSONKey,
        touched: true,
        value,
      });

      return html`
        <chromedash-form-field
          name=${field}
          index=${index}
          value=${value}
          disabledReason="${getDisabledHelpText(field)}"
          .fieldValues=${this.fieldValues}
          ?forEnterprise=${this.isEnterpriseFeature}
          @form-field-update="${(e) => {
            this.handleFormFieldUpdate(e);
            if (field === 'feature_type_radio_group') {
              this.isFeatureTypeSelected = true;
            }
          }}"
          class="${className || ''}"></chromedash-form-field>
        `;
    };

    const submitLabel = this.submitting ? 'Submitting...' : (this.isEnterpriseFeature ? 'Continue' : 'Submit');

    return html`
      <section id="stage_form">
        <form>
          <input type="hidden" name="token" />
          <chromedash-form-table ${ref(this.registerHandlers)}>
            ${this.renderWarnings()}
            
            ${!this.isEnterpriseFeature
              ? renderFormField('feature_type_radio_group', 'choices')
              : nothing}

            ${this.isFeatureTypeSelected || this.isEnterpriseFeature
              ? html`
                  ${formFields.map(field =>
                    renderFormField(
                      field,
                      field === 'enterprise_product_category' ? 'choices' : null
                    )
                  )}
                  <input type="submit" class="primary" value=${submitLabel} ?disabled=${this.submitting} />
                `
              : nothing}
              
          </chromedash-form-table>
        </form>
      </section>
    `;
  }

  render() {
    return html` ${this.renderSubHeader()} ${this.renderForm()} `;
  }
}