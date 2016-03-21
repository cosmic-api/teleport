var parseArgs = require("minimist");

var makefile;
makefile = require("./configure").makefile;

var LiveAgent;
LiveAgent = require("./builder/live").LiveAgent;

var archiveFile;
archiveFile = require("./builder/builder").archiveFile;

var main = function () {
    var argv = parseArgs(process.argv.slice(2));

    if (argv._.length === 0) {
        throw "missing argument";
    }

    var archive = argv._[0];

    var agent = new LiveAgent({
        makefile: makefile,
        tarball: archiveFile(archive)
    });

    return agent.run();
};

if (require.main === module) {
    main();
}
