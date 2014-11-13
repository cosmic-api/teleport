_ = require 'underscore'
fs = require 'fs'

# Executables
coffeeExec = "node_modules/.bin/coffee"


ruleToString = (rule) ->
  ret = "#{rule.targetFile}: #{rule.deps.join(' ')}\n"
  for line in (rule.lines.split '\n')
    line = line.trim()
    if line != ''
      ret += "\t#{line}\n"
  return "#{ret}\n"

makefile = """
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

build/bootstrap-3.3.0-dist.zip:
\t(cd build && wget https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip)

build/bootstrap.tar: build/bootstrap-lumen.css build/bootstrap-3.3.0-dist.zip
\trm -rf tmp/bootstrap
\tunzip build/bootstrap-3.3.0-dist.zip -d tmp
\tmv tmp/dist tmp/bootstrap
\tnamespace-css build/bootstrap-lumen.css -s .bs -o tmp/bootstrap/css/bootstrap.css
\tsed -i 's/\\\\.bs\\ body/\\\\.bs/g' tmp/bootstrap/css/bootstrap.css
\tcp tmp/bootstrap/css/bootstrap.css tmp/bootstrap/css/bootstrap.min.css
\ttar cf build/bootstrap.tar -C tmp/bootstrap .

build/flask-sphinx-themes.tar:
\twget https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip -O tmp/flask-sphinx-themes.zip
\trm -rf tmp/flask-sphinx-themes-master
\t(cd tmp; unzip flask-sphinx-themes.zip)
\ttar cf build/flask-sphinx-themes.tar -C tmp/flask-sphinx-themes-master .

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

addRule = (rule) ->
  makefile += ruleToString(rule)

addRulePrepareTar = (rule) ->
  {target, deps, resultDir, getLines, mounts} = rule
  tmp = "tmp/#{target}"

  mounts = [] if not mounts?

  mountLines = []
  for root, source of mounts
    # Since we're mounting it, we must be dependent on it
    deps.push "build/#{source}.tar"
    mountLines.push "mkdir -p #{tmp}#{root}"
    mountLines.push "tar xf build/#{source}.tar -C #{tmp}#{root}"

  lines = """
    rm -rf #{tmp}
    mkdir #{tmp}
    #{mountLines.join("\n")}
    #{getLines(tmp)}
    tar cf build/#{target}.tar -C #{tmp}#{resultDir} .
  """

  addRule
    targetFile: "build/#{target}.tar"
    deps: deps
    lines: lines


copyFromArchive = (name) ->
  dest = "build/archive-#{name}.tar"
  source = "_site/archive/#{name}.tar"
  addRule
    targetFile: dest
    deps: [source]
    lines: "cp -R #{source} #{dest}"
  return "archive-#{name}"


sphinx = (source) ->
  target = "#{source}-sphinx"

  addRulePrepareTar
    target: target
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

  return target

inject = (source, args) ->
  target = "#{source}-inject"

  addRulePrepareTar
    target: target
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
  return target

checkout = (name, refFile) ->
  targetFile = "build/checkouts-#{name}.tar"
  addRule
    targetFile: targetFile
    deps: [refFile]
    lines: "git --git-dir .git archive $(shell cat #{refFile}) > #{targetFile}"
  return "checkouts-#{name}"

checkoutBranch = (branch) ->
  return checkout branch, ".git/refs/heads/#{branch}"

checkoutTag = (tag) ->
  return checkout tag, ".git/refs/tags/#{tag}"


currentSource = ->
  addRule
    targetFile: "build/current-source.tar"
    deps: []
    lines: """
      git ls-files -o -i --exclude-standard > tmp/excludes
      rm -f build/current-source.tar
      # We are excluding build/current-source.tar so tar doesn't complain about recursion
      tar cf build/current-source.tar --exclude build/current-source.tar --exclude-from=tmp/excludes .
    """
  return "current-source"


newSpec = (source) ->
  target = "#{source}-xml2rfc"

  addRulePrepareTar
    target: target
    deps: ["_site/spec.coffee", "_site/templates/spec.mustache"]
    resultDir: '/out'
    mounts:
      '/': source
    getLines: (tmp) -> """
      (cd #{tmp}/_spec; xml2rfc teleport.xml --text)
      mkdir #{tmp}/out
      #{coffeeExec} _site/spec.coffee < #{tmp}/_spec/teleport.txt > #{tmp}/out/index.html
    """
  return target


master = checkoutBranch('master')
draft00 = checkoutTag('spec-draft-00')

addRulePrepareTar
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
    '/python/latest': inject sphinx(master), "--section python --version latest --jquery"
    '/python/0.2': inject sphinx(checkoutBranch('py-0.2-maintenance')), "--section python --version '0.2' --jquery"
    '/python/0.1': inject sphinx(checkoutBranch('py-0.1-maintenance')), "--section python --version '0.1' --jquery"
    '/spec/latest': inject newSpec(master), "--section spec --version latest --nobs"
    '/spec/draft-00': inject newSpec(draft00), "--section spec --version 'draft-00' --nobs"
    '/spec/1.0': inject copyFromArchive("spec-old"), "--section spec --version '1.0' --jquery"
  getLines: (tmp) -> """
    touch #{tmp}/.nojekyll
    cp -R _site/static #{tmp}

    #{coffeeExec} _site/index.coffee > tmp/site/index.html
    #{coffeeExec} _site/inject.coffee --file tmp/site/index.html --section home --nobs
  """



sphinx(currentSource())

module.exports =
  makefile: makefile


module.exports =
  makefile: makefile
  main: ->
    fs.writeFileSync "#{__dirname}/../Makefile", makefile
