_ = require 'underscore'
mustache = require 'mustache'
fs = require 'fs'
{build} = require './settings'


render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context


tabbifyLine = (line) ->
  if /^\ +/.test line
    '\t' + line.trim()
  else
     line

mapLines = (text, f) ->
  (_.map (text.split '\n'), f).join '\n'

tabbifyText = (text) ->
  return mapLines text, tabbifyLine


makefile = do ->

  # Executables
  coffeeExec = "node_modules/.bin/coffee"
  # Stuff necessary for injector
  injector = "inject.coffee settings.coffee node_modules templates/navbar.mustache"

  flatLayout = do ->
    d = []
    for section, vers of build.layout
      for version, opts of vers
        d.push _.extend opts, {
          section: section
          version: version
        }
    return d

  context =
    coffeeExec: coffeeExec
    injectorDeps: injector
    checkouts:
      for branch in build.checkouts
        out: "build/checkouts-#{branch}.tar"
        branch: branch
    copy:
      for arc in build.archive
        from: "archive/#{arc}.tar"
        to: "build/archive-#{arc}.tar"
    sphinxes:
      for root in build.sphinx
        out: "build/#{root}-sphinx.tar"
        source: "build/#{root}.tar"
        tmp: "tmp/#{root}-sphinx"
    distDeps: (do ->
      for {content} in flatLayout
        "build/#{content}-inject.tar").join(' ')
    dist:
      for {section, version, content} in flatLayout
        dir: "dist/#{section}/#{version}"
        source: "build/#{content}-inject.tar"
    injections:
      for {section, version, content, jquery, nobs} in flatLayout
        jqueryOpt = if jquery then '--jquery' else ''
        nobsOpt = if nobs then '--nobs' else ''

        tmp: "tmp/#{content}-inject"
        out: "build/#{content}-inject.tar"
        source: "build/#{content}.tar"
        injectorOpts: "--section #{section} --version '#{version}' #{jqueryOpt} #{nobsOpt}"

  tabbifyText render "makefile.mustache", context


module.exports =
  makefile: makefile
