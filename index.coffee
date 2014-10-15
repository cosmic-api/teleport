fs = require 'fs'
mustache = require 'mustache'

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context

nav = render "top_nav_docs.html",
  menu:
    about: true
    docs: false

console.log render "index.html", nav: nav
