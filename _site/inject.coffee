fs = require 'fs'
mustache = require 'mustache'
parseArgs = require 'minimist'
async = require 'async'

jsdom = require 'jsdom'
he = require 'he'

project = require './settings'

argv = parseArgs process.argv.slice(2),
  string: ['navbar']
  boolean: ['jquery', 'nobs']

jquerySrc = fs.readFileSync "#{__dirname}/static/jquery.min.js", "utf-8"
prettySrc = fs.readFileSync "#{__dirname}/static/google-code-prettify/prettify.js", "utf-8"

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context


main = ->
  if argv._[0]?
    console.log "Injecting #{argv._.length} files"
    async.each argv._, injectFile, (err) ->
      if err
        console.log err
      console.log "Finished injecting"

  else
    console.log "No input files, doing nothing"


injectFile = (file, callback) ->
  fs.readFile file, (err, buf) ->
    if err
      throw err

    inject buf.toString(), (errors, injectedHtml) ->

      fs.writeFile file, injectedHtml, (err) ->
        if err
          throw err
        console.log " * injected #{file}"
        callback null


cleanEntities = (html) ->
  # jsdom renders some HTML entities into unicode which causes problems
  he.encode html, allowUnsafeSymbols: true


inject = (html, callback) ->

  scripts = []
  if argv.jquery
    scripts.push "/static/jquery.min.js"
  if not argv.nobs
    scripts.push "/static/bootstrap/js/bootstrap.min.js"

  opts =
    src: [jquerySrc, prettySrc]
    features:
      SkipExternalResources: new RegExp("static")

  jsdom.env html, scripts, opts, (errors, window) ->
    if errors
      console.log errors
      throw errors

    if argv.navbar?
      if argv.navbar == '/'
        sec = 'home'
        ver = undefined
      else
        [sec, ver] = argv.navbar.split('/')
      nav = render "navbar.mustache", {
        menu:
          about: sec == 'home'
          docs: sec == 'python'
          spec: sec == 'spec'
        activeSectionId: sec
        activeSection: project.sections[sec]
        activeVersion: ver
      }
      window.$('body').prepend nav

    window.$('head').prepend """
      <link rel="icon" href="/static/favicon-32.png" sizes="32x32">
      <link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">
    """

    window.$('head').append """
      <script type="text/javascript">
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

        ga('create', 'UA-12144432-3', 'auto');
        ga('send', 'pageview');
      </script>
      """

    if not argv.nobs
      window.$('head').append """
        <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
      """

    window.$('head').append "\n\n"

    window.prettyPrint()

    callback null, cleanEntities window.document.documentElement.outerHTML

main()
