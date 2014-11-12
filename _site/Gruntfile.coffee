_ = require 'underscore'
fs = require 'fs'
exec = require('child_process').exec
livereload = require 'connect-livereload'
connect = require 'connect'
serve = require 'serve-static'

{apply, series, each, map} = require 'async'

latest = { version: 'latest', branch: 'master' }

{makefile} = require './configure'

livereloadPort = 35729


module.exports = (grunt) ->

  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-exec'

  grunt.initConfig
    pkg: grunt.file.readJSON 'package.json'
    exec:
      site:
        command: 'make build/dist.tar'
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
      .use(serve 'tmp/dist')
      .listen 9001

  grunt.registerTask 'deploy', 'Deploy.', ->
    # Pull, add, commit and push
    exec """
         cd dist; \
         rsync -avz -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --progress . root@104.131.5.252:/root/teleport-json.org
         """, @async()

  grunt.registerTask 'clean', 'Remove all but the source files.', ->
    series [
      apply exec, 'rm -rf build/*'
      apply exec, 'rm -rf dist/*'
      apply exec, 'rm -rf tmp/*'
    ], @async()


