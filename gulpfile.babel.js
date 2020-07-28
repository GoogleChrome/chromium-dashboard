'use strict';

const path = require('path');
const gulp = require('gulp');
const babel = require("gulp-babel");
const del = require('del');
const uglifyEs = require('gulp-uglify-es');
const uglify = uglifyEs.default;
const gulpLoadPlugins = require('gulp-load-plugins');
const eslintIfFixed = require('gulp-eslint-if-fixed');
const $ = gulpLoadPlugins();
const rollup = require('rollup');
const rollupResolve = require('rollup-plugin-node-resolve');
const rollupLitCss = require('rollup-plugin-lit-css');
const rollupBabel = require('rollup-plugin-babel');
const rollupMinify = require('rollup-plugin-babel-minify');

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
    input: 'static/components.js',
    plugins: [
      rollupLitCss({include: []}),
      rollupResolve(),
      rollupBabel({
        plugins: ["@babel/plugin-syntax-dynamic-import"]
      }),
      rollupMinify({comments: false}),
    ],
  }).then(bundle => {
    return bundle.write({
      dir: 'static/dist',
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
    .pipe(babel()) // Defaults are in .babelrc
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


// Build production files, the default task
gulp.task('default', gulp.series(
  'clean',
  'styles',
  'js',
  'lint-fix',
  'rollup',
));

// Build production files, the default task
gulp.task('watch', gulp.series(
  'default',
  function watch() {
    gulp.watch(['static/sass/**/*.scss'], gulp.series('styles'));
    gulp.watch(['static/js-src/**/*.js', 'static/elements/*.js'], gulp.series(['lint', 'js']));
    gulp.watch(['static/components.js', 'static/elements/*.js'], gulp.series(['rollup']));
  }
));
