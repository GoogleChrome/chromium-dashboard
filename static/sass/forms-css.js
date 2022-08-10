import {css} from 'lit';
import {VARS} from './_vars-css.js';

export const FORM_STYLES = [
  VARS,
  css`
    table tr[hidden] th, table tr[hidden] td {
        padding: 0;
    }

    table th {
      padding: 12px 10px 5px 0;
      vertical-align: top;
    }

    table td {
      padding: 6px 10px;
      vertical-align: top;
    }

    table td:first-of-type { 
      width: 60% 
    }

    table .helptext {
      display: block;
      font-size: small;
      max-width: 40em;
      margin-top: 2px;
    }

    table input[type="text"], table input[type="url"],
    table input[type="email"], table textarea {
      width: 100%;
      font: var(--form-element-font);
    }

    table select {
      max-width: 350px;
    }

    table:required {
      border: 1px solid $chromium-color-dark;
    }

    table .interacted:valid {
      border: 1px solid green;
    }

    table .interacted:invalid {
      border: 1px solid $invalid-color;
    }

    table input:not([type="submit"]):not([type="search"]) {
      outline: 1px dotted var(--error-border-color);
      background-color: #FFEDF5;
    }

    input, textarea {
      padding: 7px;
    }

    li {
      list-style: none;
    }

    form[name="feature_form"] h3 {
      margin: var(--content-padding-half) 0;
    }
    form[name="feature_form"] input[type="submit"] {
      margin-top: var(--content-padding);
    }

    form[name="feature_form"] .stage_form {
      margin-bottom: 2em;
    }

    form section.flat_form + h3, .final_buttons {
      margin-top: 2em;
    }

    #metadata, .stage_form, .flat_form, .final_buttons {
      max-width: 67em;
      padding: 1em;
    }

    #metadata, .stage_form, .flat_form {
      color: #444;
      background: white;
      border: 1px solid #ccc;
      box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
    }

    #metadata-readonly div + div {
      margin-top: 4px;
    }

    sl-input::part(base) {
      overflow: visible;
    }

    sl-input[invalid]::part(input),
    sl-checkbox[invalid]::part(input),
    chromedash-textarea[invalid]::part(textarea)
    {
      outline: 1px dotted red;
      background-color: #FFEDF5;
    }

    sl-select[size="small"] sl-menu-item::part(base) {
      font-size: var(--sl-font-size-x-small);
      padding: 0px;
    }

    /* Hide select until loading is done and the component is defined. */
    :not(:defined) {
      visibility: hidden;
    }

    /* menu items for selects should not be displayed at all, until defined */
    sl-select sl-menu-item:not(:defined) {
      display: none 
    }
  `];
