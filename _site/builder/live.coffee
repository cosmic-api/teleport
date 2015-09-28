fs = require 'fs'
url = require 'url'
mime = require 'mime'
cheerio = require 'cheerio'
tar = require 'tar-stream'
connect = require 'connect'
parseArgs = require 'minimist'
http = require 'http'
chokidar = require 'chokidar'

tinylr = require 'tiny-lr'
spawn = require('child_process').spawn

{ EventEmitter } = require 'events'


print = ->
  console.log "| .", arguments...
print2 = ->
  console.log "|   .", arguments...
hr = ->
  console.log '+-------------------------------'



class Server extends EventEmitter

  constructor: (options) ->
    {@tarball, @port, @lrport} = options
    @objects = null

  loadArchive: ->
    print "loading #{@tarball} into memory"
    loadTar @tarball, (err, objects) =>
      @objects = objects
      @emit 'loaded'

  run: ->
    @lrserver = tinylr()
    @lrserver.listen @lrport, =>
      print "LiveReload running on #{@lrport} ..."
      @emit 'lr-listening'

    app = connect()
    app.use (req, res, next) =>
      path = '.' + url.parse(req.url).pathname
      maybeFile = @objects[path]

      if maybeFile != null and maybeFile != undefined
        mimetype = mime.lookup path
      else
        maybeFile = @objects[path + 'index.html']
        mimetype = 'text/html'
        if maybeFile == null or maybeFile == undefined
          res.writeHead 404
          res.end()
          return

      if mimetype == 'text/html'
        body = @processHtml maybeFile
      else
        body = maybeFile

      headers =
        'Content-Type': mimetype
        'Cache-Control': 'max-age=0, no-cache, no-store'
      res.writeHead 200, headers
      res.write body
      res.end()


    @server = http.createServer(app).listen @port
    @server.on 'listening', (err) =>
      if err?
        throw err
      print "HTTP server listening on #{@port}"
      @emit 'server-listening'

  triggerReload: (callback) ->
    print "triggering reload"

    req = http.request
      hostname: '127.0.0.1'
      port: @lrport
      path: '/changed?files=*'
      method: 'POST'

    req.on 'response', (response) =>
      success = response.statusCode == 200
      data = ""
      response.on 'data', (chunk) => data += chunk.toString()
      response.on 'end', ->
        data = JSON.parse data
        print2 "#{data.clients.length} client(s)"
        if callback?
          if success then callback null else callback response

    req.end()

  processHtml: (html) ->
    # decodeEntities: true caused weird &quots; Should be investigated someday
    $ = cheerio.load html, decodeEntities: false

    # Github buttons are annoying in develoment
    $('iframe').each ->
      if new RegExp("ghbtns").test $(@).attr('src')
        $(@).remove()

    $('body').append """
      <script type="text/javascript" src="http://127.0.0.1:#{@lrport}/livereload.js"></script>
    """

    return $.html()



class Watcher extends EventEmitter

  constructor: (@files) ->

  announce: ->
    print "watching files:"
    for file in @files
      print2 file

  watch: ->
    # Clean up old watcher
    if @watcher?
      @watcher.close()
    @watcher = chokidar.watch @files, persistent: true

    @watcher.on 'change', (filename) =>
      # Stupid recursive behavior
      return if filename not in @files
      @emit 'kabam', filename

    @watcher.on 'unlink', (filename) =>
      return if filename not in @files
      @emit 'kabam', filename

    @watcher.on 'error', (err) ->
      throw err



class Builder extends EventEmitter

  constructor: (@makefile, @tarball) ->
    @building = false

  build: ->
    # Building something? Kill it and call the function again
    if @building == true
      # Someone else is already quitting the build? Too bad, detach them.
      @removeAllListeners 'killed'
      @once 'killed', ->
        @building = false
        @build()
      @kill()
      return

    @building = true

    print "generating Makefile"
    @makefile.writeMakefileSync()
    print "running 'make #{@tarball}'"

    hr()
    if process.cwd() == @makefile.rootDir
      @make = spawn 'make', [@tarball]
    else
      @make = spawn 'make', ["-C", @makefile.rootDir, @tarball]

    @make.stdout.pipe process.stdout
    @make.stderr.pipe process.stderr

    @make.on 'close', (code, signal) =>
      hr()
      if code != 0
        if signal == 'SIGTERM'
          print "make was killed by watcher"
          @building = false
          @emit 'killed'
          return

        else
          print "make returned #{code}"
          throw "fix the build before going live!"

      @building = false
      @emit 'done'

  kill: ->
    @make.kill 'SIGTERM'



class LiveAgent extends EventEmitter

  constructor: (options) ->
    {@makefile, @tarball, port, lrport} = options
    if not port?
      port = 8000
    if not lrport?
      lrport = 35729

    deps = @makefile.gatherDeps @tarball
    deps.sort()
    @watcher = new Watcher(deps)
    @server = new Server
      tarball: @tarball
      port: port
      lrport: lrport

  bootstrap: (callback) ->
    firstBuild = new Builder @makefile, @tarball
    firstBuild.build()
    firstBuild.on 'done', =>
      @server.once 'loaded', =>
        # The first build is done and the server is ready
        @watcher.watch()
        @server.run()
        @watcher.announce()
        callback()
      @server.loadArchive()

  loop: ->
    builder = new Builder(@makefile, @tarball)

    @watcher.on 'kabam', (filename) =>
      builder.removeAllListeners 'done'
      builder.once 'done', =>
        @server.once 'loaded', @server.triggerReload
        @server.loadArchive()
      builder.build()

  run: ->
    @bootstrap =>
      @loop()




# Loads tar file into memory and returns it as a JavaScript object
loadTar = (file, next) ->
  objects = {}

  extract = tar.extract()
  extract.on 'entry', (header, stream, callback) ->

    if header.type == 'file'
      chunks = []
      stream.on 'data', (chunk) ->
        chunks.push chunk
      stream.on 'end', ->
        objects[header.name] = Buffer.concat chunks
        callback()

      stream.resume()

    else if header.type == 'directory'
      objects[header.name] = null
      callback()

  extract.on 'finish', ->
    next null, objects

  fs.createReadStream(file).pipe extract



module.exports = {
  print: print
  print2: print2
  loadTar: loadTar
  Server: Server
  Watcher: Watcher
  Builder: Builder
  LiveAgent: LiveAgent
}













