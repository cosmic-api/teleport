fs = require 'fs'
find = require 'find'
mustache = require 'mustache'
jsdom = require 'jsdom'
jquery = require 'jquery'
project = require './settings'
argv = require('optimist').argv

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context

makeScriptElement = (doc, url) ->
  script = doc.createElement 'script'
  script.type  = "text/javascript"
  script.src = url
  return script

dir = argv.dir
sec = argv.section
ver = argv.version
jq = argv.jquery

activeSection = project.sections[sec]

nav = render "top_nav_docs.html", {
  menu:
    about: false
    docs: sec == 'python'
    spec: sec == 'spec'
  activeSectionId: sec
  activeSection: activeSection
  activeVersion: ver
  showCheckouts: activeSection.checkouts.length > 0
}


inject = (html, callback) ->

  jsdom.env html, (errors, window) ->

    if errors
      callback errors

    $ = jquery.create window

    $('body').prepend nav
    $('head').append """
      <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
      <link rel="icon" href="/static/favicon-32.png" sizes="32x32">
      <link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">
    """
    if jq
      $('head').append """
	<script src="/static/jquery.min.js"></script>
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
    window.document.head.appendChild makeScriptElement window.document, "/static/bootstrap/js/bootstrap.min.js"
    $('head').append "\n\n"

    callback null, window.document.innerHTML


find.eachfile /.html$/, dir, (file) ->
  html = (fs.readFileSync file).toString()

  inject html, (errors, injectedHtml) ->

    fs.writeFileSync file, injectedHtml
    console.log "Injected content into #{file}"

