'use strict';

// This gulpfile makes use of new JavaScript features.
// Babel handles this without us having to do anything. It just works.
// You can read more about the new JavaScript features here:
// https://babeljs.io/docs/learn-es2015/

import path from 'path';
import gulp from 'gulp';
import del from 'del';
import runSequence from 'run-sequence';
// import swPrecache from 'sw-precache';
import gulpLoadPlugins from 'gulp-load-plugins';
// import pkg from './package.json';
import merge from 'merge-stream';

const $ = gulpLoadPlugins();

// Compile and automatically prefix stylesheets
gulp.task('styles', () => {
  const AUTOPREFIXER_BROWSERS = [
    'ie >= 10',
    'ie_mob >= 10',
    'ff >= 30',
    'chrome >= 34',
    'safari >= 7',
    'opera >= 23',
    'ios >= 7',
    'android >= 4.4',
    'bb >= 10'
  ];

  // For best performance, don't add Sass partials to `gulp.src`
  return gulp.src([
    'static/sass/**/*.scss'
  ])
    .pipe($.sass({
      outputStyle: 'compressed',
      precision: 10
    }).on('error', $.sass.logError))
//    .pipe($.autoprefixer(AUTOPREFIXER_BROWSERS))
    .pipe(gulp.dest('static/css'));
});

gulp.task('scripts', () => {
  // Minify the vulcanized script files (overwriting in place)
  //  - The 'base' option is used to retain the relative path of each file
  return gulp.src(
    'static/elements/*.vulcanize.js', {base: 'static'}
  )
    .pipe($.uglify())
    .pipe(gulp.dest('static'));
});

gulp.task('vulcanize', () => {
  // Vulcanize the Polymer imports, creating *.vulcanize.* files beside the
  // original input files.
  return gulp.src([
      'static/elements/elements.html',
      'static/elements/metrics-imports.html',
      'static/elements/features-imports.html',
      'static/elements/admin-imports.html',
      'static/elements/samples-imports.html',
    ], {base: 'static'}
  )
    // Vulcanize does not allow the name of the output file to be changed, so
    // must manually rename the file first.
    .pipe($.rename({suffix: '.vulcanize'}))
    .pipe(gulp.dest('static'))
    .pipe($.vulcanize({
      stripComments: true,
      inlineScripts: true,
      inlineCss: true
    }))
    // Create an external script file to satisfy CSP
    .pipe($.crisper({
      scriptInHead: false
    }))
    .pipe(gulp.dest('static'));
});

// Clean output directory
gulp.task('clean', () => del(['static/elements/*.vulcanize.{html,js}'], {dot: true}));

// Build production files, the default task
gulp.task('default', ['clean'], cb =>
  runSequence(
    'styles',
    'vulcanize',
    'scripts',
//    'generate-service-worker',
    cb
  )
);

// Copy over the scripts that are used in importScripts as part of the generate-service-worker task.
gulp.task('copy-sw-scripts', () => {
  return gulp.src(['node_modules/sw-toolbox/sw-toolbox.js', 'app/scripts/sw/runtime-caching.js'])
    .pipe(gulp.dest('dist/scripts/sw'));
});

// See http://www.html5rocks.com/en/tutorials/service-worker/introduction/ for
// an in-depth explanation of what service workers are and why you should care.
// Generate a service worker file that will provide offline functionality for
// local resources. This should only be done for the 'dist' directory, to allow
// live reload to work as expected when serving from the 'app' directory.
gulp.task('generate-service-worker', ['copy-sw-scripts'], () => {
  const rootDir = 'dist';
  const filepath = path.join(rootDir, 'service-worker.js');

  return swPrecache.write(filepath, {
    // Used to avoid cache conflicts when serving on localhost.
    cacheId: pkg.name || 'web-starter-kit',
    // sw-toolbox.js needs to be listed first. It sets up methods used in runtime-caching.js.
    importScripts: [
      'scripts/sw/sw-toolbox.js',
      'scripts/sw/runtime-caching.js'
    ],
    staticFileGlobs: [
      // Add/remove glob patterns to match your directory setup.
      `${rootDir}/images/**/*`,
      `${rootDir}/scripts/**/*.js`,
      `${rootDir}/styles/**/*.css`,
      `${rootDir}/*.{html,json}`
    ],
    // Translates a static file path to the relative URL that it's served from.
    // This is '/' rather than path.sep because the paths returned from
    // glob always use '/'.
    stripPrefix: rootDir + '/'
  });
});

// Load custom tasks from the `tasks` directory
// Run: `npm install --save-dev require-dir` from the command-line
// try { require('require-dir')('tasks'); } catch (err) { console.error(err); }
