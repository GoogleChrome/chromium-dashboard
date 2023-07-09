import {css} from 'lit';
import {VARS} from './_vars-css.js';
import {RESET} from './_reset-css.js';

export const SHARED_STYLES = [
  VARS,
  RESET,
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

  .description {
    line-height: 1.4;
  }

  .comma::after {
    content: ",";
    margin-right: 0.2em;
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

  .feature-link {
    display: inline;
    white-space: normal;
    line-break: anywhere;
    color: var(--default-font-color);
  }

  .feature-link:hover {
    text-decoration: none;
  }

  .feature-link sl-badge::part(base) {
    height: 14px;
    padding: 4px;
    border-width: 0;
    text-transform: capitalize;
    font-weight: 400;
  }

  .feature-link sl-tag::part(base) {
    vertical-align: middle;
    height: 18px;
    background-color: rgb(232,234,237);
    color: var(--default-font-color);
    border: none;
    border-radius: 500px;
    display: inline-flex;
    align-items: center;
    column-gap: 0.3em;
    padding: 1px 5px;
    margin: 1px 0;
  }

  .feature-link sl-tag::part(base):hover {
    background-color: rgb(209,211,213);
  }

  .feature-link .icon {
    display: block;
    width: 12px;
    height: 12px;
  }

  .feature-link-tooltip {
    display: flex;
    flex-direction: column;
    row-gap: 0.5em;
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
