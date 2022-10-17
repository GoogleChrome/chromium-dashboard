import {css} from 'lit';
import {SHARED_STYLES} from '../shared-css.js';

export const ROADMAP_MILESTONE_CARD_CSS = [
  SHARED_STYLES,
  css`
    .layout {
      display: flex;
    }
    .layout.wrap {
      flex-wrap: wrap;
    }
    .layout.center {
      align-items: center;
    }
    .layout.center-center {
      align-items: center;
      justify-content: center;
    }
    .layout.vertical {
      flex-direction: column;
    }
    :host {
      padding: 16px;
      background: #fff;
      padding: 16px;
      margin-bottom: 16px !important;
      border-radius: 3px;
      margin-right: 8px !important;
      margin-left: 8px !important;
      counter-reset: featurecount;
      margin: 8px;
    }
    iron-icon {
      --iron-icon-height: 18px;
      --iron-icon-width: 18px;
      color: #366597;
    }
    iron-icon:hover.android {
      color: #a4c739;
    }
    iron-icon:hover.remove {
      color: var(--paper-red-700);
    }
    iron-icon:hover.deprecated {
      color: var(--paper-orange-700);
    }
    iron-icon:hover.experimental {
      color: var(--paper-green-700);
    }
    iron-icon:hover.intervention {
      color: var(--paper-yellow-800);
    }
    iron-icon.pushicon {
      cursor: pointer;
    }
    .chrome_version {
      font-size: 45px;
      margin: 8px 0 16px 0;
      white-space: nowrap;
    }
    .channel_label {
      font-weight: 600;
      text-transform: uppercase;
      font-size: 24px;
      text-align: center;
    }
    .chrome_version .chrome-logo,
    .chrome_version--stable .chrome-logo {
      position: relative;
      width: 45px;
      height: 45px;
      background: url(/static/img/chrome_logo.svg) no-repeat 50% 50%;
      background-size: contain;
      margin-right: 8px;
    }
    .chrome_version--beta .chrome-logo {
      background-image: url(/static/img/chrome_logo_beta.svg);
    }
    .chrome_version--dev .chrome-logo {
      background-image: url(/static/img/chrome_logo_dev.svg);
    }
    .chrome_version--canary .chrome-logo {
      background-image: url(/static/img/chrome_logo_canary.svg);
      background-size: 42px;
    }
    .chrome_version--dev_plus_one .chrome-logo {
      filter: gray;
      -webkit-filter: grayscale(1);
      filter: grayscale(1);
    }
    .release {
      padding: 16px;
      background: #fff;
      padding: 16px;
      margin-bottom: 16px !important;
      border-radius: 3px;
      flex: 1 0 0;
      min-width: 300px;
      counter-reset: featurecount;
    }
    .release.no-components .feature_shipping_type {
      display: none;
    }
    .release.no-components .feature_shipping_type + ul {
      margin-top: 0;
    }
    .milestone_info {
      margin-bottom: 8px;
    }
    .milestone_info:nth-of-type(3) {
      border-bottom: 1px solid #e6e6e6;
      padding-bottom: 16px;
    }
    .milestone_info .channel_label {
      font-size: inherit;
      font-weight: 500;
      text-transform: none;
    }
    .no_feature_released {
      color: #737373;
    }
    .features_list {
      margin-top: 32px;
    }
    .features_list ul,
    .features_list ol {
      margin-top: 8px;
      list-style: none;
    }
    .features_list li {
      padding: 8px;
      font-weight: 500;
      display: flex;
      justify-content: space-between;
    }
    .features_list li .icon_row {
      flex-shrink: 0;
    }
    .features_list li > :first-child {
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .features_list .features_header {
      font-weight: 500;
      text-transform: uppercase;
      margin-bottom: 16px;
    }
    .feature_shipping_type {
      margin-top: 16px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .highlight {
      background: var(--light-accent-color);
    }
    #feature_link {
      width: 100%;
    }
    .sl-skeleton-header-container {
      display: flex;
      width: 100%;
      gap: 10px;
      justify-content: center;
      margin-top: 10px;
    }
    .sl-skeleton-header-container sl-skeleton {
      width: 60%;
    }
    .sl-skeleton-title-container {
      width: 50%;
    }
    .features_list sl-skeleton {
      height: 20px;
      margin: 8px;
    }
  `,
];
