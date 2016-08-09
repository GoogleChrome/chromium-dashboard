'use strict';

// This gulpfile makes use of new JavaScript features.
// Babel handles this without us having to do anything. It just works.
// You can read more about the new JavaScript features here:
// https://babeljs.io/docs/learn-es2015/

import path from 'path';
import gulp from 'gulp';
import del from 'del';
import runSequence from 'run-sequence';
import swPrecache from 'sw-precache';
import gulpLoadPlugins from 'gulp-load-plugins';
import merge from 'merge-stream';
import cssslam from 'css-slam';

const $ = gulpLoadPlugins();

function minifyHtml() {
  return $.minifyHtml({
    quotes: true,
    empty: true,
    spare: true
  }).on('error', console.log.bind(console));
}

function uglifyJS() {
  return $.uglify({preserveComments: 'some'});
}

function license() {
  return $.license('Apache2', {
    organization: 'Copyright (c) 2016 The Google Inc. All rights reserved.',
    tiny: true
  });
}

gulp.task('lint', () => {
  return gulp.src([
    'static/**/*.js'
  ])
    .pipe($.eslint())
    .pipe($.eslint.format())
    .pipe($.eslint.failAfterError());
});

// Compile and automatically prefix stylesheets
gulp.task('styles', () => {
  const AUTOPREFIXER_BROWSERS = [
    'last 1 version',
    'last 2 iOS versions'
  ];

  // For best performance, don't add Sass partials to `gulp.src`
  return gulp.src([
    'static/sass/**/*.scss'
  ])
    .pipe($.sass({
      outputStyle: 'compressed',
      precision: 10
    }).on('error', $.sass.logError))
    .pipe($.autoprefixer(AUTOPREFIXER_BROWSERS))
    .pipe(gulp.dest('static/css'));
});

// Run scripts through babel. Note, this does not include vulcanized js.
gulp.task('js', () => {
  return gulp.src([
    //'static/elements/*.vulcanize.js',
    'static/js/**/*.es6.js',
  ])
    .pipe($.babel()) // Defaults are in .babelrc
    .pipe(uglifyJS())
    .pipe(license()) // Add license to top.
    .pipe($.rename({suffix: '.min'}))
    .pipe(gulp.dest('static/js'));
});

// Vulcanize the Polymer imports, creating *.vulcanize.* files beside the
// original import files.
gulp.task('vulcanize-lazy-elements', () => {
  return gulp.src([
    'static/bower_components/paper-menu-button/paper-menu-button.html',
    'static/elements/chromedash-legend.html'
  ])
  .pipe($.vulcanize({
    stripComments: true,
    inlineScripts: true,
    inlineCss: true,
    // Leave out elements registered by main site or shared in other
    // lazy-loaded elements.
    stripExcludes: [
      'polymer.html$',
      'iron-meta.html',
      'chromedash-color-status.html'
    ]
  }))
  .pipe($.rename({suffix: '.vulcanize'}))
  .pipe($.crisper({scriptInHead: true})) // Separate HTML and JS. CSP friendly.
  .pipe($.if('*.html', minifyHtml())) // Minify HTML output.
  .pipe($.if('*.html', cssslam.gulp())) // Minify CSS in HTML output.
  .pipe($.if('*.js', uglifyJS())) // Minify JS in HTML output.
  .pipe($.if('*.js', license())) // Add license to top.
  .pipe(gulp.dest('static/elements'));
});

gulp.task('vulcanize', ['styles', 'vulcanize-lazy-elements'], () => {
  return gulp.src([
    'static/elements/metrics-imports.html',
    'static/elements/features-imports.html',
    'static/elements/admin-imports.html',
    'static/elements/samples-imports.html',
  ])
  .pipe($.vulcanize({
    stripComments: true,
    inlineScripts: true,
    inlineCss: true
  }))
  .pipe($.rename({suffix: '.vulcanize'}))
  .pipe($.crisper({scriptInHead: true})) // Separate HTML and JS. CSP friendly.
  .pipe($.if('*.html', minifyHtml())) // Minify HTML output.
  .pipe($.if('*.html', cssslam.gulp())) // Minify CSS in HTML output.
  .pipe($.if('*.js', uglifyJS())) // Minify JS in HTML output.
  .pipe($.if('*.js', license())) // Add license to top.
  .pipe(gulp.dest('static/elements'));
});

