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
  'inject.coffee'
  'package.json'
  '../_spec/teleport.txt'
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
      options:
        livereload: livereloadPort
        nospawn: true
      files: watchFiles
      tasks: ['configure', 'exec:makeAll']

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

  grunt.registerTask 'live', ['configure', 'exec:makeAll', 'connect', 'watch']

generateMakefile = (callback) ->

  # Executables
  coffeeExec = "node_modules/.bin/coffee"
  # Stuff necessary for injector
  injector = "inject.coffee settings.coffee node_modules templates"

  # Wildcard directories will be touched if their children are modified
  touchy = [
    "../python"
    "../python/docs/source"
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

  # Flask-style Python Docs

  build/flask-sphinx-themes.tar:
  \twget https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip -O tmp/flask-sphinx-themes.zip
  \trm -rf tmp/flask-sphinx-themes-master
  \t(cd tmp; unzip flask-sphinx-themes.zip)
  \ttar cf build/flask-sphinx-themes.tar -C tmp/flask-sphinx-themes-master .

  # New Teleport spec
  build/spec-new.tar: ../_spec/teleport.txt spec.coffee
  \trm -rf tmp/spec-new
  \tmkdir tmp/spec-new
  \t#{coffeeExec} spec.coffee > tmp/spec-new/index.html
  \ttar cf build/spec-new.tar -C tmp/spec-new .


  """

  makefile += "# Copying from archive\n\n"
  for arch in project.archive
    makefile += """
    build/archive-#{arch}.tar: archive/#{arch}.tar
    \tcp archive/#{arch}.tar build/archive-#{arch}.tar


    """

  makefile += "# Checkouts\n\n"
  for branch in project.checkouts
    buildTar = "build/checkouts-#{branch}.tar"
    makefile += """
    #{buildTar}: ../.git/refs/heads/#{branch}
    \trm -f #{buildTar}
    \tgit --git-dir ../.git archive #{branch} > #{buildTar}


    """

  makefile += "# Subdirectory extraction\n\n"
  for root, subs of project.subdirs
    for sub in subs
      full = "#{root}-#{sub}"
      t = "tmp/#{full}"
      makefile += """
      build/#{full}.tar: build/#{root}.tar
      \trm -rf #{t}
      \tmkdir #{t}
      \ttar xf build/#{root}.tar -C #{t}
      \ttar cf build/#{full}.tar -C #{t}/#{sub} .


      """

  makefile += "# Build Sphinxes\n\n"
  for root in project.sphinx
    full = "#{root}-sphinx"
    t = "tmp/#{full}"
    makefile += """
    build/#{full}.tar: build/#{root}.tar build/flask-sphinx-themes.tar
    \trm -rf #{t}
    \tmkdir #{t}
    \ttar xf build/#{root}.tar -C #{t}
    \tmkdir #{t}/flask-sphinx-themes
    \ttar xf build/flask-sphinx-themes.tar -C #{t}/flask-sphinx-themes
    \techo '\\nhtml_theme_path = ["../../flask-sphinx-themes"]\\n' >> #{t}/docs/source/conf.py
    \techo '\\nimport os, sys; sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))\\n' >> #{t}/docs/source/conf.py
    \t(cd #{t}; sphinx-build -b html -D html_theme=flask docs/source out)
    \ttar cf build/#{full}.tar -C #{t}/out .


    """

  checkoutDeps = ["build/spec-new.tar"]
  makefile += "# Injecting\n\n"
  for section, vers of project.layout
    for version, {content, jquery, nobs} of vers
      full = "#{content}-inject"
      t = "tmp/#{full}"
      jqueryOpt = if jquery then '--jquery' else ''
      nobsOpt = if nobs then '--nobs' else ''
      makefile += """
      build/#{full}.tar: build/#{content}.tar #{injector}
      \trm -rf #{t}
      \tmkdir -p #{t}
      \ttar xf build/#{content}.tar -C #{t}
      \t#{coffeeExec} inject.coffee --dir #{t} --section #{section} --version '#{version}' #{jqueryOpt} #{nobsOpt}
      \ttar cf build/#{full}.tar -C #{t} .


      """
      checkoutDeps.push "build/#{full}.tar"


  makefile += """
  dist: #{checkoutDeps.join ' '} static index.coffee build/bootstrap.tar #{injector}
  \trm -rf dist
  \tmkdir -p dist

  \ttouch dist/.nojekyll
  \tcp -R static dist
  \trm -rf dist/static/bootstrap
  \tmkdir -p dist/static/bootstrap
  \ttar xf build/bootstrap.tar -C dist/static/bootstrap

  \t#{coffeeExec} index.coffee > dist/index.html
  \t#{coffeeExec} inject.coffee --file dist/index.html --section home --nobs

  """

  for section, vers of project.layout
    makefile += """
    \tmkdir dist/#{section}

    """
    for version, {content, jquery} of vers
      makefile += """
      \tmkdir dist/#{section}/#{version}
      \ttar xf build/#{content}-inject.tar -C dist/#{section}/#{version}

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

