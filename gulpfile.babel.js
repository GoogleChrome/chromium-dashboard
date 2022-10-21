'use strict';

import gulp from 'gulp';
import babel from 'gulp-babel';
import nodeSass from 'node-sass';
import gulpSass from 'gulp-sass';
const sass = gulpSass( nodeSass );
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
import rollupBabel from '@rollup/plugin-node-resolve';
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

gulp.task('lint', () => {
  return gulp.src([
    'client-src/js-src/*.js',
    'client-src/elements/*.js',
  ])
    .pipe(eslint())
    .pipe(eslint.format())
    .pipe(eslint.failAfterError());
});

gulp.task('lint-fix', () => {
  return gulp.src([
    'client-src/js-src/*.js',
    'client-src/elements/*.js',
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
    input: 'client-src/components.js',
    plugins: [
      rollupResolve(),
      rollupBabel({
        plugins: ["@babel/plugin-syntax-dynamic-import"]
      }),
      rollupMinify({mangle: false, comments: false}),
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
    'client-src/js-src/**/*.js',
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
));

// Build production files, the default task
gulp.task('watch', gulp.series(
  'default',
  function watch() {
    gulp.watch(['client-src/sass/**/*.scss'], gulp.series('styles'));
    gulp.watch(['client-src/js-src/**/*.js', 'client-src/elements/*.js'], gulp.series(['lint', 'js']));
    gulp.watch(['client-src/components.js', 'client-src/elements/*.js'], gulp.series(['rollup']));
  }
));
