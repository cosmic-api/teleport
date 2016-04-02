"use strict";

var fs = require("fs");
var url = require("url");
var mime = require("mime");
var cheerio = require("cheerio");
var AdmZip = require('adm-zip');
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
        this.tarball = options.tarball;
        this.port = options.port;
        this.lrport = options.lrport;
        this.objects = null;
    }

    loadArchive() {
        this.objects = loadZip(this.tarball);
    }

    run() {
        this.lrserver = tinylr();

        this.lrserver.listen(this.lrport, () => {
            print(`LiveReload running on ${this.lrport} ...`);
            return this.emit("lr-listening");
        });

        var app = connect();

        app.use((req, res, next) => {
            var mimetype;
            var relativePath = url.parse(req.url).pathname.substr(1);
            var body;

            var maybeFile = this.objects[relativePath];
            if (!maybeFile) {
                relativePath += 'index.html';
                mimetype = 'text/html';
                maybeFile = this.objects[relativePath];
            }

            const status = maybeFile ? 200 : 404;
            print2(`${status} ${relativePath}`);

            if (!maybeFile) {
                res.writeHead(status);
                return res.end();

            } else {
                if (!mimetype) {
                    mimetype = mime.lookup(relativePath);
                }
                if (mimetype === "text/html") {
                    body = this.processHtml(maybeFile);
                } else {
                    body = maybeFile;
                }

                res.writeHead(status, {
                    "Content-Type": mimetype,
                    "Cache-Control": "max-age=0, no-cache, no-store"
                });
                res.write(body);
                return res.end();
            }
        });

        this.server = http.createServer(app).listen(this.port);

        return this.server.on("listening", err => {
            if (err) {
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
            "<script type=\\\"text/javascript\\\" src=\\\"http://127.0.0.1:" + (this.lrport) + "/livereload.js\\\"></script>"
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

        for (let file of this.files) {
            print2(file);
        }
    }

    watch() {
        if (this.watcher) this.watcher.close();

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
        this.distDir = options.distDir;
        var port = options.port || 8000;
        var lrport = options.lrport || 35729;
        var distTarget = this.makefile.targets[this.distDir];
        var previousTarget = distTarget.getDeps()[0];
        var deps = previousTarget.getStringDepsRecursive();
        deps.sort();
        this.watcher = new Watcher(deps);

        this.server = new Server({
            tarball: previousTarget.getFilename(),
            port: port,
            lrport: lrport
        });
    }

    bootstrap(callback) {
        var firstBuild = new Builder(this.makefile, this.distDir);
        firstBuild.build();
        firstBuild.on("done", () => {
            this.server.loadArchive();
            this.server.run();
            this.server.once("loaded", () => {
                this.watcher.watch();
                this.watcher.announce();
                return callback();
            });
        });
    }

    loop() {
        var builder = new Builder(this.makefile, this.tarball);

        return this.watcher.on("kabam", filename => {
            builder.removeAllListeners("done");

            builder.once("done", () => {
                this.server.loadArchive();
                this.server.once("loaded", this.server.triggerReload);
            });

            return builder.build();
        });
    }

    run() {
        this.bootstrap(() => {
            this.loop();
        });
    }
}

var loadZip = function (file) {

    var objects = {};
    var zip = new AdmZip('./' + file);

    for (let entry of zip.getEntries()) {
        let data = entry.getData();
        if (!entry.isDirectory && data) {
            objects[entry.entryName] = data
        }
    }
    print(`loaded ${Object.keys(objects).length} objects from ${file} into memory`);
    return objects;
};

module.exports = {
    print: print,
    print2: print2,
    loadTar: loadZip,
    Server: Server,
    Watcher: Watcher,
    Builder: Builder,
    LiveAgent: LiveAgent
};