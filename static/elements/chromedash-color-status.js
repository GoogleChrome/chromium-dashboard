// Import the LitElement base class and html helper function
import { LitElement, html } from 'lit-element';

// Extend the LitElement base class
class MyElement extends LitElement {

  /**
   * Implement `render` to define a template for your element.
   *
   * You must provide an implementation of `render` for any element
   * that uses LitElement as a base class.
   */
  render(){
    /**
     * `render` must return a lit-html `TemplateResult`.
     *
     * To create a `TemplateResult`, tag a JavaScript template literal
     * with the `html` helper function:
     */
    return html`
      <!-- template content -->
      <p>A paragraph</p>
    `;
  }
}
// Register the new element with the browser.
customElements.define('chromedash-color-status', MyElement);

// <dom-module id="chromedash-color-status">
//   <link rel="import" type="css" href="../css/elements/chromedash-color-status.css">
//   <template>
//     <span id="status"></span>
//   </template>
//   <script>
//     Polymer({
//       is: 'chromedash-color-status',
//       properties: {
//         max: {
//           type: Number,
//           value: 7,
//           observer: '_maxChanged'
//         },
//         value: {
//           type: Number,
//           observer: '_valueChanged'
//         }
//       },
//       updateColor: function() {
//         var CYAN = 120;
//         var h = Math.round(CYAN - this.value * CYAN / this.max);
//         this.$.status.style.backgroundColor = 'hsl(' + h + ', 100%, 50%)';
//       },
//       _valueChanged: function() {
//         this.updateColor();
//       },
//       _maxChanged: function() {
//         this.updateColor();
//       }
//     });
//   </script>
// </dom-module>
