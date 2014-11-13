_ = require 'underscore'
fs = require 'fs'

# Executables
coffeeExec = "node_modules/.bin/coffee"


commandsFromLines = (lines) ->
  lines = (line.trim() for line in lines.split '\n')
  return _.filter lines, (line) -> line != ''


class Makefile

  constructor: (@initial) ->
    @initial = "" if not @initial?
    @rules = []

  addRule: (rule) ->
    @rules.push rule

  toString: ->
    s = @initial
    for rule in @rules
      s += rule.toString() + "\n\n"
    return s



class Rule

  constructor: (opts) ->
    {@target, @deps, @commands} = opts

  toString: ->
    "build/#{@target}.tar: #{@deps.join(' ')}\n\t#{@commands.join('\n\t')}"



class RulePrepareTar extends Rule

  constructor: (opts) ->
    {target, deps, resultDir, getLines, mounts} = opts
    tmp = "tmp/#{target}"

    mounts = [] if not mounts?

    mountLines = []
    for root, source of mounts
      # Since we're mounting it, we must be dependent on it
      deps.push "build/#{source}.tar"
      mountLines.push "mkdir -p #{tmp}#{root}"
      mountLines.push "tar xf build/#{source}.tar -C #{tmp}#{root}"

    @target = target
    @deps = deps
    @commands = ["rm -rf #{tmp}", "mkdir #{tmp}"]
      .concat mountLines
      .concat(commandsFromLines getLines(tmp))
      .concat ["tar cf build/#{target}.tar -C #{tmp}#{resultDir} ."]


class RuleCopyFromArchive extends Rule

  constructor: (name) ->
    source = "_site/archive/#{name}.tar"

    @target = "archive-#{name}"
    @deps = [source]
    @commands = ["cp -R #{source} build/#{@target}.tar"]


class RuleCheckout extends Rule

  constructor: (name, refFile) ->
    @target = "checkouts-#{name}"
    @deps = [refFile]
    @commands = [
      "git --git-dir .git archive $(shell cat #{refFile}) > build/#{@target}.tar"
    ]


class RuleCheckoutBranch extends RuleCheckout

  constructor: (branch) ->
    super branch, ".git/refs/heads/#{branch}"


class RuleCheckoutTag extends RuleCheckout

  constructor: (tag) ->
    super tag, ".git/refs/tags/#{tag}"


class RuleCurrentSource extends Rule

  constructor: ->
    @target = "current-source"
    @deps = []
    @commands = commandsFromLines """
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
      resultDir: '/'
      deps: [
        "_site/inject.coffee"
        "_site/settings.coffee"
        "_site/templates/navbar.mustache"
        "node_modules"
      ]
      mounts:
        '/': source
      getLines: (tmp) -> """
        #{coffeeExec} _site/inject.coffee --dir #{tmp} #{args}
      """


class RuleDownloadZip extends RulePrepareTar

  constructor: (target, url) ->
    super
      target: target
      resultDir: '/out'
      deps: []
      getLines: (tmp) -> """
        wget #{url} -O #{tmp}/src-#{target}.zip
        mkdir #{tmp}/out
        unzip #{tmp}/src-#{target}.zip -d #{tmp}/out
      """


initial = """
.PHONY: clean deploy site py

clean:
\trm -rf build/*
\trm -rf tmp/*

deploy:
\t(cd tmp/site; rsync -avz -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" --progress . root@104.131.5.252:/root/teleport-json.org)

site:
\t#{coffeeExec} _site/live.coffee site

py:
\t#{coffeeExec} _site/live.coffee py

# Reinstall stuff if package.json is modified
node_modules: package.json
\tnpm install

build/bootstrap-lumen.css:
\t(cd build && wget http://bootswatch.com/lumen/bootstrap.css && mv bootstrap.css bootstrap-lumen.css)

build/bootstrap.tar: build/bootstrap-lumen.css build/bootstrap-dist.tar
\trm -rf tmp/bootstrap
\ttar xf build/bootstrap-dist.tar -d tmp
\tmv tmp/dist tmp/bootstrap
\tnamespace-css build/bootstrap-lumen.css -s .bs -o tmp/bootstrap/css/bootstrap.css
\tsed -i 's/\\\\.bs\\ body/\\\\.bs/g' tmp/bootstrap/css/bootstrap.css
\tcp tmp/bootstrap/css/bootstrap.css tmp/bootstrap/css/bootstrap.min.css
\ttar cf build/bootstrap.tar -C tmp/bootstrap .

build/fonts.tar:
\trm -rf tmp/fonts
\tmkdir -p tmp/fonts
\twget -O tmp/fonts/index.css "http://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,700,400italic|Ubuntu+Mono:400,700"
\tcat tmp/fonts/index.css | grep -o -e "http.*ttf" > tmp/fonts/download.list
\t(cd tmp/fonts && xargs -i wget '{}' < download.list)
\tmkdir tmp/fonts/out
\tcp tmp/fonts/*.ttf tmp/fonts/out
\tsed 's/http.*\\/\\(.*\\.ttf\\)/\\1/g' < tmp/fonts/index.css > tmp/fonts/out/index.css
\ttar cf build/fonts.tar -C tmp/fonts/out .


"""

makefile = new Makefile initial
makefile.rules = [
  flaskSphinxThemes = new RuleDownloadZip "flask-sphinx-themes", "https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip"
  bootstrapDist = new RuleDownloadZip "bootstrap-dist", "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip"

  master = new RuleCheckoutBranch 'master'
  py01m = new RuleCheckoutBranch '0.1-maintenance'
  py02m = new RuleCheckoutBranch '0.2-maintenance'
  draft00 = new RuleCheckoutTag 'spec-draft-00'
  oldSpec = new RuleCopyFromArchive 'spec-old'
  currentSource = new RuleCurrentSource()
  specLatest = new RuleNewSpec master.target
    specDraft00 = new RuleNewSpec draft00.target
  sphinxLatest = new RuleSphinx master.target
  sphinx01 = new RuleSphinx py01m.target
  sphinx02 = new RuleSphinx py02m.target
  liveSphinx = new RuleSphinx currentSource.target
  site = new RulePrepareTar
    target: "site"
    deps: [
      "_site/static"
      "_site/index.coffee"
      "build/bootstrap.tar"
      "build/fonts.tar"
    ]
    resultDir: '/'
    mounts:
      '/static/bootstrap': 'bootstrap'
      '/static/fonts': 'fonts'
      '/python/latest': new RuleInject(sphinxLatest.target, "--section python --version latest --jquery").target
      '/python/0.2': new RuleInject(sphinx02.target, "--section python --version '0.2' --jquery").target
      '/python/0.1': new RuleInject(sphinx01.target, "--section python --version '0.1' --jquery").target
      '/spec/latest': new RuleInject(specLatest.target, "--section spec --version latest --nobs").target
      '/spec/draft-00': new RuleInject(specDraft00.target, "--section spec --version 'draft-00' --nobs").target
      '/spec/1.0': new RuleInject(oldSpec.target, "--section spec --version '1.0' --jquery").target
    getLines: (tmp) -> """
      touch #{tmp}/.nojekyll
      cp -R _site/static #{tmp}

      #{coffeeExec} _site/index.coffee > tmp/site/index.html
      #{coffeeExec} _site/inject.coffee --file tmp/site/index.html --section home --nobs
    """
]



module.exports =
  makefile: makefile.toString()
  main: ->
    fs.writeFileSync "#{__dirname}/../Makefile", makefile.toString()
