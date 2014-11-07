fs = require 'fs'
find = require 'find'
jsdom = require 'jsdom'
jquery = require 'jquery'
argv = require('optimist').argv

find.eachfile /.html$/, argv.dir, (file) ->
  html = (fs.readFileSync file).toString()

  jsdom.env html, (errors, window) ->

    $ = jquery.create window
    # Style table with Bootstrap by adding the table class
    $('table.docutils').addClass('table').removeAttr('border')

    fs.writeFileSync file, window.document.innerHTML
    console.log "Bootstrappified #{file}"
