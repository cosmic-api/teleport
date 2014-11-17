_ = require 'underscore'
fs = require 'fs'

# Executables
coffeeExec = "node_modules/.bin/coffee"
bin = "node_modules/.bin"

obnoxygen = require 'obnoxygen'
{ Makefile, commandsFromLines, BaseRule, File, TarFile } = require 'obnoxygen'


class FileTouch extends obnoxygen.BaseRule
  # For example, when the index template changes, index.coffee should be
  # considered changed too

  constructor: (touchThis, whenThisChanges) ->
    @forceLeaf = true
    super
      filename: touchThis
      deps: whenThisChanges
      commands: ["touch #{touchThis}"]


class CopiedFromArchive extends obnoxygen.File

  constructor: (name) ->
    source = "_site/archive/#{name}.tar"
    super
      archive: "archive-#{name}"
      deps: [source]
      commands: ["cp -R #{source} build/archive-#{name}.tar"]


class CurrentSource extends obnoxygen.File

  constructor: ->
    super
      archive: "current-source"
      commands: commandsFromLines """
        git ls-files -o -i --exclude-standard > tmp/excludes
        rm -f build/current-source.tar
        # We are excluding build/current-source.tar so tar doesn't complain about recursion
        tar cf build/current-source.tar --exclude build/current-source.tar --exclude-from=tmp/excludes .
      """

class NewSpec extends obnoxygen.TarFile

  constructor: (source) ->
    super
      archive: "#{source}-xml2rfc"
      deps: ["_site/spec.coffee"]
      mounts:
        '/': source
      resultDir: '/out'
      getLines: (tmp) -> """
        (cd #{tmp}/_spec; xml2rfc teleport.xml --text)
        mkdir #{tmp}/out
        #{coffeeExec} _site/spec.coffee < #{tmp}/_spec/teleport.txt > #{tmp}/out/index.html
      """


class PythonDocs extends obnoxygen.TarFile

  constructor: (source) ->
    super
      archive: "#{source}-sphinx"
      resultDir: '/python/out'
      deps: ["build/flask-sphinx-themes.tar"]
      mounts:
        '/': source
      getLines: (tmp) -> """
        mkdir #{tmp}/python/flask-sphinx-themes
        tar xf build/flask-sphinx-themes.tar -C #{tmp}/python/flask-sphinx-themes
        echo '\\nhtml_theme_path = ["../../flask-sphinx-themes"]\\n' >> #{tmp}/python/docs/source/conf.py
        echo '\\nimport os, sys; sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))\\n' >> #{tmp}/python/docs/source/conf.py
        (cd #{tmp}/python; sphinx-build -b html -D html_theme=flask docs/source out)
      """


class InjectedFile extends obnoxygen.TarFile

  constructor: (source, args) ->
    super
      archive: "#{source}-inject"
      deps: ["_site/inject.coffee"]
      mounts:
        '/': source
      getLines: (tmp) -> """
        find #{tmp} -iname \\*.html | xargs #{coffeeExec} _site/inject.coffee #{args}
      """

class DownloadedZip extends obnoxygen.TarFile

  constructor: (archive, url) ->
    super
      archive: archive
      resultDir: '/out'
      getLines: (tmp) -> """
        wget #{url} -O #{tmp}/src-#{archive}.zip
        mkdir #{tmp}/out
        unzip #{tmp}/src-#{archive}.zip -d #{tmp}/out
      """


