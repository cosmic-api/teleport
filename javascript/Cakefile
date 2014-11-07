{exec} = require 'child_process'

coffee = "./node_modules/coffee-script/bin/coffee"

task 'build', 'Build project', ->
  console.log "Compiling HUSL"
  exec "#{coffee} --compile teleport.coffee", (err, stdout, stderr) ->
    throw err if err
    exec 'uglifyjs teleport.js > teleport.min.js', (err, stdout, stderr) ->
      throw err if err
