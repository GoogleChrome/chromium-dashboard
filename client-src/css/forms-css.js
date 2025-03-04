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
      width: 60%;
    }

    table .helptext {
      display: block;
      font-size: small;
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

    .fade-in {
      animation:fadeIn 0.5s linear;
    }

    @keyframes fadeIn {
      0% {
        opacity:0
      }
      100% {
        opacity:1;
      }
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
      display: none;
    }

    chromedash-form-field {
      display: table-row-group;
    }

    chromedash-form-field tr[hidden] th,
    chromedash-form-field tr[hidden] td {
      padding: 0;
    }

    chromedash-form-field th,
    chromedash-form-field td {
      text-align: left;
      vertical-align: top;
    }

    chromedash-form-field th {
      padding: 12px 10px 5px 0;
    }

    chromedash-form-field td {
      padding: 6px 10px;
    }

    chromedash-form-field td:first-of-type {
      width: 60%;
      max-width: 35em;
    }

    chromedash-form-field .check-warning {
      color: orange;
    }

    chromedash-form-field .check-error {
      color: red;
    }

    chromedash-form-field .helptext {
      display: block;
      font-size: small;
      margin-top: 2px;
    }

    chromedash-form-field .helptext > *:first-child {
      margin-top: 0;
    }
    chromedash-form-field .helptext > *:last-child {
      margin-bottom: 0;
    }

    chromedash-form-field .helptext p {
      margin: 1em 0;
    }

    chromedash-form-field .helptext ul {
      margin: 1em 0;
    }

    chromedash-form-field .helptext li {
      list-style: circle;
      margin-left: 2em;
    }

    chromedash-form-field .helptext blockquote {
      margin: 1em;
      border: 1px solid lightgrey;
      padding: 0.5em;
    }

    chromedash-form-field .errorlist {
      color: red;
    }

    chromedash-form-field sl-input[data-user-invalid]::part(base),
    chromedash-form-field chromedash-textarea[data-user-invalid]::part(base) {
      border-color: red;
    }

    chromedash-form-field sl-details::part(base) {
      border-width: 0;
    }

    chromedash-form-field sl-details::part(header) {
      padding: 0;
      display: none;
    }

    chromedash-form-field sl-details::part(content) {
      padding-top: 0;
    }

    chromedash-form-field sl-icon-button::part(base) {
      font-size: 16px;
      color: var(--link-color);
      padding: 0;
      margin: 4px;
    }

    chromedash-form-field td.extrahelp {
      padding-left: 2em;
    }
    chromedash-form-field .extrahelp > span, chromedash-form-field .webdx > span {
      margin: 0;
    }

    chromedash-form-field .datalist-input {
      width: 100%;
      height: 30px;
      border-radius: 4px;
      padding-left: 12px;
      font-family: inherit;
      font-size: inherit;
      color: #27272a;
    }
    chromedash-form-field .datalist-input:hover {
      border-color: #aaa;
    }
    chromedash-form-field .datalist-input:focus {
      outline: none;
      border-color: #0ea5e9;
    }

    chromedash-form-field .datalist-input-wrapper {
      border-radius: 4px;
    }
    chromedash-form-field .datalist-input-wrapper:focus-within {
      box-shadow: 0 0 0 3px #0ea5e966;
    }

    sl-skeleton {
      margin-bottom: 1em;
      width: 60%;
    }
    sl-skeleton:nth-of-type(even) {
      width: 50%;
    }

    h3 sl-skeleton {
      margin-top: 1em;
      width: 30%;
      height: 1.5em;
    }

    .choices label {
      font-weight: bold;
    }
    .choices div {
      margin-top: 1em;
    }
    .choices p {
      margin: 0.5em 1.5em 1em;
    }
  `];
