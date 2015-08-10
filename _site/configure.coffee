_ = require 'underscore'
path = require 'path'
fs = require 'fs'

os = require 'os'

obnoxygen = require 'obnoxygen'
glob = require "glob"

# Executables
coffeeExec = "node_modules/.bin/coffee"
bin = "node_modules/.bin"



copyFromArchive = (name) ->
  source = "_site/archive/#{name}.tar"
  archive = "archive-#{name}"
  new obnoxygen.Rule
    archive: archive
    deps: [source]
    commands: ["cp -R #{source} #{obnoxygen.archiveFile archive}"]

pythonDocs = (version) ->
  obnoxygen.tarFile
    archive: "python-#{version}-sphinx"
    resultDir: '/python/out'
    deps: glob.sync "python/#{version}/docs/source/**"
      .concat glob.sync "python/#{version}/teleport/**"
      .concat glob.sync "python/CHANGES.rst"
    mounts:
      '/flask-sphinx-themes': obnoxygen.tarFromZip
        name: "flask-sphinx-themes"
        url: "https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip"
      '/intersphinx/python2': obnoxygen.fileDownload
        filename: 'python2.inv'
        url: 'https://docs.python.org/2.7/objects.inv'
    getCommands: (tmp) -> """
      cp -R python/#{version} #{tmp}/python
      cp #{tmp}/intersphinx/python2/python2.inv #{tmp}/python/docs/source
      echo '\\nhtml_theme_path = ["../../../flask-sphinx-themes/flask-sphinx-themes-master"]\\n' >> #{tmp}/python/docs/source/conf.py
      echo '\\nimport os, sys; sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))\\n' >> #{tmp}/python/docs/source/conf.py
      echo '\\nintersphinx_mapping = {"python": ("http://docs.python.org/2.7", "python2.inv")}\\n' >> #{tmp}/python/docs/source/conf.py
      (cd #{tmp}/python; sphinx-build -b html -D html_theme=flask docs/source out)
    """

formatSpec = (source) ->
  obnoxygen.tarFile
    archive: "#{source}-xml2rfc"
    deps: [
      "_site/spec.coffee"
      "_site/templates/spec.mustache"
      "_spec/#{source}.xml"
    ]
    resultDir: '/out'
    getCommands: (tmp) -> """
      xml2rfc _spec/#{source}.xml --text --out=#{tmp}/teleport.txt
      mkdir #{tmp}/out
      #{coffeeExec} _site/spec.coffee < #{tmp}/teleport.txt > #{tmp}/out/index.html
    """

inject = (options) ->
  {src, args} = options
  obnoxygen.tarFile
    archive: "#{src.archive}-inject"
    deps: [
      "_site/inject.coffee"
      "_site/templates/navbar.mustache"
    ]
    mounts:
      '/': src
    getCommands: (tmp) -> """
      find #{tmp} -iname \\*.html | xargs #{coffeeExec} _site/inject.coffee #{args}
    """


rootDir = path.join __dirname, ".."

makefile = new obnoxygen.Makefile rootDir

deployTmp = "#{os.tmpdir()}/oxg/dist"
makefile.addTask "deploy", """
  rm -rf #{deployTmp}
  mkdir -p #{deployTmp}
  tar xf .cache/site.tar -C #{deployTmp}
  touch .env
  sh -ac ' . ./.env; #{coffeeExec} _site/deploy.coffee -d #{deployTmp}'
"""
makefile.addTask "clean", "rm -rf build/*"

makefile.addRule new obnoxygen.Rule
  filename: 'node_modules'
  deps: ["package.json"]
  commands: ['npm install', 'touch node_modules']

