'use strict';

import gulp from 'gulp';
import babel from 'gulp-babel';
import dartSass from 'sass';
import gulpSass from 'gulp-sass';
const sass = gulpSass( dartSass );
import concat from 'gulp-concat';
import { deleteAsync } from 'del';
import uglifyEs from 'gulp-uglify-es';
const uglify = uglifyEs.default;
import rename from 'gulp-rename';
import license from 'gulp-license';
import eslint from 'gulp-eslint';
import eslintIfFixed from 'gulp-eslint-if-fixed';
import autoPrefixer from 'gulp-autoprefixer';
import { rollup } from 'rollup';
import rollupResolve from '@rollup/plugin-node-resolve';
import rollupBabel from '@rollup/plugin-babel';
import rollupMinify from 'rollup-plugin-babel-minify';

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

gulp.task('lint', () => {
  return gulp.src([
    'client-src/js-src/*.js',
    'client-src/elements/*.js',
    'client-src/contexts/*.js',
  ])
    .pipe(eslint())
    .pipe(eslint.format())
    .pipe(eslint.failAfterError());
});

gulp.task('lint-fix', () => {
  return gulp.src([
    'client-src/js-src/*.js',
    'client-src/elements/*.js',
    'client-src/contexts/*.js',
  ], {base: './'})
    .pipe(eslint({fix:true}))
    .pipe(eslint.format())
    .pipe(eslintIfFixed('./'))
    .pipe(eslint.failAfterError());
});

// Compile and automatically prefix stylesheets
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
      outputStyle: 'compressed',
      precision: 10
    }).on('error', sass.logError))
    .pipe(autoPrefixer(AUTOPREFIXER_BROWSERS))
    .pipe(gulp.dest('static/css'));
});

gulp.task('css', function() {
  return gulp.src([
    'node_modules/@shoelace-style/shoelace/dist/themes/light.css',
   ])
  .pipe(concat('base.css'))
  .pipe(gulp.dest('static/css'));
});

gulp.task('rollup', () => {
  return rollup({
    input: [
      'client-src/components.js',
      'client-src/js-src/openapi-client.js',
    ],
    plugins: [
      rollupResolve(),
      rollupBabel({babelHelpers: 'bundled'}),
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
      rollupBabel({babelHelpers: 'bundled'}),
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
    'static/css/',
    'static/dist',
    'static/js/',
  ], {dot: true});
});


// Build production files, the default task
gulp.task('default', gulp.series(
  'clean',
  'styles',
  'css',
  'js',
  'lint-fix',
  'rollup',
  'rollup-cjs',
));

// Build production files, the default task
gulp.task('watch', gulp.series(
  'default',
  function watch() {
    gulp.watch(['client-src/sass/**/*.scss'], gulp.series('styles'));
    gulp.watch([
      'client-src/js-src/**/*.js',
      'client-src/elements/*.js',
      'client-src/contexts/*.js',
    ], gulp.series(['lint', 'js']));
    gulp.watch([
      'client-src/components.js',
      'client-src/elements/*.js',
      'client-src/contexts/*.js',
    ], gulp.series(['rollup']));
  },
));
