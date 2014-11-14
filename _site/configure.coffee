_ = require 'underscore'
fs = require 'fs'

# Executables
coffeeExec = "node_modules/.bin/coffee"
bin = "node_modules/.bin"


commandsFromLines = (lines) ->
  lines = (line.trim() for line in lines.split '\n')
  return _.filter lines, (line) -> line != ''


class Makefile

  constructor: ->
    @rules = []

  addRule: (rule) ->
    @rules.push rule

  addRules: (rules) ->
    for rule in rules
      @addRule rule

  getPhonies: ->
    (rule.name for rule in @rules when rule.target == null)

  toString: ->
    s = ".PHONY: #{@getPhonies().join(' ')}\n\n"
    for rule in @rules
      s += rule.toString() + "\n\n"
    return s


class BaseRule

  constructor: (opts) ->
    {@targetFile, @deps, @commands} = opts
    if not @deps?
      @deps = []

  toString: ->
    "#{@targetFile}: #{@deps.join(' ')}\n\t#{@commands.join('\n\t')}"


class Rule extends BaseRule

  constructor: (opts) ->
    {@target, deps, commands} = opts
    super
      targetFile: "build/#{@target}.tar"
      deps: deps
      commands: commands


class Phony extends BaseRule

  constructor: (@name, commands) ->
    @target = null
    super
      targetFile: @name
      commands: commands


class RulePrepareTar extends Rule

  constructor: (opts) ->
    {target, deps, resultDir, getLines, mounts} = opts
    tmp = "tmp/#{target}"

    mounts = [] if not mounts?
    resultDir = '/' if not resultDir?
    deps = [] if not deps?

    mountLines = []
    for root, source of mounts
      # Since we're mounting it, we must be dependent on it
      deps.push "build/#{source}.tar"
      mountLines.push "mkdir -p #{tmp}#{root}"
      mountLines.push "tar xf build/#{source}.tar -C #{tmp}#{root}"

    super
      target: target
      deps: deps
      commands: ["rm -rf #{tmp}", "mkdir #{tmp}"]
        .concat mountLines
        .concat(commandsFromLines getLines(tmp))
        .concat ["tar cf build/#{target}.tar -C #{tmp}#{resultDir} ."]


class RuleCopyFromArchive extends Rule

  constructor: (name) ->
    source = "_site/archive/#{name}.tar"
    super
      target: "archive-#{name}"
      deps: [source]
      commands: ["cp -R #{source} build/archive-#{name}.tar"]


class RuleCheckout extends Rule

  constructor: (name, refFile) ->
    super
      target: "checkouts-#{name}"
      deps: [refFile]
      commands: ["git --git-dir .git archive $(shell cat #{refFile}) > build/checkouts-#{name}.tar"]


class RuleCheckoutBranch extends RuleCheckout

  constructor: (branch) ->
    super branch, ".git/refs/heads/#{branch}"


class RuleCheckoutTag extends RuleCheckout

  constructor: (tag) ->
    super tag, ".git/refs/tags/#{tag}"


class RuleCurrentSource extends Rule

  constructor: ->
    super
      target: "current-source"
      commands: commandsFromLines """
        git ls-files -o -i --exclude-standard > tmp/excludes
        rm -f build/current-source.tar
        # We are excluding build/current-source.tar so tar doesn't complain about recursion
        tar cf build/current-source.tar --exclude build/current-source.tar --exclude-from=tmp/excludes .
      """

class RuleNewSpec extends RulePrepareTar

  constructor: (source) ->
    super
      target: "#{source}-xml2rfc"
      deps: ["_site/spec.coffee", "_site/templates/spec.mustache"]
      mounts:
        '/': source
      resultDir: '/out'
      getLines: (tmp) -> """
        (cd #{tmp}/_spec; xml2rfc teleport.xml --text)
        mkdir #{tmp}/out
        #{coffeeExec} _site/spec.coffee < #{tmp}/_spec/teleport.txt > #{tmp}/out/index.html
      """


class RuleSphinx extends RulePrepareTar

  constructor: (source) ->
    super
      target: "#{source}-sphinx"
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


class RuleInject extends RulePrepareTar

  constructor: (source, args) ->
    super
      target: "#{source}-inject"
      deps: [
        "_site/inject.coffee"
        "_site/settings.coffee"
        "_site/templates/navbar.mustache"
        "node_modules"
      ]
      mounts:
        '/': source
      getLines: (tmp) -> """
        find #{tmp} -iname \\*.html | xargs #{coffeeExec} _site/inject.coffee #{args}
      """

class RuleDownloadZip extends RulePrepareTar

  constructor: (target, url) ->
    super
      target: target
      resultDir: '/out'
      getLines: (tmp) -> """
        wget #{url} -O #{tmp}/src-#{target}.zip
        mkdir #{tmp}/out
        unzip #{tmp}/src-#{target}.zip -d #{tmp}/out
      """

