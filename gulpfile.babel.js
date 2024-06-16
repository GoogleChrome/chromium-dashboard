'use strict';

import rollupResolve from '@rollup/plugin-node-resolve';
import {deleteAsync} from 'del';
import gulp from 'gulp';
import autoPrefixer from 'gulp-autoprefixer';
import babel from 'gulp-babel';
import concat from 'gulp-concat';
import license from 'gulp-license';
import rename from 'gulp-rename';
import gulpSass from 'gulp-sass';
import uglifyEs from 'gulp-uglify-es';
import {rollup} from 'rollup';
import rollupMinify from 'rollup-plugin-babel-minify';
import dartSass from 'sass';
const sass = gulpSass( dartSass );
const uglify = uglifyEs.default;

function uglifyJS() {
  return uglify({
    output: {comments: 'some'},
  });
}

function addLicense() {
  return license('Apache2', {
    organization: 'Copyright (c) 2016 The Google Inc. All rights reserved.',
    tiny: true
  });
}

function rollupIgnoreUndefinedWarning(warning, warn) {
  // There is currently a warning when using the es6 module from openapi.
  // It is a common issue and can be suppresed.
  // The error that is suppresed:
  // The 'this' keyword is equivalent to 'undefined' at the top level of an ES module, and has been rewritten
  // https://github.com/rollup/rollup/issues/1518#issuecomment-321875784
  // Suppres that error but continue to print the remaining errors.
  if (warning.code === 'THIS_IS_UNDEFINED') return;
  warn(warning); // this requires Rollup 0.46
}

// Compile and automatically prefix stylesheets
// This task is deprecated. Use css directly.
gulp.task('styles', () => {
  const AUTOPREFIXER_BROWSERS = [
    'last 1 version',
    'last 2 iOS versions'
  ];

  // For best performance, don't add Sass partials to `gulp.src`
  return gulp.src([
    'client-src/sass/**/*.scss'
  ])
    .pipe(sass({
      precision: 10
    }).on('error', sass.logError))
    .pipe(autoPrefixer(AUTOPREFIXER_BROWSERS))
    .pipe(gulp.dest('static/css'));
});

gulp.task('css', () => {
  return gulp.src([
    'node_modules/@shoelace-style/shoelace/dist/themes/light.css',
   ])
  .pipe(concat('base.css'))
  .pipe(gulp.dest('static/css'));
});

gulp.task('rollup', () => {
  return rollup({
    input: [
      'build/components.js',
      'build/js-src/openapi-client.js',
    ],
    plugins: [
      rollupResolve(),
      rollupMinify({mangle: false, comments: false}),
    ],
    onwarn: rollupIgnoreUndefinedWarning,
  }).then(bundle => {
    return bundle.write({
      dir: 'static/dist',
      format: 'es',
      sourcemap: true,
      compact: true,
    });
  });
});

gulp.task('rollup-cjs', () => {
  return rollup({
    input: [
      'client-src/js-src/openapi-client.js',
    ],
    plugins: [
      rollupResolve(),
      rollupMinify({mangle: false, comments: false}),
    ],
    onwarn: rollupIgnoreUndefinedWarning,
  }).then(bundle => {
    return bundle.write({
      dir: 'static/dist',
      format: 'cjs',
      sourcemap: true,
      compact: true,
    });
  });
});

// Run scripts through babel.
gulp.task('js', () => {
  return gulp.src([
    'client-src/js-src/**/*.js',
    // openapi-client has imports and needs to use rollup.
    // exclude it from the list.
    // Else, the file will need to be treated as a module.
    // Browsers defer loading <script type="module"> tags and this client is
    // needed early on page load.
    '!client-src/js-src/**/openapi-client*.js',
  ])
    .pipe(babel()) // Defaults are in .babelrc
    .pipe(uglifyJS())
    .pipe(addLicense()) // Add license to top.
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest('static/js'));
});

// Clean generated files
gulp.task('clean', () => {
  return deleteAsync([
    // Disabled as part of removing sass/scss.
    // 'static/css/',
    'static/dist',
    'static/js/',
  ], {dot: true});
});


// Build production files, the default task
gulp.task('default', gulp.series(
  'clean',
  // Incrementally removing sass/scss.
  // 'styles',
  'css',
  'js',
  'rollup',
  'rollup-cjs',
));

// Build production files, the default task
gulp.task('watch', gulp.series(
  'default',
  () => {
    gulp.watch(['client-src/sass/**/*.scss'], gulp.series('styles'));
    gulp.watch([
      'client-src/js-src/**/*.js',
      'client-src/elements/*.js',
      'client-src/elements/*.ts',
      'client-src/elements/css/**/*.js',
      'client-src/contexts/*.js',
    ], gulp.series(['js']));
    gulp.watch([
      'client-src/components.js',
      'client-src/elements/*.js',
      'client-src/elements/css/**/*.js',
      'client-src/contexts/*.js',
    ], gulp.series(['rollup']));
  },
));
