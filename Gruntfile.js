module.exports = function(grunt) {

  grunt.initConfig({
    // pkg: grunt.file.readJSON('package.json'),

    vulcanize: {
      options: {
        // excludes: {
        //   imports: [
        //     "polymer.html$"
        //   ]
        // },
        stripComments: true,
        inlineScripts: true,
        inlineCss: true
      },
      buildall: {
        options: {
          csp: 'elements.vulcanize.js'
        },
        files: {
          'static/elements/elements.vulcanize.html': 'static/elements/elements.html'
        },
      },
      build1: {
        options: {
          csp: 'metrics-imports.vulcanize.js'
        },
        files: {
          'static/elements/metrics-imports.vulcanize.html': 'static/elements/metrics-imports.html'
        }
      },
      build2: {
        options: {
          csp: 'features-imports.vulcanize.js'
        },
        files: {
          'static/elements/features-imports.vulcanize.html': 'static/elements/features-imports.html'
        }
      },
      build3: {
        options: {
          csp: 'admin-imports.vulcanize.js'
        },
        files: {
          'static/elements/admin-imports.vulcanize.html': 'static/elements/admin-imports.html'
        }
      }
    },

    minified : {
      files: {
        src: [
          'static/elements/*.vulcanize.js'
        ],
        dest: 'static'
      },
      options : {
        sourcemap: false,
        mirrorSource: {
          path: 'static/'
        },
        ext: '.js'
      }
    },

    compass: {
      dist: {
        options: {
          config: 'config.rb'
        }
      }
    },

    clean: {
      default: ['static/elements/*.vulcanize.{html,js}']
    },

    watch: {
      elements: {
        files: ['components/*.html'],
        tasks: ['vulcanize'],
        options: {
          spawn: false,
        },
      },
    },

    appengine: {
      options: {
        manageFlags: {
          oauth2: true
        },
        runFlags: {
          port: 8080
        }
      },
      frontend: {
        root: '.'
      }
      // backend: {
      //   root: '.',
      //   backend: true,
      // }
    }

  });

  // Plugin and grunt tasks.
  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', ['compass', 'vulcanize', 'minified']);
  grunt.registerTask('serve', ['appengine:run:frontend']);
};
