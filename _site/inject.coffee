fs = require 'fs'
find = require 'find'
mustache = require 'mustache'

jsdom = require 'jsdom'
he = require 'he'

project = require './settings'
argv = require('optimist').argv
jquerySrc = fs.readFileSync "#{__dirname}/static/jquery.min.js", "utf-8"

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context

makeScriptElement = (doc, url) ->
  script = doc.createElement 'script'
  script.type  = "text/javascript"
  script.src = url
  return script

dir = argv.dir
file = argv.file
sec = argv.section
ver = argv.version

main = ->
  if file?
    injectFile file

  if dir?
    find.eachfile /.html$/, dir, (file) ->
      injectFile file


injectFile = (file) ->
  html = (fs.readFileSync file).toString()

  inject html, (errors, injectedHtml) ->

    fs.writeFileSync file, injectedHtml
    console.log "Injected content into #{file}"


activeSection = project.sections[sec]

nav = render "navbar.mustache", {
  menu:
    about: sec == 'home'
    docs: sec == 'python'
    spec: sec == 'spec'
  activeSectionId: sec
  activeSection: activeSection
  activeVersion: ver
}


cleanEntities = (html) ->
  # jsdom renders some HTML entities into unicode which causes problems
  he.encode html, allowUnsafeSymbols: true

inject = (html, callback) ->

  jsdom.env html, src: [jquerySrc], (errors, window) ->
    if errors
      callback errors

    if argv.jquery
      window.document.head.appendChild makeScriptElement window.document, "/static/jquery.min.js"

    window.$('body').prepend nav
    window.$('head').prepend """
      <link rel="icon" href="/static/favicon-32.png" sizes="32x32">
      <link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">
    """

    ga = window.document.createElement 'script'
    ga.type  = "text/javascript"
    ga.text = """
      (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

      ga('create', 'UA-12144432-3', 'auto');
      ga('send', 'pageview');
    """
    window.document.head.appendChild ga

    if not argv.nobs
      window.document.head.appendChild makeScriptElement window.document, "/static/bootstrap/js/bootstrap.min.js"
      window.$('head').append """
        <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
      """

    window.$('head').append "\n\n"

    callback null, cleanEntities window.document.documentElement.outerHTML

main()
