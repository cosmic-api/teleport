fs = require 'fs'
mime = require 'mime'
cheerio = require 'cheerio'
tar = require 'tar-stream'
connect = require 'connect'
parseArgs = require 'minimist'
http = require 'http'




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

  return $.html()


main = ->
  argv = parseArgs process.argv.slice(2)
  if argv._.length == 0
    throw "missing argument"

  loadTar "#{__dirname}/../build/#{argv._[0]}.tar", (err, objects) ->

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

    console.log 'Listening on 8000'
    http.createServer(app).listen(8000)


if require.main == module
  main()
