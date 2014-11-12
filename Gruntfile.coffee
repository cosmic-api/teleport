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
      configure:
        command: './configure'
      makeSite:
        command: 'make build/site.tar'
    watch:
      site:
        options:
          spawn: false
        files: [
          '_site/templates/**'
          '_site/static/**'
          '_site/inject.coffee'
          '_spec/teleport.txt'
          'package.json'
        ]
        tasks: ['configure', 'exec:makeSite']

  grunt.registerTask 'connect', 'Start a static web server.', ->
    connect()
      .use(livereload({port: livereloadPort}))
      .use(serve 'tmp/site')
      .listen 9001

  grunt.registerTask 'live:site', ['exec:configure', 'exec:makeSite', 'connect', 'watch:site']

