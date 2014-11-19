parseArgs = require 'minimist'

{makefile} = require './configure'
obnoxygen = require 'obnoxygen'

{LiveAgent} = obnoxygen.live
{archiveFile} = obnoxygen

main = ->

  argv = parseArgs process.argv.slice(2)
  if argv._.length == 0
    throw "missing argument"

  archive = argv._[0]

  agent = new LiveAgent
    makefile: makefile
    tarball: archiveFile(archive)

  agent.run()


if require.main == module
  main()


