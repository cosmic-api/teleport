fs = require 'fs'
mustache = require 'mustache'
parseArgs = require 'minimist'
hljs = require 'highlight.js'

cheerio = require 'cheerio'


navbarTemplate = fs.readFileSync("#{__dirname}/templates/navbar.mustache").toString()


main = ->
  argv = parseArgs process.argv.slice(2),
    string: ['navbar']
    boolean: ['bs', 'highlight', 'analytics']

  if argv._.length == 0
    console.log "No input files, doing nothing"
    return

  console.log "Injecting #{argv._.length} file(s)"
  for filename in argv._
    injectFile filename, argv



injectFile = (filename, options) ->
  fs.readFile filename, (err, buf) ->
    if err
      throw err

    injectedHtml = inject buf.toString(), options

    fs.writeFile filename, injectedHtml, (err) ->
      if err
        throw err
      console.log " * injected #{filename}"



inject = (html, options) ->
  {navbar, bs, highlight, analytics} = options

  $ = cheerio.load html

  if bs
    # Normalize jquery. Make sure there is one single jquery for every page.
    $('script').each ->
      src = $(@).attr('src')
      if src? and new RegExp("jquery(\.min)?\.js").test src
        $(@).remove()
    $('head').prepend '<script type="text/javascript" src="/static/jquery.min.js"></script>'
    $('head').append """
      <script type="text/javascript" src="/static/bootstrap/js/bootstrap.min.js"></script>
      <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
      <link rel="icon" href="/static/favicon-32.png" sizes="32x32">
      <link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">

    """

  if analytics
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
  if highlight
    $('pre.highlight-please').each ->
      if $(@).hasClass 'python'
        $code = $ '<code>'
        $code.addClass 'hljs python'
        $code.html hljs.highlight('python', $(@).text()).value
        $(@).html ''
        $(@).append $code

        #$(@).html hljs.highlight('python', $(@).text()).value
    $('pre.highlight-please').removeClass 'highlight-please'

  if navbar?
    $('body').prepend renderNavbar navbar

  return $.html()



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
      star: false
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: '0.4' }
        { version: '0.2' }
      ]
    spec:
      star: false
      repoLink: true
      subMenuShow: true
      subMenu: [
        { version: 'draft-02' }
        { version: 'draft-01' }
        { version: 'draft-00' }
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
    latestSpec: sections.spec.subMenu[0].version
    latestPython: sections.python.subMenu[0].version
  }



main()
