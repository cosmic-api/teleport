{makefile} = require './configure'


module.exports = (grunt) ->

  grunt.loadNpmTasks 'grunt-exec'
  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-contrib-connect'

  grunt.initConfig
    pkg: grunt.file.readJSON 'package.json'
    exec:
      configure:
        command: './configure'
      makeSite:
        command: 'make build/site.tar'
      makePy:
        command: 'make build/current-source-sphinx.tar'
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
        tasks: ['exec:configure', 'exec:makeSite']
      py:
        options:
          spawn: false
        files: [
          'python/teleport/**'
          'python/docs/source/**'
          'package.json'
        ]
        tasks: ['exec:configure', 'exec:makePy']
    connect:
      site:
        options:
          base: 'tmp/site'
          livereload: true
      py:
        options:
          base: 'tmp/current-source-sphinx'
          livereload: true


  grunt.registerTask 'live:site', [
    'exec:configure'
    'exec:makeSite'
    'connect:site'
    'watch:site'
  ]

  grunt.registerTask 'live:py', [
    'exec:configure'
    'exec:makePy'
    'connect:py'
    'watch:py'
  ]

