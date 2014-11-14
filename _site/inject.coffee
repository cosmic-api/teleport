fs = require 'fs'
mustache = require 'mustache'
parseArgs = require 'minimist'
hljs = require 'highlight.js'

cheerio = require 'cheerio'
he = require 'he'


navbarTemplate = fs.readFileSync("#{__dirname}/templates/navbar.mustache").toString()


main = ->
  argv = parseArgs process.argv.slice(2),
    string: ['navbar']
    boolean: ['jquery', 'bs']

  if argv._.length == 0
    console.log "No input files, doing nothing"
    return

  options =
    navbar: argv.navbar
    bs: argv.bs

  console.log "Injecting #{argv._.length} files"
  for filename in argv._
    injectFile filename, options



injectFile = (filename, options) ->
  fs.readFile filename, (err, buf) ->
    if err
      throw err

    injectedHtml = inject buf.toString(), options

    fs.writeFile filename, injectedHtml, (err) ->
      if err
        throw err
      console.log " * injected #{filename}"


renderNavbar = (path) ->

  if path == '/'
    sec = 'home'
    ver = undefined
  else
    [sec, ver] = path.split('/')

  sections = {
    home:
      star: true
      repoLink: true
      subMenuShow: false
    python:
      star: true
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { divider: true }
        { version: '0.2' }
        { version: '0.1' }
      ]
    spec:
      star: true
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'latest' }
        { divider: true }
        { version: '1.0' }
      ]
  }

  return mustache.render navbarTemplate, {
    menu:
      about: sec == 'home'
      docs: sec == 'python'
      spec: sec == 'spec'
    activeSectionId: sec
    activeSection: sections[sec]
    activeVersion: ver
  }


inject = (html, options) ->
  {bs, navbar} = options

  $ = cheerio.load html

  # Normalize jquery. Make sure there is one single jquery for every page.
  $('script').each ->
    src = $(@).attr('src')
    if src? and new RegExp("jquery(\.min)?\.js").test src
      $(@).remove()
  $('head').prepend '<script type="text/javascript" src="/static/jquery.min.js"></script>'

  if bs
    $('head').append """
      <script type="text/javascript" src="/static/bootstrap/js/bootstrap.min.js"></script>
      <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>


    """

  $('head').prepend """
    <link rel="icon" href="/static/favicon-32.png" sizes="32x32">
    <link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">
  """

  $('head').append """
    <script type="text/javascript">
      (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

      ga('create', 'UA-12144432-3', 'auto');
      ga('send', 'pageview');
    </script>
  """

  $('pre.highlight-please').each ->
    if $(@).hasClass 'python'
      $(@).html hljs.highlight('python', $(@).text()).value
  $('pre.highlight-please').removeClass 'highlight-please'

  if navbar?
    $('body').prepend renderNavbar navbar

  return $.html()

main()
