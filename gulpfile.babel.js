'use strict';

import rollupResolve from '@rollup/plugin-node-resolve';
import {deleteAsync} from 'del';
import gulp from 'gulp';
import autoPrefixer from 'gulp-autoprefixer';
import babel from 'gulp-babel';
import concat from 'gulp-concat';
import license from 'gulp-license';
import rename from 'gulp-rename';
import uglifyEs from 'gulp-uglify-es';
import {rollup} from 'rollup';
import rollupMinify from 'rollup-plugin-babel-minify';
const uglify = uglifyEs.default;

function uglifyJS() {
  return uglify({
    output: {comments: 'some'},
  });
}

function addLicense() {
  return license('Apache2', {
    organization: 'Copyright (c) 2024 The Google Inc. All rights reserved.',
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
      'build/js-src/cs-client.js',
      'build/js-src/features-page.js',
      'build/js-src/shared.js',
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

// Clean generated files
gulp.task('clean', () => {
  return deleteAsync([
    'static/dist',
  ], {dot: true});
});


// Build production files, the default task
gulp.task('default', gulp.series(
  'clean',
  'css',
  'rollup',
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
