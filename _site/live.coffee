parseArgs = require 'minimist'

{makefile} = require './configure'
{runWithOptions} = require('obnoxygen').live

main = ->

  argv = parseArgs process.argv.slice(2)
  if argv._.length == 0
    throw "missing argument"

  archive = argv._[0]

  runWithOptions
    rootDir: "#{__dirname}/.."
    archive: archive
    makefile: makefile


if require.main == module
  main()


