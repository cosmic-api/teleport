"use strict";

var fs = require("fs");
var url = require("url");
var mime = require("mime");
var cheerio = require("cheerio");
var tar = require("tar-stream");
var connect = require("connect");
var http = require("http");
var chokidar = require("chokidar");
var tinylr = require("tiny-lr");
var spawn = require("child_process").spawn;

var EventEmitter = require("events").EventEmitter;

var print = function () {
    return console.log("| .", ...arguments);
};

var print2 = function () {
    return console.log("|   .", ...arguments);
};

var hr = function () {
    return console.log("+-------------------------------");
};

class Server extends EventEmitter {
    constructor(options) {
        super();
        this.tarball = options.tarball, this.port = options.port, this.lrport = options.lrport, options;
        this.objects = null;
    }

    loadArchive() {
        print(("loading " + (this.tarball) + " into memory"));

        return loadTar(this.tarball, (err, objects) => {
            this.objects = objects;
            return this.emit("loaded");
        });
    }

    run() {
        this.lrserver = tinylr();

        this.lrserver.listen(this.lrport, () => {
            print(("LiveReload running on " + (this.lrport) + " ..."));
            return this.emit("lr-listening");
        });

        var app = connect();

        app.use((req, res, next) => {
            var mimetype;
            var path = "." + url.parse(req.url).pathname;
            var maybeFile = this.objects[path];

            if (maybeFile !== null && maybeFile !== undefined) {
                mimetype = mime.lookup(path);
            } else {
                maybeFile = this.objects[path + "index.html"];
                mimetype = "text/html";

                if (maybeFile === null || maybeFile === undefined) {
                    res.writeHead(404);
                    res.end();
                    return;
                }
            }

            var body = (mimetype === "text/html" ? this.processHtml(maybeFile) : maybeFile);

            var headers = {
                "Content-Type": mimetype,
                "Cache-Control": "max-age=0, no-cache, no-store"
            };

            res.writeHead(200, headers);
            res.write(body);
            return res.end();
        });

        this.server = http.createServer(app).listen(this.port);

        return this.server.on("listening", err => {
            if (typeof err !== "undefined" && err !== null) {
                throw err;
            }

            print(("HTTP server listening on " + (this.port)));
            return this.emit("server-listening");
        });
    }

    triggerReload(callback) {
        print("triggering reload");

        var req = http.request({
            hostname: "127.0.0.1",
            port: this.lrport,
            path: "/changed?files=*",
            method: "POST"
        });

        req.on("response", response => {
            var success = response.statusCode === 200;
            var data = "";

            response.on("data", chunk => {
                return data += chunk.toString();
            });

            return response.on("end", function () {
                data = JSON.parse(data);
                print2(((data.clients.length) + " client(s)"));

                if (typeof callback !== "undefined" && callback !== null) {
                    return (success ? callback(null) : callback(response));
                }
            });
        });

        return req.end();
    }

    processHtml(html) {
        var $ = cheerio.load(html, {
            decodeEntities: false
        });

        $("iframe").each(function () {
            return (new RegExp("ghbtns").test($(this).attr("src")) ? $(this).remove() : undefined);
        });

        $("body").append(
            ("<script type=\\\"text/javascript\\\" src=\\\"http://127.0.0.1:" + (this.lrport) + "/livereload.js\\\"></script>")
        );

        return $.html();
    }
}

class Watcher extends EventEmitter {
    constructor(files) {
        super();
        this.files = files;
    }

    announce() {
        print("watching files:");

        return (() => {
            for (let file of this.files) {
                print2(file);
            }
        })();
    }

    watch() {
        (this.watcher != null ? this.watcher.close() : undefined);

        this.watcher = chokidar.watch(this.files, {
            persistent: true
        });

        this.watcher.on("change", filename => {
            if (this.files.indexOf(filename) != -1) {
                return;
            }

            return this.emit("kabam", filename);
        });

        this.watcher.on("unlink", filename => {
            if (this.files.indexOf(filename) != -1) {
                return;
            }

            return this.emit("kabam", filename);
        });

        return this.watcher.on("error", function (err) {
            throw err;
        });
    }
}

class Builder extends EventEmitter {
    constructor(makefile, tarball) {
        super();
        this.makefile = makefile;
        this.tarball = tarball;
        this.building = false;
    }

    build() {
        if (this.building === true) {
            this.removeAllListeners("killed");

            this.once("killed", function () {
                this.building = false;
                return this.build();
            });

            this.kill();
            return;
        }

        this.building = true;
        print("generating Makefile");
        this.makefile.writeMakefileSync();
        print(("running 'make " + (this.tarball) + "'"));
        hr();
        (process.cwd() === this.makefile.rootDir ? this.make = spawn("make", [this.tarball]) : this.make = spawn("make", ["-C", this.makefile.rootDir, this.tarball]));
        this.make.stdout.pipe(process.stdout);
        this.make.stderr.pipe(process.stderr);

        return this.make.on("close", (code, signal) => {
            hr();

            if (code !== 0) {
                if (signal === "SIGTERM") {
                    print("make was killed by watcher");
                    this.building = false;
                    this.emit("killed");
                    return;
                } else {
                    print(("make returned " + (code)));
                    throw "fix the build before going live!";
                }
            }

            this.building = false;
            return this.emit("done");
        });
    }

    kill() {
        return this.make.kill("SIGTERM");
    }
}

class LiveAgent extends EventEmitter {
    constructor(options) {
        super();
        this.makefile = options.makefile;
        this.tarball = options.tarball;
        var port = options.port;
        var lrport = options.lrport;
        (!(port != null) ? port = 8000 : undefined);
        (!(lrport != null) ? lrport = 35729 : undefined);
        var deps = this.makefile.gatherDeps(this.tarball);
        deps.sort();
        this.watcher = new Watcher(deps);

        this.server = new Server({
            tarball: this.tarball,
            port: port,
            lrport: lrport
        });
    }

    bootstrap(callback) {
        var firstBuild = new Builder(this.makefile, this.tarball);
        firstBuild.build();

        return firstBuild.on("done", () => {
            this.server.once("loaded", () => {
                this.watcher.watch();
                this.server.run();
                this.watcher.announce();
                return callback();
            });

            return this.server.loadArchive();
        });
    }

    loop() {
        var builder = new Builder(this.makefile, this.tarball);

        return this.watcher.on("kabam", filename => {
            builder.removeAllListeners("done");

            builder.once("done", () => {
                this.server.once("loaded", this.server.triggerReload);
                return this.server.loadArchive();
            });

            return builder.build();
        });
    }

    run() {
        return this.bootstrap(() => {
            return this.loop();
        });
    }
}

var loadTar = function (file, next) {
    var objects = {};
    var extract = tar.extract();

    extract.on("entry", function (header, stream, callback) {
        if (header.type === "file") {
            var chunks = [];

            stream.on("data", function (chunk) {
                return chunks.push(chunk);
            });

            stream.on("end", function () {
                objects[header.name] = Buffer.concat(chunks);
                return callback();
            });

            return stream.resume();
        } else if (header.type === "directory") {
            objects[header.name] = null;
            return callback();
        }
    });

    extract.on("finish", function () {
        return next(null, objects);
    });

    return fs.createReadStream(file).pipe(extract);
};

module.exports = {
    print: print,
    print2: print2,
    loadTar: loadTar,
    Server: Server,
    Watcher: Watcher,
    Builder: Builder,
    LiveAgent: LiveAgent
};