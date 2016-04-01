var parseArgs = require("minimist");

var configure = require("./configure");
var live = require("./builder/live");


var main = function () {
    var argv = parseArgs(process.argv.slice(2));

    if (argv._.length === 0) {
        throw "missing argument";
    }

    var distDir = argv._[0];

    var agent = new live.LiveAgent({
        makefile: configure.makefile,
        distDir: distDir
    });

    return agent.run();
};

if (require.main === module) {
    main();
}
