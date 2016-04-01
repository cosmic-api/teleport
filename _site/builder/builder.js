"use strict";

var os = require("os");
var fs = require("fs");
var crypto = require("crypto");


var stringHash = function (str) {
    var hash = 5381;
    var i = str.length;
    while (i) {
        hash = (hash * 33) ^ str.charCodeAt(--i);
    }
    hash = hash >>> 0;
    return ("00000000" + hash.toString(8)).substr(-8);
};


var normalizeCommands = function (commands) {
    if (Array.isArray(commands)) {
        return commands;
    } else {
        var lines = [];
        for (var rawLine of commands.split('\n')) {
            rawLine = rawLine.trim();
            if (rawLine !== "") {
                lines.push(rawLine);
            }
        }
        return lines;
    }
};

class Makefile {
    constructor(rootDir) {
        this.rootDir = rootDir;
        this.targets = {};
        this.tasks = {};
    }

    writeMakefileSync() {
        return fs.writeFileSync(`${this.rootDir}/Makefile`, this.toString());
    }

    addRule(target) {
        var filename = target.getFilename();
        if (this.targets[filename]) {
            return;
        }
        this.targets[filename] = target;
        for (let dep of target.getDeps()) {
            this.addRule(dep);
        }
    }

    addTask(name, commands) {
        commands = normalizeCommands(commands);
        this.tasks[name] = name + ":\n\t" + commands.join("\n\t");
    }

    toString() {
        var taskNames = Object.keys(this.tasks);
        taskNames.sort();
        var s = ".PHONY: " + taskNames.join(" ") + "\n\n";

        for (let name of taskNames) {
            s += this.tasks[name] + "\n\n";
        }

        var targetNames = Object.keys(this.targets);
        targetNames.sort();

        for (let name of targetNames) {
            s += this.targets[name].stringify() + "\n\n";
        }

        return s;
    }
}

class Target {
    constructor(options) {
        this.options = options;
    }

    getFilename() {
        return this.options.filename;
    }

    getCommands() {
        return this.options.commands || [];
    }

    getDeps() {
        return this.options.deps || [];
    }

    getStaticDeps() {
        return this.options.staticDeps || [];
    }

    getStringDepsRecursive() {
        var allDeps = new Set(this.getStaticDeps());
        for (let dep of this.getDeps()) {
            allDeps.add(dep.getFilename());
            for (let subDep of dep.getStringDepsRecursive()) {
                allDeps.add(subDep);
            }
        }
        return Array.from(allDeps);
    }

    stringify() {
        const stringDeps = [].concat(this.getStaticDeps());
        for (let depRule of this.getDeps()) {
            stringDeps.push(depRule.getFilename());
        }
        stringDeps.sort();

        var s = this.getFilename() + ": ";
        s += stringDeps.join(' ') + "\n\t";
        s += this.getCommands().join("\n\t");
        return s;
    }
}

class Dist extends Target {
    constructor(name, src) {
        var distDir = `dist/${name}`;
        super({
            filename: distDir,
            deps: [src],
            commands: normalizeCommands(`
                rm -rf ${distDir}
                mkdir -p ${distDir}
                tar xf ${src.getFilename()} -C ${distDir}
            `)
        });
    }
}

class BuildTarget extends Target {

    getDeps() {
        var mounts = this.getMounts();
        var allDeps = [].concat(super.getDeps());
        for (let k of Object.keys(mounts)) {
            allDeps.push(mounts[k]);
        }
        return allDeps;
    }

    getHash() {
        var salt = this.options.salt || '';
        var allDeps = this.getStringDepsRecursive();
        allDeps.sort();
        return stringHash(allDeps.join(' ') + salt);
    }

    getFilename() {
        return `build/${this.getHash()}.tar`;
    }

    getMounts() {
        return this.options.mounts || {};
    }

    getCommands() {
        var resultDir = this.options.resultDir || "/";
        var mounts = this.getMounts();
        var filename = this.getFilename();

        var tmp = `build/${this.getHash()}`;
        var commands = [
            `rm -rf ${tmp}`,
            `mkdir -p ${tmp}`
        ];

        for (let root of Object.keys(mounts)) {
            commands.push(`mkdir -p ${tmp}${root}`);
            commands.push(`tar xf ${mounts[root].getFilename()} -C ${tmp}${root}`);
        }
        commands = commands.concat(normalizeCommands(this.options.getCommands(tmp)));
        commands.push(`tar cf ${filename} -C ${tmp}${resultDir} .`);
        commands.push(`rm -rf ${tmp}`);
        return commands;
    }
}

var googleFonts = function (googleUrl) {
    return new BuildTarget({
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

    return new BuildTarget({
        salt: url,
        getCommands: function (tmp) {
            return `wget -O ${tmp}/${filename} "${url}"`;
        }
    });
};

var tarFromZip = function (url) {
    return new BuildTarget({
        resultDir: "/out",
        salt: url,
        getCommands: function (tmp) {
            return `
            wget ${url} -O ${tmp}/temp.zip
            mkdir ${tmp}/out
            unzip ${tmp}/temp.zip -d ${tmp}/out
            `;
        }
    });
};

module.exports = {
    normalizeCommands: normalizeCommands,
    Makefile: Makefile,
    Target: Target,
    Dist: Dist,
    BuildTarget: BuildTarget,
    tarFromZip: tarFromZip,
    googleFonts: googleFonts,
    fileDownload: fileDownload
};