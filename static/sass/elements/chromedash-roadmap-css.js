import { css } from "lit";
import { SHARED_STYLES } from "../shared-css.js";
import { LAYOUT_CSS } from "../_layout-css.js";

export const ROADMAP_CSS = [
  SHARED_STYLES,
  LAYOUT_CSS,
  css`
    :host {
      display: inline-flex;
      padding: 0 0em $content-padding * 5;
      margin-right: $content-padding * -1;
    }
  `,
];
