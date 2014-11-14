fs = require 'fs'
mime = require 'mime'
cheerio = require 'cheerio'
tar = require 'tar-stream'
connect = require 'connect'
parseArgs = require 'minimist'
http = require 'http'

tinylr = require 'tiny-lr'
spawn = require('child_process').spawn

{makefile} = require './configure'

lrport = 35729


print = ->
  console.log "| +", arguments...
print2 = ->
  console.log "|   -", arguments...
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


# This stores the entire contents of the tarball
objects = null


main = ->
  argv = parseArgs process.argv.slice(2)
  if argv._.length == 0
    throw "missing argument"

  archive = argv._[0]

  loadSpecificTar = (callback) ->
    loadTar "#{__dirname}/../build/#{archive}.tar", callback

  loadSpecificTar (err, o) ->
    objects = o

    app = connect()
    app.use (req, res, next) ->
      path = '.' + req.url
      o = objects[path]

      if o == null
        path += 'index.html'
        o = processHtml objects[path]

      if o != null and o != undefined

        headers =
          'Content-Type': mime.lookup path
          'Cache-Control': 'max-age=0, no-cache, no-store'

        res.writeHead 200, headers
        res.write o
        res.end()

      res.writeHead 404
      res.end()

    #setInterval triggerReload, 5000

    runLiveReload (err, server) ->
      http.createServer(app).listen 8000, ->
        print "Serving build/#{archive}.tar on 8000"

        leaves = makefile.gatherNodes "build/#{archive}.tar"
        leaves.sort()
        print "Watching files:"
        for file in leaves
          print2 file
        hr()

        buildMode = false

        for leaf in leaves
          fs.watch leaf, (event, filename) ->
            return if buildMode
            buildMode = true

            print "#{filename} changed, running 'make build/#{archive}.tar'"

            hr()
            make = spawn 'make', ["build/#{archive}.tar"]
            make.stdout.pipe process.stdout
            make.stderr.pipe process.stderr
            make.on 'close', (code, signal) ->
              buildMode = false
              hr()

              if code?
                print "make returned #{code}"

              triggerReload()


if require.main == module
  main()
