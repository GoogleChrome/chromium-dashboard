import { css } from "lit";
import { SHARED_STYLES } from "../shared-css.js";

export const FEATURELIST_CSS = [
  SHARED_STYLES,
  css`
    :host {
      display: block;
    }
    #ironlist {
      min-height: 0;
    }
    .milestone-marker {
      margin: 32px 0 8px 0;
      font-size: 18px;
      -webkit-font-smoothing: initial;
    }
    .item {
      width: 100%;
      padding-bottom: 8px;
    }
    p {
      margin: 32px;
    }
    @media only screen and (max-width: 700px) {
      .milestone-marker {
        font-size: 14px;
        font-weight: 500;
        margin: 8px;
      }
      [data-first-of-milestone]:after {
        font-size: 12px;
        font-weight: normal;
        top: -22px;
        opacity: 1;
        text-transform: uppercase;
      }
    }
  `,
];