// Clean generated files
gulp.task('clean', () => {
  del([
    'static/css/',
    'static/dist',
    'static/elements/*.vulcanize.{html,js}',
    'static/js/**/*.es6.min.js'
  ], {dot: true});

});

// Build production files, the default task
gulp.task('default', ['clean'], cb =>
  runSequence(
    'styles',
    'lint',
    'vulcanize',
    'js',
    'generate-service-worker',
    cb
  )
);

// Generate a service worker file that will provide offline functionality for
// local resources.
gulp.task('generate-service-worker', () => {
  const staticDir = 'static';
  const distDir = path.join(staticDir, 'dist');
  const filepath = path.join(distDir, 'service-worker.js');

  return swPrecache.write(filepath, {
    cacheId: 'chromestatus',
    verbose: true,
    logger: $.util.log,
    staticFileGlobs: [
      // Images
      `${staticDir}/img/**/*`,
      `${staticDir}/elements/openinnew.svg`,
      // Scripts
      `${staticDir}/bower_components/webcomponentsjs/webcomponents-lite.min.js`,
      `${staticDir}/js/**/*.js`,
      // Styles
      `${staticDir}/css/**/*.css`,
      // Polymer imports
      // NOTE: The admin imports are intentionally excluded, as the admin pages
      //       only work online
      `${staticDir}/elements/paper-menu-button.vulcanize.*`,
      `${staticDir}/elements/chromedash-legend.vulcanize.*`,
      `${staticDir}/elements/metrics-imports.vulcanize.*`,
      `${staticDir}/elements/features-imports.vulcanize.*`,
      `${staticDir}/elements/samples-imports.vulcanize.*`,
    ],
    runtimeCaching: [
      // Server-side generated content
      {
        // The features page, which optionally has a trailing slash or a
        // feature id. For example:
        //  - /features
        //  - /features/
        //  - /features/<numeric feature id>
        // This overly-specific regex is required to avoid matching other
        // static content (i.e. /static/css/features/features.css)
        urlPattern: /\/features(\/(\w+)?)?$/,
        handler: 'fastest',
        options: {
          cache: {
            maxEntries: 10,
            name: 'features-cache'
          }
        }
      },
      {
        // The metrics pages (optionally with a trailing slash)
        //  - /metrics/css/animated
        //  - /metrics/css/timeline/animated
        //  - /metrics/css/popularity
        //  - /metrics/css/timeline/popularity
        //  - /metrics/feature/popularity
        //  - /metrics/feature/timeline/popularity
        urlPattern: /\/metrics\/(css|feature)\/(timeline\/)?(animated|popularity)(\/)?$/,
        handler: 'fastest',
        options: {
          cache: {
            maxEntries: 10,
            name: 'metrics-cache'
          }
        }
      },
      {
        // The samples page (optionally with a trailing slash)
        urlPattern: /\/samples(\/)?$/,
        handler: 'fastest',
        options: {
          cache: {
            maxEntries: 10,
            name: 'samples-cache'
          }
        }
      },
      // For dynamic data (json), try the network first to get the most recent
      // values.
      {
        urlPattern: /\/data\//,
        handler: 'networkFirst'
      },
      {
        urlPattern: /\/features.json$/,
        handler: 'networkFirst'
      },
      {
        urlPattern: /\/samples.json$/,
        handler: 'networkFirst'
      },
      {
        urlPattern: /\/omaha_data$/,
        handler: 'networkFirst'
      },
    ],
  });
});

// Load custom tasks from the `tasks` directory
// Run: `npm install --save-dev require-dir` from the command-line
// try { require('require-dir')('tasks'); } catch (err) { console.error(err); }
