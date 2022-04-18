import { css } from "lit";
import { VARS } from "./_vars-css.js";

export const SHARED_STYLES = [
  VARS,
  css`

  * {
    box-sizing: border-box;
    list-style: none;
    font: inherit;
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

  #updated {
    padding-top: var(--content-padding);
  }

  #updated span {
    color: var(--unimportant-text-color);
    border-top: var(--default-border);
    padding: var(--content-padding-quarter) var(--content-padding) 0 0;
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
`];
