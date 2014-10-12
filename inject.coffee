fs = require 'fs'
find = require 'find'
jade = require 'jade'
jsdom = require 'jsdom'
jquery = require 'jquery'
project = require './settings'
argv = require('optimist').argv

getTemplate = (file) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return jade.compile raw

makeScriptElement = (doc, url) ->
  script = doc.createElement 'script'
  script.type  = "text/javascript"
  script.src = url
  return script

dir = argv.dir
sec = argv.section
ver = argv.version
jq = argv.jquery

nav = getTemplate("top_nav_docs.jade")
  activeSectionId: sec
  activeSection: project.sections[sec]
  activeProject: project
  activeVersion: ver

find.eachfile /.html$/, dir, (file) ->
  html = (fs.readFileSync file).toString()

  jsdom.env html, (errors, window) ->

    $ = jquery.create window

    $('body').prepend nav
    $('head').append """
      <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
    """
    if jq
      $('head').append """
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
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

    fs.writeFileSync file, window.document.innerHTML
    console.log "Injected content into #{file}"
