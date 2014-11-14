fs = require 'fs'
mime = require 'mime'
cheerio = require 'cheerio'
tar = require 'tar-stream'
connect = require 'connect'
parseArgs = require 'minimist'
http = require 'http'
chokidar = require 'chokidar'

tinylr = require 'tiny-lr'
spawn = require('child_process').spawn


port = 8000
lrport = 35729


print = ->
  console.log "| .", arguments...
print2 = ->
  console.log "|   .", arguments...
hr = ->
  console.log '+-------------------------------'



triggerReload = (callback) ->
  print "triggering reload"

  options =
    hostname: '127.0.0.1'
    port: lrport
    path: '/changed?files=*'
    method: 'POST'

  req = http.request options, (response) ->
    success = response.statusCode == 200
    data = ""
    response.on 'data', (chunk) -> data += chunk.toString()
    response.on 'end', ->
      data = JSON.parse data
      print2 "#{data.clients.length} client(s)"
      if callback?
        if success then callback null else callback response
  req.end()


runLiveReload = (callback) ->
  server = tinylr()
  server.listen lrport, ->
    print "LiveReload running on #{lrport} ..."
    callback null, server


# Loads tar file into memory and returns it as a JavaScript object
loadTar = (file, next) ->
  objects = {}

  extract = tar.extract()
  extract.on 'entry', (header, stream, callback) ->

    if header.type == 'file'
      objects[header.name] = ''
      stream.on 'data', (chunk) ->
        objects[header.name] += chunk.toString()
      stream.on 'end', ->
        callback()

      stream.resume()

    else if header.type == 'directory'
      objects[header.name] = null
      callback()

  extract.on 'finish', ->
    next null, objects

  fs.createReadStream(file).pipe extract


processHtml = (html) ->
  $ = cheerio.load html

  # Github buttons are annoying in develoment
  $('iframe').each ->
    if new RegExp("ghbtns").test $(@).attr('src')
      $(@).remove()

  $('body').append """
    <script type="text/javascript" src="http://127.0.0.1:#{lrport}/livereload.js"></script>
  """

  return $.html()


main = ->
  argv = parseArgs process.argv.slice(2)
  if argv._.length == 0
    throw "missing argument"

  archive = argv._[0]

  # Lock to make sure build isn't interrupted
  buildMode = false
  # Watches get reset on every rebuild
  watcher = null

  # This stores the whole tarball
  store = { objects: null }
  updateStore = (callback) ->
    print "loading build/#{archive}.tar into memory"
    loadTar "#{__dirname}/../build/#{archive}.tar", (err, objects) ->
      store.objects = objects
      callback null

  rebuild = (callback) ->
    buildMode = true
    {makefile, writeMakefileSync} = require './configure'

    # Clean up old watcher
    if watcher != null
      watcher.close()

    print "running './configure'"
    writeMakefileSync()
    print "running 'make build/#{archive}.tar'"

    hr()
    make = spawn 'make', ["build/#{archive}.tar"]
    make.stdout.pipe process.stdout
    make.stderr.pipe process.stderr
    make.on 'close', (code, signal) ->
      hr()
      print "make returned #{code}"
      updateStore ->
        nodes = makefile.gatherNodes "build/#{archive}.tar"
        nodes.sort()
        print "watching files:"

        for file in nodes
          print2 file

        watcher = chokidar.watch nodes, persistent: true
        watcher.on 'change', (filename) ->
          return if buildMode
          return if filename not in nodes
          print "#{filename} changed"
          rebuild ->
            triggerReload ->

        watcher.on 'unlink', (filename) ->
          return if buildMode
          return if filename not in nodes
          print "#{filename} unlinked"
          rebuild ->
            triggerReload ->

        watcher.on 'error', (err) ->
          throw err

        buildMode = false
        callback null

  runServer = (callback) ->

    app = connect()
    app.use (req, res, next) ->
      path = '.' + req.url
      o = store.objects[path]

      if o == null
        path += 'index.html'
        o = processHtml store.objects[path]

      if o != null and o != undefined

        headers =
          'Content-Type': mime.lookup path
          'Cache-Control': 'max-age=0, no-cache, no-store'

        res.writeHead 200, headers
        res.write o
        res.end()

      res.writeHead 404
      res.end()

    server = http.createServer(app).listen port, (err) ->
      if err?
        throw err
      print "HTTP server listening on #{port}"
      callback null, server


  rebuild ->
    runLiveReload ->
      runServer ->



if require.main == module
  main()













