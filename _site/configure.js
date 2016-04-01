var path = require("path");
var fs = require("fs");
var os = require("os");
var builder = require("./builder/builder");
var glob = require("glob");
var nodeExec = "node";
var bin = "node_modules/.bin";


var copyFromArchive = function (name) {
    var source = `_site/archive/${name}.tar`;
    var archive = `archive-${name}`;
    var filename = `build/${name}`;

    return new builder.Target({
        filename: filename,
        staticDeps: [source],
        commands: [
            `mkdir -p build`,
            `cp -R ${source} ${filename}`
        ]
    });
};

var pythonBuildVenv = new builder.BuildTarget({
    salt: 'virtualenv',
    getCommands: function (tmp) {
        return `
            python3 -m venv --without-pip ${tmp}
            wget https://bootstrap.pypa.io/get-pip.py -P ${tmp}
            ${tmp}/bin/python ${tmp}/get-pip.py
            ${tmp}/bin/pip install sphinx
        `;
    }
});

var pythonDocs = function (version) {
    var staticDeps = glob.sync(`python/${version}/docs/**`);
    staticDeps = staticDeps.concat(glob.sync(`python/${version}/teleport/**`));
    staticDeps = staticDeps.concat(`python/${version}/CHANGES.rst`);

    return new builder.BuildTarget({
        resultDir: "/python/out",
        staticDeps: staticDeps,
        mounts: {
            "/flask-sphinx-themes": builder.tarFromZip("https://github.com/cosmic-api/flask-sphinx-themes/archive/master.zip"),
            "/intersphinx/python2": builder.fileDownload({
                filename: "python2.inv",
                url: "https://docs.python.org/2.7/objects.inv"
            }),
            "/venv": pythonBuildVenv
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

var formatSpec = function (source) {
    return new builder.BuildTarget({
        staticDeps: [
            "_site/spec.js",
            "_site/templates/spec.mustache",
            `_spec/${source}.xml`
        ],
        resultDir: "/out",
        getCommands: function (tmp) {
            return `
                xml2rfc --no-network _spec/${source}.xml --text --out=${tmp}/teleport.txt
                mkdir ${tmp}/out
                ${nodeExec} _site/spec.js < ${tmp}/teleport.txt > ${tmp}/out/index.html
            `;
        }
    });
};

var inject = function (options) {
    var src = options.src;
    var args = options.args;
    return new builder.BuildTarget({
        staticDeps: ["_site/inject.js", "_site/templates/navbar.mustache"],
        mounts: {
            "/": src
        },
        getCommands: function (tmp) {
            return `find ${tmp} -iname \\*.html | xargs ${nodeExec} _site/inject.js ${args}`;
        }
    });
};

var rootDir = path.join(__dirname, "..");
var makefile = new builder.Makefile(rootDir);
var deployTmp = "dist";

makefile.addTask(
    "deploy",
    `
        rm -rf ${deployTmp}
        mkdir -p ${deployTmp}
        tar xf build/site.tar -C ${deployTmp}
        ${bin}/surge --project ./dist --domain www.teleport-json.org
    `
);

makefile.addTask("clean", "rm -rf build/*");

var localNpmPackage = function (name) {
    return new builder.BuildTarget({
        staticDeps: [`node_modules/${name}/package.json`],
        getCommands: function (tmp) {
            return `cp -R node_modules/${name}/* ${tmp}`;
        }
    });
};

var bootstrap = new builder.BuildTarget({
    resultDir: "/dist",
    mounts: {
        "/": builder.tarFromZip("https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip"),
        "/fonts": builder.googleFonts("http://fonts.googleapis.com/css?family=Lato:400,700,400italic|Inconsolata:400,700"),
        "/lumen": builder.fileDownload({
            filename: "bootstrap-lumen.css",
            url: "http://bootswatch.com/flatly/bootstrap.css"
        }),
        "/highlight": localNpmPackage("highlight.js"),
        "/awesome": builder.tarFromZip("http://fortawesome.github.io/Font-Awesome/assets/font-awesome-4.5.0.zip")
    },
    staticDeps: ["_site/static/static.css"],
    getCommands: function (tmp) {
        return `
            # Concatenate CSS from multiple sources
            cp ${tmp}/lumen/bootstrap-lumen.css ${tmp}/everything.css
            cat ${tmp}/highlight/styles/default.css >> ${tmp}/everything.css
            cat _site/static/static.css >> ${tmp}/everything.css
            # Make the css safe to mix with other css
            ${bin}/namespace-css ${tmp}/everything.css -s .bs >> ${tmp}/everything-safe.css
            sed -i.bak 's/\\.bs\\ body/\\.bs,\\ \\.bs\\ body/g' ${tmp}/everything-safe.css
            # Remove google font API loads
            sed -i.bak '/googleapis/d' ${tmp}/everything-safe.css
            rm -r ${tmp}/dist/css/*
            # Fonts get prepended
            cp ${tmp}/fonts/index.css ${tmp}/dist/css/bootstrap.css
            cat ${tmp}/everything-safe.css >> ${tmp}/dist/css/bootstrap.css
            cat ${tmp}/awesome/font-awesome-4.5.0/css/font-awesome.css >> ${tmp}/dist/css/bootstrap.css
            ${bin}/cleancss ${tmp}/dist/css/bootstrap.css > ${tmp}/dist/css/bootstrap.min.css
            # Copy fonts
            mkdir -p ${tmp}/dist/fonts
            cp ${tmp}/fonts/*.ttf ${tmp}/dist/fonts
            cp ${tmp}/awesome/font-awesome-4.5.0/fonts/* ${tmp}/dist/fonts
        `;

    }
});

var site = new builder.BuildTarget({
    staticDeps: [
        "_site/static",
        "_site/index.js",
        "_site/templates/index.mustache",
        "_site/inject.js",
        "_site/templates/navbar.mustache"
    ],
    mounts: {
        "/static/bootstrap": bootstrap,

        // "/python/0.5": inject({
        //     src: pythonDocs("0.5"),
        //     args: "--navbar 'python/0.5' --bs"
        // }),

        "/python/0.4": inject({
            src: pythonDocs("0.4"),
            args: "--navbar 'python/0.4' --bs"
        }),

        "/python/0.3": inject({
            src: pythonDocs("0.3"),
            args: "--navbar 'python/0.3' --bs"
        }),

        "/python/0.2": inject({
            src: pythonDocs("0.2"),
            args: "--navbar 'python/0.2' --bs"
        }),

        "/spec/draft-00": inject({
            src: formatSpec("draft-00"),
            args: "--navbar 'spec/draft-00' --bs"
        }),

        "/spec/draft-01": inject({
            src: formatSpec("draft-01"),
            args: "--navbar 'spec/draft-01' --bs"
        }),

        "/spec/draft-02": inject({
            src: formatSpec("draft-02"),
            args: "--navbar 'spec/draft-02' --bs"
        }),

        "/spec/draft-03": inject({
            src: formatSpec("draft-03"),
            args: "--navbar 'spec/draft-03' --bs"
        }),

        "/spec/draft-04": inject({
            src: formatSpec("draft-04"),
            args: "--navbar 'spec/draft-04' --bs"
        }),

        "/spec/1.0": inject({
            src: copyFromArchive("spec-old"),
            args: "--navbar 'spec/1.0' --bs"
        }),

        "/npm-jquery": localNpmPackage("jquery")
    },

    getCommands: function (tmp) {
        return `
            cp -R _site/static ${tmp}
            cp ${tmp}/npm-jquery/dist/jquery* ${tmp}/static
            rm -rf ${tmp}/npm-jquery
            ${nodeExec} _site/index.js > ${tmp}/index.html
            ${nodeExec} _site/inject.js ${tmp}/index.html --navbar '/' --bs --highlight
        `;
    }
});

makefile.addRule(new builder.Dist('site', site));
makefile.addRule(new builder.Dist('site-ga', inject({
    src: site,
    args: "--analytics"
})));

if (require.main === module) {
    fs.writeFileSync(`${__dirname}/../Makefile`, makefile.toString())
}

module.exports = {
    makefile: makefile
};