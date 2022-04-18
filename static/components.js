/** This is the entry file for rollup. It bundles all the web components: polymer-paper components and our own components */

// polymer components
import '@polymer/app-layout';
import '@polymer/app-layout/app-scroll-effects/effects/waterfall';
import '@polymer/iron-collapse';
import '@polymer/iron-icon';
import '@polymer/iron-iconset-svg';
import '@polymer/paper-item';
import '@polymer/paper-listbox';
import '@polymer/paper-ripple';
import '@polymer/paper-styles/color.js';

// Shoelace components
// css is imported via _base.html in base.css, built by gulpfile.babel.js.
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import { setBasePath } from '@shoelace-style/shoelace/dist/utilities/base-path.js';

// Set the base path to the folder you copied Shoelace's assets to
setBasePath('@shoelace-style/shoelace'); // /dist/assets

// chromedash components
import './elements/icons';
import './elements/chromedash-accordion';
import './elements/chromedash-approvals-dialog';
import './elements/chromedash-banner';
import './elements/chromedash-callout';
import './elements/chromedash-color-status';
import './elements/chromedash-dialog';
import './elements/chromedash-feature';
import './elements/chromedash-feature-detail';
import './elements/chromedash-feature-filter';
import './elements/chromedash-feature-table';
import './elements/chromedash-featurelist';
import './elements/chromedash-new-feature-list';
import './elements/chromedash-gantt';
import './elements/chromedash-legend';
import './elements/chromedash-metadata';
import './elements/chromedash-metrics';
import './elements/chromedash-myfeatures';
import './elements/chromedash-process-overview';
import './elements/chromedash-timeline';
import './elements/chromedash-toast';
import './elements/chromedash-roadmap';
import './elements/chromedash-roadmap-milestone-card';
import './elements/chromedash-userlist';
import './elements/chromedash-x-meter';
