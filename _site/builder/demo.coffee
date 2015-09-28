connect = require 'connect'
mime = require 'mime'
http = require 'http'
fs = require 'fs'
{print, print2} = require './live'


# Break if vis not installed
vis = require 'vis'

port = 8001

demoFromMakefile = (makefile) ->
  nodes = []
  edges = []

  gathered = []
  for target, deps of makefile.dag
    if target not in gathered
      gathered.push target
    for dep in deps
      if dep not in gathered
        gathered.push dep

      edges.push
        from: dep
        to: target

  for node in gathered
    nodes.push
      id: node
      label: ''
      title: node

  """
  <html>
  <head>
  <title>Demo</title>
  <script type="text/javascript" src="/vis/vis.min.js"></script>
  <link href="/vis/vis.css" rel="stylesheet" type="text/css" />
  <style type="text/css">
    body {
      margin: 0;
      height: 100%;
      width: 100%;
    }

    #mynetwork {
      width: 100%;
      height: 100%;
    }
  </style>
  </head>
  <body>
  <div id="mynetwork"></div>

    <script type="text/javascript">
      // create an array with nodes
      var nodes = #{JSON.stringify nodes};
      var edges = #{JSON.stringify edges};

      // create a network
      var container = document.getElementById('mynetwork');
      var data = {
        nodes: nodes,
        edges: edges
      };
      var options = {
        edges: {style: 'arrow'},
        physics: {
          barnesHut: {enabled: false},
          repulsion: {nodeDistance: 203, centralGravity: 0.15, springLength: 89, springConstant: 0.072, damping: 0.08}
        }
      };
      var network = new vis.Network(container, data, options);
    </script>

  </body>
  </html>
  """

runDemoServer = (options) ->
  {rootDir, makefile, callback} = options

  app = connect()
  app.use (req, res, next) ->

    statusCode = 200
    headers =
      'Cache-Control': 'max-age=0, no-cache, no-store'

    libFile = req.url.replace  /^\/vis\/(.*)$/, '$1'
    if libFile != req.url
      body = fs.readFileSync "#{rootDir}/node_modules/vis/dist/#{libFile}"
      headers['Content-Type'] = mime.lookup libFile
    else if req.url == '/'
      path = '/index.html'
      body = demoFromMakefile(makefile)
      headers['Content-Type'] = 'text/html'
    else
      statusCode = 404
      body = ''

    res.writeHead statusCode, headers
    res.write body
    res.end()

  server = http.createServer(app).listen port, (err) ->
    if err?
      throw err
    print "HTTP server listening on #{port}"
    callback null, server


module.exports = {
  runDemoServer: runDemoServer
  demoFromMakefile: demoFromMakefile
}