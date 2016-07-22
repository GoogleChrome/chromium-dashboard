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

const $ = gulpLoadPlugins();

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

// Minify the vulcanized script files
gulp.task('scripts', () => {
  // The script files are overwritten (as they are generated anyways)
  //  - The 'base' option is needed to retain the relative path of each file,
  //    allow overwriting
  return gulp.src(
    'static/elements/*.vulcanize.js', {base: 'static'}
  )
    .pipe($.uglify())
    .pipe(gulp.dest('static'));
});

// Vulcanize the Polymer imports, creating *.vulcanize.* files beside the
// original import files.
gulp.task('vulcanize', () => {
  return gulp.src([
      'static/elements/metrics-imports.html',
      'static/elements/features-imports.html',
      'static/elements/admin-imports.html',
      'static/elements/samples-imports.html',
    ], {base: 'static'}
  )
    // Vulcanize does not allow the name of the output file to be specified, so
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
      scriptInHead: true
    }))
    .pipe(gulp.dest('static'));
});

// Clean generated files
gulp.task('clean', () => {
  del([
    'static/css',
    'static/dist',
    'static/elements/*.vulcanize.{html,js}'
    ], {dot: true});
});

// Build production files, the default task
gulp.task('default', ['clean'], cb =>
  runSequence(
    'styles',
    'lint',
    'vulcanize',
    'scripts',
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
