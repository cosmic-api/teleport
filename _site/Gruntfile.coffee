_ = require 'underscore'
fs = require 'fs'
livereload = require 'connect-livereload'
connect = require 'connect'
serve = require 'serve-static'

{makefile} = require './configure'

livereloadPort = 35729


module.exports = (grunt) ->

  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-exec'

  grunt.initConfig
    pkg: grunt.file.readJSON 'package.json'
    exec:
      site:
        command: 'make build/site.tar'
    watch:
      site:
        options:
          spawn: false
        files: [
          'templates/**'
          'static/**'
          'inject.coffee'
          'package.json'
          '../_spec/teleport.txt'
        ]
        tasks: ['configure', 'exec:site']

  grunt.registerTask 'live:site', ['configure', 'exec:site', 'connect', 'watch:site']

  grunt.registerTask 'default', ['configure', 'exec:site']

  grunt.registerTask 'configure', 'Write Makefile.', ->
    fs.writeFileSync 'Makefile', makefile

  grunt.registerTask 'connect', 'Start a static web server.', ->
    connect()
      .use(livereload({port: livereloadPort}))
      .use(serve 'tmp/site')
      .listen 9001
