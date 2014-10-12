_ = require 'underscore'
fs = require 'fs'
filewalker = require 'filewalker'
exec = require('child_process').exec
livereload = require 'connect-livereload'
connect = require 'connect'
project = require './settings'
{apply, series, each, map} = require 'async'

latest = { version: 'latest', branch: 'master' }


livereloadPort = 35729
watchFiles = [
  'templates/**'
  'static/**'
  'cosmic-bootstrap/less/**'
  'sphinx-bootstrap/**'
  'sphinx-boot.coffee'
  'inject.coffee'
  'package.json'
]

listFiles = (dir, callback) ->
  files = []
  walker = filewalker(dir)
  walker.on 'dir',  (rel, stat, abs) ->
    files.push "#{dir}/#{rel}"
  walker.on 'file', (rel, stat, abs) ->
    if not /pyc$/.test rel
      files.push "#{dir}/#{rel}"
  walker.on 'error', (err) ->
    callback err, null
  walker.on 'done', ->
    # Don't look at changes inside .tox
    files = _.reject files, (name) -> /\.tox/.test name
    # Ignore git files too
    files = _.reject files, (name) -> /\.git/.test name
    callback null, files
  walker.walk()

parallelListFiles = (dirs, callback) ->
  map dirs, listFiles, (err, results) ->
    if err
      callback err, null
    callback null, _.zip dirs, results

writeMakefile = (callback) ->
  generateMakefile (err, text) -> 
    fs.writeFile 'Makefile', text, (err) ->
      callback err

module.exports = (grunt) ->

  grunt.initConfig
    pkg: grunt.file.readJSON 'package.json'
    exec:
      makeAll:
        command: 'make dist'
    watch:
      main:
        options:
          livereload: livereloadPort
          nospawn: true
        files: watchFiles
        tasks: ['configure', 'exec:makeMain']
      docs:
        options:
          livereload: livereloadPort
          nospawn: true
        files: watchFiles
        tasks: ['configure', 'exec:makeDocs']

  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-exec'

  grunt.registerTask 'default', ['configure', 'exec:makeAll']

  grunt.registerTask 'configure', 'Write Makefile.', ->
    done = @async()
    writeMakefile (err) ->
      if err
        done err
      done()

  grunt.registerTask 'connect', 'Start a static web server.', ->
    connect()
      .use(livereload({port: livereloadPort}))
      .use(connect.static 'dist')
      .listen 9001

  grunt.registerTask 'init', 'Set up environment.', ->
    series [
      apply exec, 'git clone -b cosmic git@github.com:cosmic-api/bootstrap.git cosmic-bootstrap'
      apply exec, 'git clone git@github.com:cosmic-api/flask-sphinx-themes.git'
      apply exec, 'git clone git@github.com:cosmic-api/teleport.py.git teleport-py'
    ], @async()

  grunt.registerTask 'deploy', 'Deploy to GitHub pages.', ->
    # Pull, add, commit and push
    exec """
         cd dist; \
         git checkout master; \
         git pull origin master; \
         git add -A; \
         git commit -m "Regenerated"; \
         git push origin master
         """, @async()

  grunt.registerTask 'clean', 'Remove all but the source files.', ->
    series [
      apply exec, 'rm -rf build/*'
      apply exec, 'rm -rf dist/*'
      apply exec, 'rm -rf tmp/*'
      apply exec, 'rm -rf cosmic-bootstrap/dist'
      apply exec, 'cd teleport-py/docs; make clean'
    ], @async()

  grunt.registerTask 'live', ['configure', 'exec:makeAll', 'connect', 'watch']
  grunt.registerTask 'live-main', ['configure', 'exec:makeMain', 'connect', 'watch:main']

