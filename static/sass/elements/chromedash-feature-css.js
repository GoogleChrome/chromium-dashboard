import { css } from "lit";
import { SHARED_STYLES } from "../shared-css.js";

export const FEATURE_CSS = [
  SHARED_STYLES,
  css`
    :host {
      display: block;
      position: relative;
      background: #fff;
      border-radius: 3px;
      border: 1px solid #ddd;
      box-shadow: rgba(0, 0, 0, 0.067) 1px 1px 4px;
      padding: 10px 10px 10px 20px !important;
      list-style: none;
      box-sizing: border-box;
      contain: content;
      overflow: hidden;
    }
    :host:active {
      outline: none;
    }
    :host([open]) {
      outline: none;
    }
    :host([open]) .desc summary {
      white-space: normal;
    }
    [hidden] {
      display: none !important;
    }
    button {
      background: transparent;
      border: 0;
      padding: 0;
    }
    h2 {
      display: inline-block;
      font-size: 25px;
      flex: 1 0 0;
    }
    iron-icon {
      --iron-icon-height: 20px;
      --iron-icon-width: 20px;
    }
    iron-icon.android {
      color: #a4c739;
    }
    iron-icon.remove {
      color: var(--paper-red-700);
    }
    iron-icon.deprecated {
      color: var(--paper-orange-700);
    }
    iron-icon.experimental {
      color: var(--paper-green-700);
    }
    iron-icon.intervention {
      color: var(--paper-yellow-800);
    }
    iron-icon.disabled {
      opacity: 0.5;
    }
    .opennew {
      width: 18px;
      height: 18px;
    }
    .open-standalone {
      position: absolute;
      right: 0;
      top: 0;
      display: flex;
      align-items: center;
      height: 100%;
      border-left: 2px solid #eee;
      padding: 4px;
    }
    .iconrow {
      display: flex;
      align-items: center;
    }
    .category-tooltip,
    .topcorner .tooltip {
      margin-left: 4px;
    }
    .topcorner a {
      text-decoration: none;
    }
    hgroup {
      display: flex;
      align-items: flex-start;
      cursor: pointer;
    }
    hgroup .category {
      color: #a9a9a9;
    }
    hgroup chromedash-color-status {
      position: absolute;
      top: 0;
      left: 0;
    }
    section {
      margin: 18px 0;
    }
    section.desc {
      margin: 10px 0 0 0;
      cursor: pointer;
      color: #797979;
      line-height: 20px;
    }
    section.desc summary p:not(.preformatted) {
      text-overflow: ellipsis;
      overflow: hidden;
      white-space: nowrap;
    }
    section.desc summary p:not(:first-child) {
      margin: 10px 0 0 0;
    }
    section h3 {
      margin: 10px 0;
      font-size: 18px;
      font-weight: 400;
    }
    section div > span {
      flex-shrink: 0;
    }
    section .impl_status {
      display: flex;
      flex-direction: column;
    }
    section .impl_status > span {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px;
    }
    section .impl_status > span:nth-of-type(odd) {
      background: #eee;
    }
    section .impl_status .chromium_status {
      font-weight: 500;
    }
    section .impl_status .vendor_icon,
    section .impl_status .chrome_icon,
    section .impl_status .opera_icon {
      background: url(/static/img/browsers-logos.png) no-repeat;
      background-size: cover;
      height: 20px;
      width: 20px;
      margin-right: 4px;
      display: inline-block;
    }
    section .impl_status .chrome_icon {
      background-position: 0px 50%;
    }
    section .impl_status .opera_icon {
      background-position: -75px 50%;
    }
    section .impl_status_label {
      display: flex;
      align-items: center;
    }
    section .impl_status_icons {
      display: flex;
      align-items: center;
      min-width: 50px;
    }
    section .views {
      display: flex;
      flex-wrap: wrap;
    }
    section .views .view {
      display: flex;
      align-items: center;
      position: relative;
      height: 35px;
      background: #eee;
      margin: 0 8px 16px 0;
      padding: 8px;
    }
    section .views .standardization .vendor-view {
      margin-left: 0;
    }
    section .views iron-icon {
      margin: 0 8px;
    }
    section .views .vendor-view {
      background: url(/static/img/browsers-logos.png) no-repeat;
      background-size: cover;
      height: 16px;
      margin: 8px;
      display: inline-block;
    }
    section .views .edge-view {
      background-position: -80px 50%;
      width: 16px;
    }
    section .views .safari-view {
      background-position: -20px 50%;
      width: 17px;
    }
    section .views .ff-view {
      background-position: -40px 50%;
      width: 17px;
    }
    section .views .w3c-view {
      background-position: -99px 50%;
      width: 22px;
    }
    section chromedash-color-status {
      overflow: hidden;
    }
    section chromedash-color-status.bottom {
      margin-top: 3px;
    }
    section .owner-list {
      display: flex;
      align-items: flex-end;
      flex-direction: column;
    }
    section .owner-list a {
      display: block;
    }
    section .comments html-echo {
      white-space: pre-wrap;
    }
    section .doc_links,
    section .sample_links,
    section .owner {
      flex-shrink: 1 !important;
    }
    section .sample_links {
      margin-left: 8px;
    }
    .sidebyside {
      display: flex;
      justify-content: space-between;
    }
    .sidebyside .flex {
      flex: 0 0 calc(50% - 16px);
    }
    .resources label {
      margin-right: 8px;
    }
    @media only screen and (max-width: 700px) {
      :host {
        border-radius: 0 !important;
        margin: 7px initial !important;
        transition: none !important;
      }
      iron-icon {
        --iron-icon-height: 16px;
        --iron-icon-width: 16px;
      }
      h2 {
        font-size: 20px !important;
      }
      section {
        margin-left: 0;
      }
      .category {
        display: none;
      }
      .impl_status > span:not([hidden]):not(:last-of-type),
      .impl_status > a {
        margin-bottom: 10px;
      }
      .views > span {
        margin-bottom: 10px;
      }
      .sidebyside {
        display: block;
      }
    }
    @media only screen and (min-width: 701px) {
      .resources {
        display: flex;
        align-items: center;
      }
    }
  `,
];
