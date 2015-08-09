s3 = require 's3'

parseArgs = require 'minimist'
argv = parseArgs process.argv.slice(2)

console.log argv


client = s3.createClient
  s3Options:
    accessKeyId: process.env.AWS_ACCESS_KEY_ID
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    # any other options are passed to new AWS.S3()
    # See: http://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/Config.html#constructor-property

params =
  localDir: argv.d
  deleteRemoved: true
  s3Params:
    Bucket: "www.teleport-json.org"
    Prefix: ""
    # other options supported by putObject, except Body and ContentLength.
    # See: http://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/S3.html#putObject-property

uploader = client.uploadDir params

uploader.on 'error', (err) ->
  console.error "unable to sync:", err.stack

uploader.on 'progress', ->
  console.log "progress", uploader.progressAmount, uploader.progressTotal

uploader.on 'end', ->
  console.log "done uploading"
