import {css} from 'lit';
import {VARS} from './_vars-css.js';
import {RESET} from './_reset-css.js';
import {FLEX_BOX} from './_flexbox-css.js';

export const SHARED_STYLES = [
  VARS,
  RESET,
  FLEX_BOX,
  css`

  * {
    box-sizing: border-box;
    list-style: none;
     /* font: inherit; */
    text-decoration: inherit;
    -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
  }

  .conditional-comma:last-child {
    display: none;
  }

  .data-table {
    width: 100%;
    border: var(--default-border);
    border-radius: var(--border-radius);
  }
  .data-table th {
    text-align: left;
    background: var(--table-header-background);
    padding: var(--content-padding-half) var(--content-padding);
  }
  .data-table td {
    vertical-align: top;
    border-top: var(--default-border);
    padding: var(--content-padding-half) var(--content-padding);
  }

  h1,
  h2,
  h3,
  h4 {
    font-weight: 300;
  }

  h1 {
    font-size: 30px;
  }

  h2,
  h3,
  h4 {
    background: var(--heading-background);
    color: var(--heading-color);
  }

  h2 {
    font-size: 25px;
  }

  h3 {
    font-size: 20px;
  }

  a {
    text-decoration: none;
    color: var(--link-color);
  }
  a:hover {
    text-decoration: underline;
    color: var(--link-hover-color);
    cursor: pointer;
  }

  input:not([type="submit"]),
  textarea {
    border: 1px solid var(--bar-border-color);
  }

  input:not([type="submit"])[disabled],
  textarea[disabled],
  button[disabled] {
    opacity: 0.5;
  }

  button,
  input[type="submit"],
  .button {
    display: inline-block;
    padding: 4px 16px;
    background: var(--button-background);
    border: var(--button-border);
    border-radius: var(--button-border-radius);
    color: var(--button-color);
    white-space: nowrap;
    user-select: none;
    cursor: pointer;
    font-size: var(--button-font-size);
  }

  button.primary,
  input[type="submit"],
  .button.primary {
    background: var(--primary-button-background);
    color: var(--primary-button-color);
    font-weight: bold;
  }

  button.primary:disabled,
  input[type="submit"]:disabled,
  .button.primary:disabled {
    background: var(--gray-4);
  }

  .button.secondary {
    margin: var(--content-padding);
    border: var(--default-border);
    border-color: var(--primary-border-background);
    border-radius: var(--border-radius);
  }

  button:not(:disabled):hover {
    border-color: var(--gray-4);
  }

  #subheader {
    display: flex;
    align-items: center;
    margin: var(--content-padding) 0;
    max-width: var(--max-content-width);
    width: 100%;
  }
  #subheader div.search {
    min-width: 350px;
  }
  #subheader div input {
    width: 280px;
    padding: 10px 7px;
  }

  code {
   white-space: nowrap;
   font-family: monospace;
  }

  .description {
    line-height: 1.4;
  }

  .comma::after {
    content: ",";
    margin-right: 0.2em;
  }

  details {
    padding: var(--content-padding-quarter);
  }

  details summary {
    list-style: revert; /* Show small triangle */
    white-space: nowrap;
    box-sizing: border-box;
    contain: content;
    overflow: hidden;
    cursor: pointer;
    transition: margin 250ms ease-out;
  }

  details summary:hover {
    color: var(--link-hover-color);
  }

  details[open] #preview {
    display: none;
  }

  details[open] summary {
    margin-bottom: var(--content-padding-quarter);
  }

  details > div {
    padding: var(--content-padding-quarter);
    padding-left: var(--content-padding);
  }

  .no-web-share {
    display: none;
  }

  iron-icon {
    height: var(--icon-size);
    width: var(--icon-size);
  }

  .preformatted {
    white-space: pre-wrap;
  }

  .warning {
    margin: var(--content-padding);
    padding: var(--content-padding);
    background: var(--warning-background);
    color: var(--warning-color);
  }

  #breadcrumbs a {
    text-decoration: none;
    color: inherit;
  }

  sl-dialog::part(title) {
    padding-top: calc(var(--header-spacing) / 2);
    padding-bottom: calc(var(--header-spacing) / 2);
  }

  sl-dialog::part(close-button) {
    padding-right: 0;
  }

  sl-dialog::part(body) {
    padding-top: 0;
    padding-bottom: calc(var(--body-spacing) / 2);
  }

  sl-details::part(base) {
    margin: var(--content-padding-half) 0 0 0;
    color: var(--accordion-color);
    border: none;
    border-radius: 0;
    background-color: transparent;
  }

  sl-details::part(header) {
    border-radius: var(--accordion-border-radius);
    background: var(--accordion-background);
    font-weight: 300;
    font-size: 20px;
    padding: var(--content-padding-quarter) var(--content-padding-half)
  }

  sl-details::part(content) {
    padding: 0;
  }

  sl-skeleton {
    --color: #eee;
    --sheen-color: #ccc;
  }

  sl-relative-time {
    margin: 0 -3px;  // Mitigate spacing from unknown cause.
  }

  @media only screen and (max-width: 700px) {
    h1 {
      font-size: 24px;
    }
    h2 {
      font-size: 20px;
    }
    h3 {
      font-size: 15px;
    }

    #subheader div:not(.search):not(.actionlinks):not(.tooltips) {
      display: none;
    }

    #subheader div.search {
      text-align: center;
      min-width: 0;
      margin: 0;
    }
    #subheader div.search input {
      width: auto;
    }
  }
`];