bootstrap = obnoxygen.tarFile
  archive: 'bootstrap'
  resultDir: '/dist'
  mounts:
    '/': obnoxygen.tarFromZip
      name: "bootstrap-dist"
      url: "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip"
    '/fonts': obnoxygen.googleFonts "http://fonts.googleapis.com/css?family=Lato:400,700,400italic|Inconsolata:400,700"
    '/lumen': obnoxygen.fileDownload
      filename: 'bootstrap-lumen.css'
      url: 'http://bootswatch.com/flatly/bootstrap.css'
    '/highlight': obnoxygen.localNpmPackage 'highlight.js'
    '/awesome': obnoxygen.tarFromZip
      name: 'font-awesome'
      url: 'http://fortawesome.github.io/Font-Awesome/assets/font-awesome-4.4.0.zip'
  deps: [
    '_site/static/static.css'
  ]
  getCommands: (tmp) -> """
    # Concatenate CSS from multiple sources
    cp #{tmp}/lumen/bootstrap-lumen.css #{tmp}/everything.css
    cat #{tmp}/highlight/styles/default.css >> #{tmp}/everything.css
    cat _site/static/static.css >> #{tmp}/everything.css
    # Make the css safe to mix with other css
    #{bin}/namespace-css #{tmp}/everything.css -s .bs >> #{tmp}/everything-safe.css
    sed -i 's/\\.bs\\ body/\\.bs,\\ \\.bs\\ body/g' #{tmp}/everything-safe.css
    # Remove google font API loads
    sed -i '/googleapis/d' #{tmp}/everything-safe.css
    rm -r #{tmp}/dist/css/*
    # Fonts get prepended
    cp #{tmp}/fonts/index.css #{tmp}/dist/css/bootstrap.css
    cat #{tmp}/everything-safe.css >> #{tmp}/dist/css/bootstrap.css
    cat #{tmp}/awesome/font-awesome-4.4.0/css/font-awesome.css >> #{tmp}/dist/css/bootstrap.css
    #{bin}/cleancss #{tmp}/dist/css/bootstrap.css > #{tmp}/dist/css/bootstrap.min.css
    # Copy fonts
    mkdir -p #{tmp}/dist/fonts
    cp #{tmp}/fonts/*.ttf #{tmp}/dist/fonts
    cp #{tmp}/awesome/font-awesome-4.4.0/fonts/* #{tmp}/dist/fonts
  """


master = obnoxygen.gitCheckoutBranch 'master'

site = obnoxygen.tarFile
  archive: "site"
  deps: [
    "_site/static"
    "_site/index.coffee"
    "_site/templates/index.mustache"
    "_site/inject.coffee"
    "_site/templates/navbar.mustache"
  ]
  mounts:
    '/static/bootstrap': bootstrap
    '/python/0.4': inject
      src: pythonDocs '0.4'
      args: "--navbar 'python/0.4' --bs"
    '/python/0.2': inject
      src: pythonDocs '0.2'
      args: "--navbar 'python/0.2' --bs"
    '/spec/draft-00': inject
      src: formatSpec 'draft-00'
      args: "--navbar 'spec/draft-00' --bs"
    '/spec/draft-01': inject
      src: formatSpec 'draft-01'
      args: "--navbar 'spec/draft-01' --bs"
    '/spec/draft-02': inject
      src: formatSpec 'draft-02'
      args: "--navbar 'spec/draft-02' --bs"
    '/spec/1.0': inject
      src: copyFromArchive 'spec-old'
      args: "--navbar 'spec/1.0' --bs"
    '/npm-jquery': obnoxygen.localNpmPackage 'jquery'
  getCommands: (tmp) -> """
    cp -R _site/static #{tmp}
    cp #{tmp}/npm-jquery/dist/jquery* #{tmp}/static
    rm -rf #{tmp}/npm-jquery

    #{coffeeExec} _site/index.coffee > #{tmp}/index.html
    #{coffeeExec} _site/inject.coffee #{tmp}/index.html --navbar '/' --bs --highlight
  """

makefile.addRule site
makefile.addRule inject
  src: site
  args: "--analytics"


if require.main == module
  fs.writeFileSync "#{__dirname}/../Makefile", makefile.toString()


runDemo = ->
  obnoxygen.demo.runDemoServer
    rootDir: "."
    makefile: makefile
    callback: (err, server) ->

module.exports =
  makefile: makefile
  runDemo: runDemo



