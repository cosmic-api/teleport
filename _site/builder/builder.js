"use strict";

var os = require("os");
var fs = require("fs");
var glob = require("glob");
var crypto = require("crypto");



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
            let target = this.targets[name];
            let commands = target.getCommands(this.rootDir);
            if (commands.length > 0) {
                s += target.getFilename() + ": ";
                s += target.getStringDeps().join(' ') + "\n\t";
                s += "mkdir -p build\n\t";
                s += target.getCommands(this.rootDir).join("\n\t");
                s += "\n";
            }

            s += "\n"
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

    getStringDeps() {
        const stringDeps = [].concat(this.getStaticDeps());
        for (let depRule of this.getDeps()) {
            stringDeps.push(depRule.getFilename());
        }
        stringDeps.sort();
        return stringDeps;
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

    getFilename() {
        var archive = this.options.archive;
        return `build/${archive}.zip`;
    }

    getMounts() {
        return this.options.mounts || {};
    }

    getCommands(rootDir) {
        var resultDir = this.options.resultDir || "/";
        var mounts = this.getMounts();
        var filename = this.getFilename();

        var tmp = `build/${this.options.archive}`;
        var commands = [
            `rm -rf ${tmp}`,
            `mkdir -p ${tmp}`
        ];

        for (let root of Object.keys(mounts)) {
            commands.push(`mkdir -p ${tmp}${root}`);
            commands.push(`unzip -q ${mounts[root].getFilename()} -d ${tmp}${root}`);
        }
        commands = commands.concat(normalizeCommands(this.options.getCommands(tmp)));
        commands.push(`(cd ${tmp}${resultDir}; zip -q -r ${rootDir}/${filename} .)`);
        commands.push(`rm -rf ${tmp}`);
        return commands;
    }
}

var googleFonts = function (googleUrl) {
    return new BuildTarget({
        resultDir: "/out",
        archive: 'google-fonts',
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

var zipFileDownload = function (archive, url) {
    return new Target({
        filename: `build/${archive}.zip`,
        commands: [`wget -O build/${archive}.zip "${url}"`]
    });
};

var fileDownload = function (filename, url) {
    return new BuildTarget({
        archive: `download-${filename}`,
        getCommands: function (tmp) {
            return `wget -O ${tmp}/${filename} "${url}"`;
        }
    });
};

var zipFile = function (archive, filename) {
    return new Target({
        filename: filename,
        archive: archive,
        staticDeps: [],
        commands: []
    });
};

var pythonVenv = function (version) {
    return new BuildTarget({
        archive: `venv-${version}`,
        getCommands: function (tmp) {
            return `
                python${version} -m venv --without-pip ${tmp}
                wget https://bootstrap.pypa.io/get-pip.py -P ${tmp}
                ${tmp}/bin/python ${tmp}/get-pip.py
                ${tmp}/bin/pip install sphinx
            `;
        }
    });
};

var pythonDocs = function (version, venv) {
    var staticDeps = glob.sync(`python/${version}/docs/**`);
    staticDeps = staticDeps.concat(glob.sync(`python/${version}/teleport/**`));
    staticDeps = staticDeps.concat(`python/${version}/CHANGES.rst`);

    return new BuildTarget({
        resultDir: "/python/out",
        staticDeps: staticDeps,
        archive: `docs-python-${version}`,
        mounts: {
            "/flask-sphinx-themes": zipFileDownload(
                "flask-sphinx-themes.zip",
                "https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip"),
            "/intersphinx/python2": fileDownload(
                "python2.inv",
                "https://docs.python.org/2.7/objects.inv"),
            "/venv": venv
        },
        getCommands: function (tmp) {
            return `
                cp -R python/${version} ${tmp}/python
                cp ${tmp}/intersphinx/python2/python2.inv ${tmp}/python/docs
                echo '\\nhtml_theme_path = ["../../flask-sphinx-themes/flask-sphinx-themes-master"]\\n' >> ${tmp}/python/docs/conf.py
                echo '\\nintersphinx_mapping = {"python": ("http://docs.python.org/2.7", "python2.inv")}\\n' >> ${tmp}/python/docs/conf.py
                (cd ${tmp}/python; ../venv/bin/python setup.py install)
                (cd ${tmp}/python; ../venv/bin/python ../venv/bin/sphinx-build -b html -D html_theme=flask docs out)
            `;
        }
    });
};

var formatSpec = function (version) {
    return new BuildTarget({
        archive: `spec-${version}`,
        staticDeps: [
            "_site/spec.js",
            "_site/templates/spec.mustache",
            `_spec/${version}.xml`
        ],
        resultDir: "/out",
        getCommands: function (tmp) {
            return `
                xml2rfc --no-network _spec/${version}.xml --text --out=${tmp}/teleport.txt
                mkdir ${tmp}/out
                node _site/spec.js < ${tmp}/teleport.txt > ${tmp}/out/index.html
            `;
        }
    });
};

var inject = function (source, args) {
    if (!source.options.archive) {
        console.log(source);
    }
    return new BuildTarget({
        archive: `${source.options.archive}-inject`,
        staticDeps: ["_site/inject.js", "_site/templates/navbar.mustache"],
        mounts: {
            "/": source
        },
        getCommands: function (tmp) {
            return `find ${tmp} -iname \\*.html | xargs node _site/inject.js ${args}`;
        }
    });
};

var localNpmPackage = function (name) {
    return new BuildTarget({
        archive: `npm-${name}`,
        staticDeps: [`node_modules/${name}/package.json`],
        getCommands: function (tmp) {
            return `cp -R node_modules/${name}/* ${tmp}`;
        }
    });
};

var dist = function(name, src) {
    var distDir = `dist/${name}`;
    return new Target({
        filename: distDir,
        deps: [src],
        commands: normalizeCommands(`
            rm -rf ${distDir}
            mkdir -p ${distDir}
            tar xf ${src.getFilename()} -C ${distDir}
        `)
    });
};


module.exports = {
    normalizeCommands: normalizeCommands,
    Makefile: Makefile,
    Target: Target,
    BuildTarget: BuildTarget,
    googleFonts: googleFonts,
    fileDownload: fileDownload,
    zipFile: zipFile,
    zipFileDownload: zipFileDownload,
    localNpmPackage: localNpmPackage,
    pythonVenv: pythonVenv,
    pythonDocs: pythonDocs,
    formatSpec: formatSpec,
    inject: inject,
    dist: dist
};