generateMakefile = (callback) ->

  # Executables
  coffeeExec = "node_modules/.bin/coffee"
  jadeExec = "node_modules/.bin/jade"
  # Stuff necessary for injector
  injector = "inject.coffee settings.coffee node_modules templates"

  # Wildcard directories will be touched if their children are modified
  touchy = [
    "cosmic-bootstrap/less"
    "teleport-py"
    "teleport-py/docs/source"
  ]

  tmpdir = "tmp"

  makefile = """

  # Reinstall stuff if package.json is modified

  node_modules: package.json
  \tnpm install
  \ttouch node_modules
  cosmic-bootstrap/node_modules: cosmic-bootstrap/package.json
  \t(cd cosmic-bootstrap; npm install)
  \ttouch cosmic-bootstrap/node_modules

  # Cosmic Bootstrap

  cosmic-bootstrap/dist: cosmic-bootstrap/less
  \t(cd cosmic-bootstrap; npm install; node_modules/.bin/grunt dist)

  """

  extractRef = (projectDir, branch, fullname) ->
    """
    #{projectDir}/.git/refs/heads/#{branch} :
    \tgit --git-dir #{projectDir}/.git fetch origin #{branch}:#{branch}

    build/#{fullname}: #{projectDir}/.git/refs/heads/#{branch}
    \trm -rf build/#{fullname}
    \tmkdir -p build/#{fullname}
    \tgit --git-dir #{projectDir}/.git archive #{branch} | tar x -C build/#{fullname}


    """


  makePythonSphinx = (fullname) ->
    t = "tmp/#{fullname}.sphinx"
    """
    build/#{fullname}.sphinx.tar: build/#{fullname} build/#{fullname}.tox.tar
    \trm -rf #{t}
    \tcp -R build/#{fullname} #{t}
    \tmkdir #{t}/.tox
    \ttar xf build/#{fullname}.tox.tar -C #{t}/.tox
    \techo '\\nhtml_theme_path = ["../../../../flask-sphinx-themes"]\\n' >> #{t}/docs/source/conf.py
    \t(. #{t}/.tox/py27/bin/activate; sphinx-build -b html -D html_theme=flask #{t}/docs/source #{t}/out)
    \ttar cf build/#{fullname}.sphinx.tar -C #{t}/out .


    """


  makeSpecSphinx = (fullname, githubUrl) ->
    t = "tmp/#{fullname}.sphinx"
    """
    build/#{fullname}.sphinx.tar: build/#{fullname} sphinx-bootstrap
    \trm -rf #{t}
    \tcp -R build/#{fullname} #{t}
    \techo '\\nhtml_theme_path = ["../../../sphinx-bootstrap"]\\n'   >> #{t}/source/conf.py
    \techo '\\nhtml_theme_options = {"github_url": "#{githubUrl}"}\\n' >> #{t}/source/conf.py
    \tmkdir #{t}/build
    \tsphinx-build -b html -D html_theme=bootstrap -D pygments_style=emacs #{t}/source #{t}/build
    \ttar cf build/#{fullname}.sphinx.tar -C #{t}/build .


    """


  injectNavbar = (archive, project, section, version, jquery) ->
    t = "tmp/#{archive}.inject"
    jqueryOpt = if jquery then '--jquery' else ''
    """
    build/#{archive}.inject.tar: build/#{archive}.tar #{injector}
    \trm -rf #{t}
    \tmkdir -p #{t}
    \ttar xf build/#{archive}.tar -C #{t}
    \t#{coffeeExec} inject.coffee --dir #{t} --project #{project} --section #{section} --version '#{version}' #{jqueryOpt}
    \ttar cf build/#{archive}.inject.tar -C #{t} .


    """


  checkoutDeps = []
  for {version, branch} in [latest].concat project.sections.python.checkouts
    fullname = "teleport-py-#{version}"

    makefile += extractRef "teleport-py", branch, fullname
    t = "tmp/#{fullname}.tox"
    makefile += """
      build/#{fullname}.tox.tar: build/#{fullname}
      \trm -rf #{t}
      \tcp -R build/#{fullname} #{t}
      \t(cd #{t}; tox -e py27 --notest)
      \ttar cf build/#{fullname}.tox.tar -C #{t}/.tox .


      """
    makefile += makePythonSphinx fullname
    makefile += injectNavbar "#{fullname}.sphinx", 'teleport', "python", version
    checkoutDeps.push "build/#{fullname}.sphinx.inject.tar"

  makefile += """
  dist: #{checkoutDeps.join ' '} cosmic-bootstrap/dist static
  \tmkdir -p dist
  \tmkdir dist/python
  \trm -rf dist/index.html
  \ttouch dist/.nojekyll
  \tcp -R static dist
  \tcp -R cosmic-bootstrap/dist dist/static/bootstrap

  """

  for {version, ref} in [latest].concat project.sections.python.checkouts
    makefile += "\tmkdir dist/python/#{version}\n"
    makefile += "\ttar xf build/teleport-py-#{version}.sphinx.inject.tar -C dist/python/#{version}\n"

  parallelListFiles touchy, (err, results) ->
    if err
      callback err, null
    makefile += """

    # These directories will be touched if any of their files or
    # subdirectories (recursive) has been modified. This lets us use these
    # directories as wildcards


    """
    for [dir, files] in results
      makefile += """
      #{dir}: #{files.join ' '}
      \ttouch #{dir}

      """

    callback null, makefile