class RuleDownloadFonts extends RulePrepareTar

  constructor: (googleUrl) ->
    super
      target: 'fonts'
      resultDir: '/out'
      getLines: (tmp) -> """
        wget -O #{tmp}/index.css "#{googleUrl}"
        cat #{tmp}/index.css | grep -o -e "http.*ttf" > #{tmp}/download.list
        (cd #{tmp} && xargs -i wget '{}' < download.list)
        mkdir #{tmp}/out
        cp #{tmp}/*.ttf #{tmp}/out
        sed 's/http.*\\/\\(.*\\.ttf\\)/\"..\\/fonts\\/\\1\"/g' < #{tmp}/index.css > #{tmp}/out/index.css
      """

class RuleDownload extends RulePrepareTar

  constructor: (filename, url) ->
    super
      target: "download-#{filename}"
      getLines: (tmp) -> """
        wget -O #{tmp}/#{filename} "#{url}"
      """


makefile = new Makefile()

makefile.addRules [
  new Phony "clean", ["rm -rf build/*", "rm -rf tmp/*"]
  new Phony "deploy", commandsFromLines """
      (cd tmp/site; rsync -avz -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --progress . root@104.131.5.252:/root/teleport-json.org)
    """
  new Phony 'site', ["#{coffeeExec} _site/live.coffee site"]
  new Phony 'py', ["#{coffeeExec} _site/live.coffee py"]

  new BaseRule
    targetFile: 'node_modules'
    deps: ["package.json"]
    commands: ['npm install']

  downloadLumen = new RuleDownload 'bootstrap-lumen.css', 'http://bootswatch.com/lumen/bootstrap.css'
  downloadTomorrow = new RuleDownload 'prettify-tomorrow.css', 'http://jmblog.github.io/color-themes-for-google-code-prettify/css/themes/tomorrow.css'

  flaskSphinxThemes = new RuleDownloadZip "flask-sphinx-themes", "https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip"
  bootstrapDist = new RuleDownloadZip "bootstrap-dist", "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip"

  fonts = new RuleDownloadFonts "http://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,700,400italic|Ubuntu+Mono:400,700"

  bootstrap = new RulePrepareTar
    target: 'bootstrap'
    resultDir: '/dist'
    mounts:
      '/': bootstrapDist.target
      '/dist/fonts': fonts.target
      '/lumen': downloadLumen.target
      '/tomorrow': downloadTomorrow.target
    getLines: (tmp) -> """
      namespace-css #{tmp}/lumen/bootstrap-lumen.css -s .bs -o #{tmp}/dist/css/bootstrap.css
      namespace-css #{tmp}/tomorrow/prettify-tomorrow.css -s .bs >> #{tmp}/dist/css/bootstrap.css
      sed -i 's/\\.bs\\ body/\\.bs/g' #{tmp}/dist/css/bootstrap.css
      sed -i '/googleapis/d' #{tmp}/dist/css/bootstrap.css
      echo "" >> #{tmp}/dist/css/bootstrap.css
      cat #{tmp}/dist/fonts/index.css >> #{tmp}/dist/css/bootstrap.css
      rm #{tmp}/dist/fonts/index.css
      #{bin}/cleancss #{tmp}/dist/css/bootstrap.css > #{tmp}/dist/css/bootstrap.min.css
    """

  master = new RuleCheckoutBranch 'master'
  py01m = new RuleCheckoutBranch 'py-0.1-maintenance'
  py02m = new RuleCheckoutBranch 'py-0.2-maintenance'
  draft00 = new RuleCheckoutTag 'spec-draft-00'
  oldSpec = new RuleCopyFromArchive 'spec-old'
  currentSource = new RuleCurrentSource()
  specLatest = new RuleNewSpec master.target
    specDraft00 = new RuleNewSpec draft00.target
  sphinxLatest = new RuleSphinx master.target
  sphinx01 = new RuleSphinx py01m.target
  sphinx02 = new RuleSphinx py02m.target
  liveSphinx = new RuleSphinx currentSource.target

  injectPyLatest = new RuleInject sphinxLatest.target, "--navbar python/latest --bs"
  injectPy02 = new RuleInject sphinx02.target, "--navbar 'python/0.2' --bs"
  injectPy01 = new RuleInject sphinx01.target, "--navbar 'python/0.1' --bs"
  specLatest = new RuleInject specLatest.target, "--navbar 'spec/latest' --bs"
  spacDraft00 = new RuleInject specDraft00.target, "--navbar 'spec/draft-00' --bs"
  spec10 = new RuleInject oldSpec.target, "--navbar 'spec/1.0' --bs"

  site = new RulePrepareTar
    target: "site"
    deps: [
      "_site/static"
      "_site/index.coffee"
      "build/bootstrap.tar"
      "build/fonts.tar"
    ]
    mounts:
      '/static/bootstrap': 'bootstrap'
      '/python/latest': injectPyLatest.target
      '/python/0.2': injectPy02.target
      '/python/0.1': injectPy01.target
      '/spec/latest': specLatest.target
      '/spec/draft-00': spacDraft00.target
      '/spec/1.0': spec10.target
    getLines: (tmp) -> """
      touch #{tmp}/.nojekyll
      cp -R _site/static #{tmp}

      #{coffeeExec} _site/index.coffee > #{tmp}/index.html
      #{coffeeExec} _site/inject.coffee #{tmp}/index.html --navbar '/' --bs
    """
]



module.exports =
  makefile: makefile.toString()
  main: ->
    fs.writeFileSync "#{__dirname}/../Makefile", makefile.toString()
