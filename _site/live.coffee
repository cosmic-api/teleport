grunt = require 'grunt'

grunt.task.init = ->

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

argv = require('optimist').argv

if argv._[0] == 'site'
  grunt.tasks ['live:site'], {}
else if argv._[0] == 'py'
  grunt.tasks ['live:py'], {}

