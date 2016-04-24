"use strict";
var fs = require("fs");
var url = require("url");
var http = require("http");
var path = require("path");


function getServer(rootDir) {
    return http.createServer((request, response) => {

        var uri = url.parse(request.url).pathname;
        var filename = path.join(rootDir, uri);

        fs.exists(filename, function(exists) {
            console.log(request.method, filename);
            if(!exists) {
                response.writeHead(404, {"Content-Type": "text/plain"});
                response.write("404 Not Found\n");
                response.end();
                return;
            }

            if (fs.statSync(filename).isDirectory()) filename += '/index.html';

            fs.readFile(filename, "binary", function(err, file) {
                if(err) {
                    response.writeHead(500, {"Content-Type": "text/plain"});
                    response.write(err + "\n");
                    response.end();
                    return;
                }

                response.writeHead(200);
                response.write(file, "binary");
                response.end();
            });
        });
    });
}

if (require.main === module) {
    var port = parseInt(process.argv[2] || "8000");
    var server = getServer("./result");
    server.listen(8000);
    server.on("listening", err => {
        if (err) {
            throw err;
        }

        console.log("HTTP server listening on " + port);
    });
}
