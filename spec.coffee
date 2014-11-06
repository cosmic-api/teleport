fs = require 'fs'
jsdom = require 'jsdom'
mustache = require 'mustache'

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context

html = (fs.readFileSync "teleport/teleport.html").toString()

txt = fs.readFileSync("#{__dirname}/teleport/teleport.txt").toString()

spec = ''
for line in txt.split "\n"
  longLine = /^\S.*$/.test line
  if longLine
    if /^Boronine.*$/.test(line) or /^Internet.*2014$/.test(line)
      line = "<span class='page-stuff'>#{line}</span>"
    else
      line = "<span class='title'>#{line}</span>"

  spec += line + "\n"

console.log render "spec.html", body: "<pre class='rfc'>#{spec}</pre>"
