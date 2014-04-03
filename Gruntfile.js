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
        strip: true,
        csp: false,
        inline: true
      },
      build: {
        files: {
          'static/elements/elements.vulcanize.html': 'static/elements/elements.html',
          'static/elements/features-imports.vulcanize.html': 'static/elements/features-imports.html',
          'static/elements/admin-imports.vulcanize.html': 'static/elements/admin-imports.html',
          'static/elements/metrics-imports.vulcanize.html': 'static/elements/metrics-imports.html',
        },
      }
    },

    watch: {
      elements: {
        files: ['components/*.html'],
        tasks: ['vulcanize'],
        options: {
          spawn: false,
        },
      },
    }

  });

  // Plugin and grunt tasks.
  require('load-grunt-tasks')(grunt);

  grunt.registerTask('default', ['vulcanize:build']);
};
