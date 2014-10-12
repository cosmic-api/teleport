fs = require 'fs'
find = require 'find'
jade = require 'jade'
jsdom = require 'jsdom'
jquery = require 'jquery'
{projectOrder, projects} = require './settings'
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
pro = argv.project
sec = argv.section
ver = argv.version
jq = argv.jquery

gaText = getTemplate("includes/google_analytics.jade")()
nav = getTemplate("includes/top_nav_docs.jade")
  activeProjectId: pro
  activeProject: projects[pro]
  activeSectionId: sec
  activeSection: projects[pro].sections[sec]
  activeVersion: ver
  projectOrder: projectOrder
  projects: projects

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
      var _gaq = _gaq || [];
      var pluginUrl = '//www.google-analytics.com/plugins/ga/inpage_linkid.js';
      _gaq.push(['_require', 'inpage_linkid', pluginUrl]);
      _gaq.push(['_setAccount', 'UA-36006075-1']);
      _gaq.push(['_setDomainName', 'cosmic-api.com']);
      _gaq.push(['_trackPageview']);
      (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();
    """
    window.document.head.appendChild ga
    window.document.head.appendChild makeScriptElement window.document, "/static/bootstrap/js/bootstrap.min.js"
    $('head').append "\n\n"

    fs.writeFileSync file, window.document.innerHTML
    console.log "Injected content into #{file}"
