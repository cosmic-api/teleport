"use strict";

var _ = require("underscore");
var os = require("os");
var fs = require("fs");
var util = require("util");
var crypto = require("crypto");

var normalizeCommands = function (commands) {
    if (util.isArray(commands)) {
        return commands;
    } else {
        var lines = (commands.split("\n").map(line => {
            return line.trim();
        }));

        return _.filter(lines, function (line) {
            return line !== "";
        });
    }
};

var archiveFile = function (name) {
    return `.cache/${name}.tar`;
};

class Makefile {
    constructor(rootDir) {
        this.rootDir = rootDir;
        this.targets = {};
        this.tasks = {};
        this.dag = {};
    }

    writeMakefileSync() {
        return fs.writeFileSync(`${this.rootDir}/Makefile`, this.toString());
    }

    addRule(target) {
        if (this.targets[target.filename]) {
            return;
        }

        this.targets[target.filename] = target;
        this.dag[target.filename] = target.deps;

        return (() => {
            for (let depRule of target.depRules) {
                this.addRule(depRule);
            }
        })();
    }

    gatherDeps(node) {
        (node.filename != null ? node = node.filename : undefined);
        var nodes = [];

        var gatherDeps = node => {
            if (nodes.indexOf(node) != -1) {
                return;
            }

            return (() => {
                for (let dep of this.dag[node]) {
                    if (nodes.indexOf(dep) != -1) {
                        continue;
                    }

                    (this.dag[dep] != null ? gatherDeps(dep) : nodes.push(dep));
                }
            })();
        };

        gatherDeps(node);
        return nodes;
    }

    addTask(name, commands) {
        commands = normalizeCommands(commands);
        return this.tasks[name] = ((name) + ":\n\t" + (commands.join("\n\t")));
    }

    toString() {
        var taskNames = _.keys(this.tasks);
        taskNames.sort();
        var s = (".PHONY: " + (taskNames.join(" ")) + "\n\n");

        for (let name of taskNames) {
            s += this.tasks[name] + "\n\n";
        }

        var targetNames = _.keys(this.targets);
        targetNames.sort();

        for (let name of targetNames) {
            s += this.targets[name].stringify() + "\n\n";
        }

        return s;
    }
}

class Rule {
    constructor(opts) {

        this.filename = opts.filename;
        this.archive = opts.archive;
        var deps = opts.deps;
        var commands = opts.commands;

        if (!(this.filename != null)) {
            if (this.archive != null) {
                this.filename = archiveFile(this.archive);
            } else {
                console.log(opts);
                throw "Either filename or archive need to be specified";
            }
        }

        this.commands = normalizeCommands(commands);
        (!(deps != null) ? deps = [] : undefined);
        this.deps = [];
        this.depRules = [];

        for (let dep of deps) {
            if (dep.filename != null) {
                this.depRules.push(dep);
                this.deps.push(dep.filename);
            } else {
                this.deps.push(dep);
            }
        }
    }

    stringify() {
        this.deps.sort();
        var s = this.filename + ": ";
        s += this.deps.join(' ') + "\n\t";
        s += this.commands.join("\n\t");
        return s;
    }
}

var tarFile = function (options) {

    var archive = options.archive;
    var deps = options.deps || [];
    var resultDir = options.resultDir || "/";
    var getCommands = options.getCommands;
    var mounts = options.mounts || [];

    var tmp = os.tmpdir() + "/oxg/" + crypto.randomBytes(8).toString("hex");
    var mountLines = [];

    var filename, source;
    for (let root of Object.keys(mounts)) {
        source = mounts[root];

        if (source.filename) {
            filename = source.filename;
            deps.push(source);
        } else {
            filename = archiveFile(source);
            deps.push(filename);
        }

        mountLines.push("mkdir -p " + (tmp) + (root));
        mountLines.push("tar xf " + (filename) + " -C " + (tmp) + (root));
    }

    return new Rule({
        archive: archive,
        deps: deps,

        commands: [`rm -rf ${tmp}`, `mkdir -p ${tmp}`]
            .concat(mountLines)
            .concat(normalizeCommands(getCommands(tmp)))
            .concat([`mkdir -p .cache && tar cf ${archiveFile(archive)} -C ${tmp}${resultDir} .`])
    });
};

var gitCheckout = function (name, refFile) {
    var archive = ("checkouts-" + (name));

    return new Rule({
        archive: archive,
        deps: [refFile],
        commands: [`git --git-dir .git archive $(shell cat ${refFile}) > ${archiveFile(archive)}`]
    });
};

var gitCheckoutBranch = function (branch) {
    return gitCheckout(branch, `.git/refs/heads/${branch}`);
};

var gitCheckoutTag = function (tag) {
    return gitCheckout(tag, `.git/refs/tags/${tag}`);
};

var workingTree = function (options) {
    var name = options.name;
    var deps = options.deps;

    return new Rule({
        archive: name,
        deps: deps,
        commands: `
        git ls-files -o -i --exclude-standard > /tmp/excludes
        rm -f ${archiveFile(name)}
        # We are excluding  so tar doesn't complain about recursion
        tar cf ${archiveFile(name)} --exclude .git --exclude ${archiveFile(name)} --exclude-from=/tmp/excludes .
        `
    });
};

var googleFonts = function (googleUrl) {
    return tarFile({
        archive: "fonts",
        resultDir: "/out",

        getCommands: function (tmp) {
            return `
            wget -O ${tmp}/index.css "${googleUrl}"
            cat ${tmp}/index.css | grep -o -e "http.*ttf" > ${tmp}/download.list
            (cd ${tmp} && wget -i download.list)
            mkdir ${tmp}/out
            cp ${tmp}/*.ttf ${tmp}/out
            sed 's/http.*\\/\\(.*\\.ttf\\)/\"..\\/fonts\\/\\1\"/g' < ${tmp}/index.css > ${tmp}/out/index.css
            `;
        }
    });
};

var fileDownload = function (options) {
    var filename = options.filename;
    var url = options.url;

    return tarFile({
        archive: `download-${filename}`,
        getCommands: function (tmp) {
            return `wget -O ${tmp}/${filename} "${url}"`;
        }
    });
};

var tarFromZip = function (options) {
    var name = options.name;
    var url = options.url;

    return tarFile({
        archive: name,
        resultDir: "/out",

        getCommands: function (tmp) {
            return `
            wget ${url} -O ${tmp}/src-${name}.zip
            mkdir ${tmp}/out
            unzip ${tmp}/src-${name}.zip -d ${tmp}/out
            `;
        }
    });
};

var localNpmPackage = function (name) {
    return tarFile({
        archive: `npm-${name}`,
        deps: [`node_modules/${name}/package.json`],

        getCommands: function (tmp) {
            return `cp -R node_modules/${name}/* ${tmp}`;
        }
    });
};

module.exports = {
    normalizeCommands: normalizeCommands,
    archiveFile: archiveFile,
    Makefile: Makefile,
    Rule: Rule,
    tarFile: tarFile,
    workingTree: workingTree,
    gitCheckout: gitCheckout,
    gitCheckoutBranch: gitCheckoutBranch,
    gitCheckoutTag: gitCheckoutTag,
    tarFromZip: tarFromZip,
    googleFonts: googleFonts,
    fileDownload: fileDownload,
    localNpmPackage: localNpmPackage
};