fs = require 'fs'
mustache = require 'mustache'

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context

nav = render "top_nav_docs.html",
  menu:
    about: true
    docs: false

console.log """
<html>
<head>
<link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
<link rel="icon" href="/static/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">
<title>Teleport - Lightweight JSON Types</title>
<script src="/static/jquery.min.js"></script>
<script src="/static/bootstrap/js/bootstrap.min.js"></script>
</head>
<body class="bs" style="margin:0px">
    #{nav}
    <div class="container">
		<h1>Teleport</h1>
		</h4>Lightweight JSON Types</h4>
	</div>
</body>
</html>
"""
