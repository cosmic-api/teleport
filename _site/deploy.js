var s3 = require("s3");
var parseArgs = require("minimist");
var argv = parseArgs(process.argv.slice(2));
console.log(argv);

var client = s3.createClient({
    s3Options: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    }
});

var params = {
    localDir: argv.d,
    deleteRemoved: true,

    s3Params: {
        Bucket: "www.teleport-json.org",
        Prefix: ""
    }
};

var uploader = client.uploadDir(params);

uploader.on("error", function (err) {
    return console.error("unable to sync:", err.stack);
});

uploader.on("progress", function () {
    return console.log("progress", uploader.progressAmount, uploader.progressTotal);
});

uploader.on("end", function () {
    return console.log("done uploading");
});