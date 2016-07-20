module.exports = function(grunt) {

  grunt.initConfig({
    // pkg: grunt.file.readJSON('package.json'),

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

  grunt.registerTask('serve', ['appengine:run:frontend']);
};
