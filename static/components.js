/** This is the entry file for rollup. It bundles all the web components: polymer-paper components and our own components */

// polymer components
import '@polymer/app-layout';
import '@polymer/app-layout/app-scroll-effects/effects/waterfall';
import '@polymer/iron-icon';
import '@polymer/iron-iconset-svg';
import '@polymer/paper-item';
import '@polymer/paper-listbox';
import '@polymer/paper-ripple';
import '@polymer/paper-styles/color.js';

// chromedash components
import './elements/icons';
import './elements/chromedash-color-status';
import './elements/chromedash-feature';
import './elements/chromedash-featurelist';
import './elements/chromedash-legend';
import './elements/chromedash-metadata';
import './elements/chromedash-metrics';
import './elements/chromedash-process-overview';
import './elements/chromedash-sample-panel';
import './elements/chromedash-schedule';
import './elements/chromedash-timeline';
import './elements/chromedash-toast';
import './elements/chromedash-userlist';
import './elements/chromedash-x-meter';
