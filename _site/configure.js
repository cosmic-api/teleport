var path = require("path");
var fs = require("fs");
var builder = require("./builder/builder");
var glob = require("glob");
var bin = "node_modules/.bin";


var pythonBuildVenv = builder.pythonVenv("3.5");

var bootstrap = new builder.BuildTarget({
    resultDir: "/dist",
    archive: 'bootstrap-modified',
    mounts: {
        "/": builder.zipFileDownload(
            "bootstrap-dist",
            "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip"),
        "/fonts": builder.googleFonts("http://fonts.googleapis.com/css?family=Lato:400,700,400italic|Inconsolata:400,700"),
        "/lumen": builder.fileDownload(
            "bootstrap-lumen.css",
            "http://bootswatch.com/flatly/bootstrap.css"),
        "/highlight": builder.localNpmPackage("highlight.js"),
        "/awesome": builder.zipFileDownload(
            "font-awesome",
            "http://fortawesome.github.io/Font-Awesome/assets/font-awesome-4.5.0.zip")
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
    archive: 'site',
    staticDeps: [
        "_site/static",
        "_site/index.js",
        "_site/inject.js",
        "_site/templates/index.mustache",
        "_site/templates/navbar.mustache"
    ],
    mounts: {
        "/static/bootstrap": bootstrap,
        "/python/0.4": builder.inject(
            builder.pythonDocs("0.4", pythonBuildVenv),
            "--navbar 'python/0.4' --bs"),
        "/python/0.3": builder.inject(
            builder.pythonDocs("0.3", pythonBuildVenv),
            "--navbar 'python/0.3' --bs"),
        "/python/0.2": builder.inject(
            builder.pythonDocs("0.2", pythonBuildVenv),
            "--navbar 'python/0.2' --bs"),
        "/spec/draft-00": builder.inject(
            builder.formatSpec("draft-00"),
            "--navbar 'spec/draft-00' --bs"),
        "/spec/draft-01": builder.inject(
            builder.formatSpec("draft-01"),
            "--navbar 'spec/draft-01' --bs"),
        "/spec/draft-02": builder.inject(
            builder.formatSpec("draft-02"),
            "--navbar 'spec/draft-02' --bs"),
        "/spec/draft-03": builder.inject(
            builder.formatSpec("draft-03"),
            "--navbar 'spec/draft-03' --bs"),
        "/spec/draft-04": builder.inject(
            builder.formatSpec("draft-04"),
            "--navbar 'spec/draft-04' --bs"),
        "/spec/1.0": builder.inject(
            builder.zipFile("spec-old", "_site/archive/spec-old.zip"),
            "--navbar 'spec/1.0' --bs"),
        "/npm-jquery": builder.localNpmPackage("jquery")
    },

    getCommands: function (tmp) {
        return `
            cp -R _site/static ${tmp}
            cp ${tmp}/npm-jquery/dist/jquery* ${tmp}/static
            rm -rf ${tmp}/npm-jquery
            node _site/index.js > ${tmp}/index.html
            node _site/inject.js ${tmp}/index.html --navbar '/' --bs --highlight
        `;
    }
});

var siteGA = builder.inject(site, "--analytics");

var siteDist = builder.dist('site', site);
var siteDistGA = builder.dist('site-ga', siteGA);

var rootDir = path.join(__dirname, "..");
var makefile = new builder.Makefile(rootDir);

makefile.addRule(siteDist);
makefile.addRule(siteDistGA);

makefile.addTask("clean", "rm -rf build/*");
makefile.addTask(
    "deploy",
    `${bin}/surge --project ${siteDistGA.getFilename()} --domain www.teleport-json.org`
);

if (require.main === module) {
    fs.writeFileSync(`${rootDir}/Makefile`, makefile.toString())
}

module.exports = {
    makefile: makefile
};
