'use strict';

// This gulpfile makes use of new JavaScript features.
// Babel handles this without us having to do anything. It just works.
// You can read more about the new JavaScript features here:
// https://babeljs.io/docs/learn-es2015/

const path = require('path');
const gulp = require('gulp');
const del = require('del');
const swPrecache = require('sw-precache');
const uglifyEs = require('gulp-uglify-es');
const uglify = uglifyEs.default;
const gulpLoadPlugins = require('gulp-load-plugins');
const eslintIfFixed = require('gulp-eslint-if-fixed');
const rollup = require('rollup');
const $ = gulpLoadPlugins();
const resolve = require('rollup-plugin-node-resolve');

function minifyHtml() {
  return $.minifyHtml({
    quotes: true,
    empty: true,
    spare: true
  }).on('error', console.log.bind(console));
}

function uglifyJS() {
  return uglify({
    output: {comments: 'some'},
  });
}

function license() {
  return $.license('Apache2', {
    organization: 'Copyright (c) 2016 The Google Inc. All rights reserved.',
    tiny: true
  });
}

gulp.task('lint', () => {
  return gulp.src([
    'static/js-src/*.js',
    'static/elements/*.js',
  ])
    .pipe($.eslint())
    .pipe($.eslint.format())
    .pipe($.eslint.failAfterError());
});

gulp.task('lint-fix', () => {
  return gulp.src([
    'static/js-src/*.js',
    'static/elements/*.js',
  ], {base: './'})
    .pipe($.eslint({fix:true}))
    .pipe($.eslint.format())
    .pipe(eslintIfFixed('./'))
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

gulp.task('rollup', () => {
  return rollup.rollup({
    input: 'static/rollup-entry',
    plugins: [
      resolve(),
    ],
  }).then(bundle => {
    return bundle.write({
      file: 'static/dist/component-bundle.js',
      format: 'es',
      sourcemap: true,
      compact: true,
    });
  });
});

// Run scripts through babel.
gulp.task('js', () => {
  return gulp.src([
    'static/js-src/**/*.js',
  ])
    .pipe($.babel()) // Defaults are in .babelrc
    .pipe(uglifyJS())
    .pipe(license()) // Add license to top.
    .pipe($.rename({suffix: '.min'}))
    .pipe(gulp.dest('static/js'));
});

// Clean generated files
gulp.task('clean', () => {
  return del([
    'static/css/',
    'static/dist',
    'static/js/',
  ], {dot: true});
});

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
      `${staticDir}/img/{browsers-logos.png,*.svg,crstatus_128.png,github-white.png}`,
      // Scripts
      `${staticDir}/js/**/!(*.es6).js`, // Don't include unminimized/untranspiled js.
    ],
    runtimeCaching: [{ // Server-side generated content
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
    }, {
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
    }, {
      // The samples page (optionally with a trailing slash)
      urlPattern: /\/samples(\/)?$/,
      handler: 'fastest',
      options: {
        cache: {
          maxEntries: 10,
          name: 'samples-cache'
        }
      }
    }, {
      // For dynamic data (json), use "fastest" so liefi scenarios are fast.
      // "fastest" also makes a network request to update the cached copy.
      // The worst case is that the user with an active SW gets stale content
      // and never refreshes the page.
      // TODO: use sw-toolbox notifyOnCacheUpdate when it's ready
      // https://github.com/GoogleChrome/sw-toolbox/pull/174/
      urlPattern: /\/data\//,
      handler: 'fastest'
    }, {
      urlPattern: /\/features(_v\d+)?.json$/,
      handler: 'fastest'
    }, {
      urlPattern: /\/samples.json$/,
      handler: 'fastest'
    }, {
      urlPattern: /\/omaha_data$/,
      handler: 'fastest'
    }]
  });
});

// Build production files, the default task
gulp.task('watch', gulp.series(
  'styles',
  'js',
  'lint-fix',
  'generate-service-worker',
  function watch() {
    gulp.watch(['static/sass/**/*.scss'], gulp.series('styles'));
    gulp.watch(['static/js-src/**/*.js', 'static/elements/*.js'], gulp.series(['lint', 'js']));
    gulp.watch(['static/rollup-entry.js', 'static/elements/*.js'], gulp.series(['rollup']));
  }
));

// Build production files, the default task
gulp.task('default', gulp.series(
  'clean',
  'styles',
  'js',
  'lint-fix',
  'rollup',
  'generate-service-worker',
));
