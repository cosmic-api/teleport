var fs = require("fs");
var mustache = require("mustache");

var render = function (file, context) {
    var raw = fs.readFileSync(`${__dirname}/templates/${file}`).toString();
    return mustache.render(raw, context);
};

console.log(render("index.mustache"));