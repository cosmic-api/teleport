fs = require 'fs'
mustache = require 'mustache'

render = (file, context) ->
  raw = fs.readFileSync("#{__dirname}/templates/#{file}").toString()
  return mustache.render raw, context

txt = fs.readFileSync("#{__dirname}/../_spec/teleport.txt").toString()

pageStuffMode = null
titleMode = null

spec = ''
for line in txt.split "\n"

  if pageStuffMode != false
    if line == ''
      if pageStuffMode == true
        pageStuffMode = false
    else
      if /^Internet\ Engineering\ Task\ Force/.test line
        pageStuffMode = true
      line = "<span class='page-stuff'>#{line}</span>"

  else if pageStuffMode == false and titleMode != false
    if line == ''
      if titleMode == true
        titleMode = false
    else
      titleMode = true
      line = "<span class='title'>#{line}</span>"

  else if titleMode == false
    longLine = /^\S.*$/.test line
    if longLine
      if /^Boronine.*$/.test(line) or /^Internet.*2014$/.test(line)
        line = "<span class='page-stuff'>#{line}</span>"
      else
        line = "<span class='title'>#{line}</span>"

  spec += line + "\n"

console.log render "spec.mustache", body: "<pre class='rfc'>#{spec}</pre>"