makefile = new Makefile()
makefile.addTask "deploy", """
  (cd tmp/site-inject \
  && rsync -avz \
  -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
  --progress . root@104.131.5.252:/root/teleport-json.org)
"""
makefile.addTask "clean", "rm -rf build/*", "rm -rf tmp/*"
makefile.addRules [

  new BaseRule
    filename: 'node_modules'
    deps: ["package.json"]
    commands: ['npm install', 'touch node_modules']

  downloadLumen = new obnoxygen.FileDownload 'bootstrap-lumen.css', 'http://bootswatch.com/lumen/bootstrap.css'

  flaskSphinxThemes = new obnoxygen.TarFromZip "flask-sphinx-themes", "https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip"
  bootstrapDist = new obnoxygen.TarFromZip "bootstrap-dist", "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip"

  fonts = new obnoxygen.GoogleFonts "http://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,700,400italic|Ubuntu+Mono:400,700"

  new FileTouch '_site/index.coffee', ['_site/templates/index.mustache']
  new FileTouch '_site/spec.coffee', ['_site/templates/spec.mustache']
  new FileTouch '_site/inject.coffee', ['_site/templates/navbar.mustache']

  npmHighlight = new obnoxygen.LocalNpmPackage 'highlight.js'
  npmJquery = new obnoxygen.LocalNpmPackage 'jquery'

  bootstrap = new TarFile
    archive: 'bootstrap'
    resultDir: '/dist'
    mounts:
      '/': bootstrapDist.archive
      '/fonts': fonts.archive
      '/lumen': downloadLumen.archive
      '/highlight': npmHighlight.archive
    deps: [
      '_site/static/static.css'
    ]
    getLines: (tmp) -> """
      # Concatenate CSS from multiple sources
      cp #{tmp}/lumen/bootstrap-lumen.css #{tmp}/everything.css
      cat #{tmp}/highlight/styles/tomorrow.css >> #{tmp}/everything.css
      cat _site/static/static.css >> #{tmp}/everything.css
      # Make the css safe to mix with other css
      namespace-css #{tmp}/everything.css -s .bs >> #{tmp}/everything-safe.css
      sed -i 's/\\.bs\\ body/\\.bs,\\ \\.bs\\ body/g' #{tmp}/everything-safe.css
      # Remove google font API loads
      sed -i '/googleapis/d' #{tmp}/everything-safe.css
      rm -r #{tmp}/dist/css/*
      # Fonts get prepended
      cp #{tmp}/fonts/index.css #{tmp}/dist/css/bootstrap.css
      cat #{tmp}/everything-safe.css >> #{tmp}/dist/css/bootstrap.css
      #{bin}/cleancss #{tmp}/dist/css/bootstrap.css > #{tmp}/dist/css/bootstrap.min.css
      # Copy fonts
      mkdir -p #{tmp}/dist/fonts
      cp #{tmp}/fonts/*.ttf #{tmp}/dist/fonts
    """

  master = new obnoxygen.GitCheckoutBranch 'master'
  py01m = new obnoxygen.GitCheckoutBranch 'py-0.1-maintenance'
  py02m = new obnoxygen.GitCheckoutBranch 'py-0.2-maintenance'
  draft00 = new obnoxygen.GitCheckoutTag 'spec-draft-00'
  oldSpec = new CopiedFromArchive 'spec-old'
  currentSource = new CurrentSource()
  specLatest = new NewSpec master.archive
  specDraft00 = new NewSpec draft00.archive
  sphinxLatest = new PythonDocs master.archive
  sphinx01 = new PythonDocs py01m.archive
  sphinx02 = new PythonDocs py02m.archive
  liveSphinx = new PythonDocs currentSource.archive

  injectPyLatest = new InjectedFile sphinxLatest.archive, "--navbar python/latest --bs"
  injectPy02 = new InjectedFile sphinx02.archive, "--navbar 'python/0.2' --bs"
  injectPy01 = new InjectedFile sphinx01.archive, "--navbar 'python/0.1' --bs"
  specLatest = new InjectedFile specLatest.archive, "--navbar 'spec/latest' --bs"
  spacDraft00 = new InjectedFile specDraft00.archive, "--navbar 'spec/draft-00' --bs"
  spec10 = new InjectedFile oldSpec.archive, "--navbar 'spec/1.0' --bs"

  site = new TarFile
    archive: "site"
    deps: [
      "_site/static"
      "_site/index.coffee"
    ]
    mounts:
      '/static/bootstrap': 'bootstrap'
      '/python/latest': injectPyLatest.archive
      '/python/0.2': injectPy02.archive
      '/python/0.1': injectPy01.archive
      '/spec/latest': specLatest.archive
      '/spec/draft-00': spacDraft00.archive
      '/spec/1.0': spec10.archive
      '/npm-jquery': npmJquery.archive
    getLines: (tmp) -> """
      cp -R _site/static #{tmp}
      cp #{tmp}/npm-jquery/dist/jquery* #{tmp}/static
      rm -rf #{tmp}/npm-jquery

      #{coffeeExec} _site/index.coffee > #{tmp}/index.html
      #{coffeeExec} _site/inject.coffee #{tmp}/index.html --navbar '/' --bs --highlight
    """

  deploySite = new InjectedFile site.archive, "--analytics"
]

main = ->
  fs.writeFileSync "#{__dirname}/../Makefile", makefile.toString()


if require.main == module
  main()


module.exports =
  makefile: makefile
  writeMakefileSync: main