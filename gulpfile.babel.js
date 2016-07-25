'use strict';

// This gulpfile makes use of new JavaScript features.
// Babel handles this without us having to do anything. It just works.
// You can read more about the new JavaScript features here:
// https://babeljs.io/docs/learn-es2015/

import path from 'path';
import gulp from 'gulp';
import del from 'del';
import runSequence from 'run-sequence';
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
    organization: 'Copyright (c) 2016 The Chromium Authors. All rights reserved.',
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

// // Minify the vulcanized script files
// gulp.task('scripts', () => {
//   // The script files are overwritten (as they are generated anyways)
//   //  - The 'base' option is needed to retain the relative path of each file,
//   //    allow overwriting
//   return gulp.src(
//     'static/elements/*.vulcanize.js', {base: 'static'}
//   )
//     .pipe(uglifyJS())
//     .pipe(gulp.dest('static'));
// });

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
    // 'static/elements/elements.html',
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
  del(['static/elements/*.vulcanize.{html,js}', 'static/css/'], {dot: true});
});

// Build production files, the default task
gulp.task('default', ['clean'], cb =>
  runSequence(
    'styles',
    'lint',
    'vulcanize',
    // 'scripts',
    cb
  )
);

// Load custom tasks from the `tasks` directory
// Run: `npm install --save-dev require-dir` from the command-line
// try { require('require-dir')('tasks'); } catch (err) { console.error(err); }
