/** This is the entry file for rollup. It bundles all the web components: polymer-paper components and our own components */

// polymer components
import '@polymer/iron-collapse';
import '@polymer/iron-icon';
import '@polymer/iron-iconset-svg';

// Shoelace components
// css is imported via _base.html in base.css, built by gulpfile.babel.js.
import '@shoelace-style/shoelace/dist/components/button/button.js';
import '@shoelace-style/shoelace/dist/components/checkbox/checkbox.js';
import '@shoelace-style/shoelace/dist/components/dialog/dialog.js';
import '@shoelace-style/shoelace/dist/components/details/details.js';
import '@shoelace-style/shoelace/dist/components/dropdown/dropdown.js';
import '@shoelace-style/shoelace/dist/components/icon/icon.js';
import '@shoelace-style/shoelace/dist/components/icon-button/icon-button.js';
import '@shoelace-style/shoelace/dist/components/input/input.js';
import '@shoelace-style/shoelace/dist/components/menu/menu.js';
import '@shoelace-style/shoelace/dist/components/menu-item/menu-item.js';
import '@shoelace-style/shoelace/dist/components/progress-bar/progress-bar.js';
import '@shoelace-style/shoelace/dist/components/relative-time/relative-time.js';
import '@shoelace-style/shoelace/dist/components/skeleton/skeleton.js';
import '@shoelace-style/shoelace/dist/components/select/select.js';
import '@shoelace-style/shoelace/dist/components/textarea/textarea.js';
import {setBasePath} from '@shoelace-style/shoelace/dist/utilities/base-path.js';

// Set the base path to the folder you copied Shoelace's assets to
setBasePath('/static/shoelace');

// Configure shoelace to also find material design 24pt outline icons
// like: <sl-icon-button library="material" name="unfold-more">
// See developer-documentation.md for instructions adding icons.
import { registerIconLibrary } from '@shoelace-style/shoelace/dist/utilities/icon-library.js';
registerIconLibrary('material', {
  resolver: name =>  `/static/shoelace/assets/material-icons/${name}.svg`,
  mutator: svg => svg.setAttribute('fill', 'currentColor')
});


// chromedash components
import './elements/icons';
import './elements/chromedash-all-features-page';
import './elements/chromedash-activity-log';
import './elements/chromedash-app';
import './elements/chromedash-approvals-dialog';
import './elements/chromedash-banner';
import './elements/chromedash-callout';
import './elements/chromedash-color-status';
import './elements/chromedash-feature';
import './elements/chromedash-feature-detail';
import './elements/chromedash-feature-filter';
import './elements/chromedash-feature-page';
import './elements/chromedash-feature-table';
import './elements/chromedash-feature-row';
import './elements/chromedash-featurelist';
import './elements/chromedash-footer';
import './elements/chromedash-form-field';
import './elements/chromedash-form-table';
import './elements/chromedash-gate-chip';
import './elements/chromedash-gantt';
import './elements/chromedash-guide-edit-page';
import './elements/chromedash-guide-editall-page';
import './elements/chromedash-guide-metadata';
import './elements/chromedash-guide-new-page';
import './elements/chromedash-guide-stage-page';
import './elements/chromedash-guide-verify-accuracy-page';
import './elements/chromedash-header';
import './elements/chromedash-legend';
import './elements/chromedash-metadata';
import './elements/chromedash-myfeatures-page';
import './elements/chromedash-process-overview';
import './elements/chromedash-settings-page';
import './elements/chromedash-stack-rank';
import './elements/chromedash-stack-rank-page';
import './elements/chromedash-textarea';
import './elements/chromedash-timeline';
import './elements/chromedash-timeline-page';
import './elements/chromedash-toast';
import './elements/chromedash-roadmap';
import './elements/chromedash-roadmap-milestone-card';
import './elements/chromedash-roadmap-page';
import './elements/chromedash-userlist';
import './elements/chromedash-x-meter';
