"use strict";

var fs = require("fs");
var mustache = require("mustache");
var parseArgs = require("minimist");
var hljs = require("highlight.js");
var cheerio = require("cheerio");
var navbarTemplate = fs.readFileSync(`${__dirname}/templates/navbar.mustache`).toString();

var main = function () {
    var argv = parseArgs(process.argv.slice(2), {
        string: ["navbar"],
        boolean: ["bs", "highlight", "analytics"]
    });

    if (argv._.length === 0) {
        console.log("No input files, doing nothing");
        return;
    }

    console.log(`Injecting ${argv._.length} file(s)`);

    for (let filename of argv._) {
        injectFile(filename, argv);
    }
};

var injectFile = function (filename, options) {
    return fs.readFile(filename, function (err, buf) {
        if (err) {
            throw err;
        }

        var injectedHtml = inject(buf.toString(), options);

        return fs.writeFile(filename, injectedHtml, function (err) {
            if (err) {
                throw err;
            }

            return console.log(" * injected " + (filename));
        });
    });
};

var inject = function (html, options) {
    var navbar = options.navbar;
    var bs = options.bs;
    var highlight = options.highlight;
    var analytics = options.analytics;

    var $ = cheerio.load(html);

    if (bs) {
        $("script").each(function () {
            var src = $(this).attr("src");
            if (src != null && new RegExp("jquery(\\.min)?\\.js").test(src)) {
                $(this).remove();
            }
        });

        $("head").prepend('<script type="text/javascript" src="/static/jquery.min.js"></script>');

        $("head").append(`
            <script type="text/javascript" src="/static/bootstrap/js/bootstrap.min.js"></script>
            <link rel="stylesheet" href="/static/bootstrap/css/bootstrap.min.css" type="text/css"/>
            <link rel="icon" href="/static/favicon-32.png" sizes="32x32">
            <link rel="apple-touch-icon-precomposed" href="/static/favicon-152.png">
        `);
    }

    if (analytics) {
        $("head").append(`
            <script type="text/javascript">
                (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
                (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
                m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
                })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
                ga('create', 'UA-12144432-3', 'auto');
                ga('send', 'pageview');
            </script>
        `);
    }

    if (highlight) {
        $("pre.highlight-please").each(function () {
            if ($(this).hasClass("python")) {
                var $code = $("<code>");
                $code.addClass("hljs python");
                $code.html(hljs.highlight("python", $(this).text()).value);
                $(this).html("");
                return $(this).append($code);
            }
        });

        $("pre.highlight-please").removeClass("highlight-please");
    }
    if (navbar != null) {
        $("body").prepend(renderNavbar(navbar));
    }

    return $.html();
};

var renderNavbar = function (path) {
    var sec, ver, p;
    if (path === "/") {
        sec = "home";
    } else {
        p = path.split("/");
        sec = p[0];
        ver = p[1];
    }

    var sections = {
        home: {
            star: true,
            repoLink: true,
            subMenuShow: false
        },

        python: {
            star: false,
            repoLink: true,
            subMenuShow: true,

            subMenu: [
                // { version: "0.5" },
                { version: "0.4" },
                { version: "0.3" },
                { version: "0.2" }
            ]
        },

        spec: {
            star: false,
            repoLink: true,
            subMenuShow: true,

            subMenu: [
                { version: "draft-04" },
                { version: "draft-03" },
                { version: "draft-02" },
                { version: "draft-01" },
                { version: "draft-00" },
                { divider: true },
                { version: "1.0" }
            ]
        }
    };

    return mustache.render(navbarTemplate, {
        menu: {
            about: sec === "home",
            docs: sec === "python",
            spec: sec === "spec"
        },

        activeSectionId: sec,
        activeSection: sections[sec],
        activeVersion: ver,
        latestSpec: sections.spec.subMenu[0].version,
        latestPython: sections.python.subMenu[0].version
    });
};

main();