var fs = require("fs");
var marked = require("marked");
var mustache = require("mustache");

var render = function (file, context) {
    var raw = fs.readFileSync(((__dirname) + "/templates/" + (file))).toString();
    return mustache.render(raw, context);
};

var txt = "";
process.stdin.resume();
process.stdin.setEncoding("utf-8");

process.stdin.on("data", function (buf) {
    return txt += buf;
});

process.stdin.on("end", function () {
    var pageStuffMode = null;
    var titleMode = null;
    var spec = "";

    for (let line of txt.split("\\n")) {
        if (pageStuffMode !== false) {
            if (line === "") {
                (pageStuffMode === true ? pageStuffMode = false : undefined);
            } else {
                (/^Internet Engineering Task Force/.test(line) ? pageStuffMode = true : undefined);
                line = ("<span class='page-stuff'>" + (line) + "</span>");
            }
        } else if (pageStuffMode === false && titleMode !== false) {
            if (line === "") {
                (titleMode === true ? titleMode = false : undefined);
            } else {
                titleMode = true;
                line = ("<span class='title'>" + (line) + "</span>");
            }
        } else if (titleMode === false) {
            var longLine = /^\S.*$/.test(line);

            if (longLine) {
                (/^Boronine.*$/.test(line) || /^Internet.*2014$/.test(line) ? line = ("<span class='page-stuff'>" + (line) + "</span>") : line = ("<span class='title'>" + (line) + "</span>"));
            }
        }

        spec += line + "\\n";
    }

    return console.log(render("spec.mustache", {
        body: `<pre class='rfc'>${spec}</pre>`
    }));
});