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
      apply exec, 'git clone git@github.com:cosmic-api/flask-sphinx-themes.git'
      apply exec, 'git clone git@github.com:cosmic-api/teleport.py.git teleport-py'
      apply exec, 'git clone git@github.com:cosmic-api/teleport.git teleport'
    ], @async()

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
      apply exec, 'cd teleport-py/docs; make clean'
    ], @async()

  grunt.registerTask 'live', ['configure', 'exec:makeAll', 'connect', 'watch']
  grunt.registerTask 'live-main', ['configure', 'exec:makeMain', 'connect', 'watch:main']

generateMakefile = (callback) ->

  # Executables
  coffeeExec = "node_modules/.bin/coffee"
  # Stuff necessary for injector
  injector = "inject.coffee settings.coffee node_modules templates"

  # Wildcard directories will be touched if their children are modified
  touchy = [
    "teleport-py"
    "teleport-py/docs/source"
    "templates"
  ]

  tmpdir = "tmp"

  makefile = """

  # Reinstall stuff if package.json is modified

  node_modules: package.json
  \tnpm install
  \ttouch node_modules

  # Bootstrap

  build/bootstrap-lumen.css:
  \t(cd build && wget http://bootswatch.com/lumen/bootstrap.css && mv bootstrap.css bootstrap-lumen.css)

  build/bootstrap-3.3.0-dist.zip:
  \t(cd build && wget https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip)

  build/bootstrap.tar: build/bootstrap-lumen.css build/bootstrap-3.3.0-dist.zip
  \trm -rf tmp/bootstrap
  \tunzip build/bootstrap-3.3.0-dist.zip -d tmp
  \tmv tmp/dist tmp/bootstrap
  \tnamespace-css build/bootstrap-lumen.css -s .bs -o tmp/bootstrap/css/bootstrap.css
  \tsed -i 's/\\.bs\\ body/\\.bs/g' tmp/bootstrap/css/bootstrap.css
  \tcp tmp/bootstrap/css/bootstrap.css tmp/bootstrap/css/bootstrap.min.css
  \ttar cf build/bootstrap.tar -C tmp/bootstrap .

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


  injectNavbar = (archive, project, section, version, jquery) ->
    t = "tmp/#{archive}.inject"
    jqueryOpt = if jquery then '--jquery' else ''
    """
    build/#{archive}.inject.tar: build/#{archive}.tar #{injector}
    \trm -rf #{t}
    \tmkdir -p #{t}
    \ttar xf build/#{archive}.tar -C #{t}
    \t#{coffeeExec} inject.coffee --dir #{t} --section #{section} --version '#{version}' #{jqueryOpt}
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

  # Old teleport spec
  fullname = "teleport-spec-1.0"
  makefile += """
    build/#{fullname}.tar:
    \ttar cf build/#{fullname}.tar -C teleport-spec-1.0 .


    """
  makefile += injectNavbar "#{fullname}", "teleport", "spec", "1.0"
  checkoutDeps.push "build/#{fullname}.inject.tar"


  makefile += """
  dist: #{checkoutDeps.join ' '} static index.coffee build/bootstrap.tar #{injector}
  \trm -rf dist
  \tmkdir -p dist

  \tmkdir dist/python
  \tmkdir dist/spec
  \ttouch dist/.nojekyll
  \tcp -R static dist
  \trm -rf dist/static/bootstrap
  \tmkdir -p dist/static/bootstrap
  \ttar xf build/bootstrap.tar -C dist/static/bootstrap
  \t#{coffeeExec} index.coffee > dist/index.html
  \t#{coffeeExec} inject.coffee --file dist/index.html --section home

  \t# Old Teleport spec
  \tmkdir dist/spec/1.0
  \ttar xf build/teleport-spec-1.0.inject.tar -C dist/spec/1.0


  """

  for {version, ref} in [latest].concat project.sections.python.checkouts
    makefile += "\tmkdir dist/python/#{version}\n"
    makefile += "\ttar xf build/teleport-py-#{version}.sphinx.inject.tar -C dist/python/#{version}\n"

  """
  for {version, ref} in [latest].concat project.sections.spec.checkouts
    makefile += "\tmkdir dist/spec/#{version}\n"
    makefile += "\ttar xf build/teleport-spec-#{version}.sphinx.inject.tar -C dist/spec/#{version}\n"
  """

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

