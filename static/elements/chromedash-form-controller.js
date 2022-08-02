import {FormSubmitController} from '@shoelace-style/shoelace/dist/internal/form.js';

export class ChromedashFormSubmitController extends FormSubmitController {
//   constructor(host, options) {
//     this.options = Object.assign({
//       form: (input) => input.closest('form'),
//       name: (input) => input.name,
//       value: (input) => input.value,
//       defaultValue: (input) => input.defaultValue,
//       disabled: (input) => input.disabled,
//       reportValidity: (input) => {
//         return typeof input.reportValidity === 'function' ? input.reportValidity() : true;
//       }, setValue: (input, value) => {
//         input.value = value;
//       }}, options);
//     (this.host = host).addController(this);
//     this.handleFormData = this.handleFormData.bind(this);
//     this.handleFormSubmit = this.handleFormSubmit.bind(this);
//     this.handleFormReset = this.handleFormReset.bind(this);
//     this.reportFormValidity = this.reportFormValidity.bind(this);
//   }

  hostConnected() {
    if (!this.options) return;
    super.hostConnected();
  }
}
