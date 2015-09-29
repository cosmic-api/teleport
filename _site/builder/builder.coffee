_ = require 'underscore'
os = require 'os'
fs = require 'fs'
util = require 'util'
crypto = require 'crypto'


normalizeCommands = (commands) ->
  if util.isArray commands
    return commands
  else
    lines = (line.trim() for line in commands.split '\n')
    return _.filter lines, (line) -> line != ''

archiveFile = (name) ->
  ".cache/#{name}.tar"

class Makefile

  constructor: (@rootDir) ->
    @targets = {}
    @tasks = {}
    @dag = {}

  writeMakefileSync: ->
    fs.writeFileSync "#{@rootDir}/Makefile", @toString()

  addRule: (target) ->
    if target.filename in @targets
      return

    @targets[target.filename] = target
    @dag[target.filename] = target.deps

    for depRule in target.depRules
      @addRule depRule

  addRules: (targets) ->
    for target in targets
      @addRule target

  gatherDeps: (node) ->
    if node.filename?
      node = node.filename
    nodes = []

    gatherDeps = (node) =>
      return if node in nodes
      for dep in @dag[node]
        continue if dep in nodes
        if @dag[dep]?
          gatherDeps dep
        else
          nodes.push dep

    gatherDeps node
    return nodes

  addTask: (name, commands) ->
    commands = normalizeCommands commands
    @tasks[name] = "#{name}:\n\t#{commands.join('\n\t')}"

  toString: ->
    taskNames = _.keys @tasks
    taskNames.sort()
    s = ".PHONY: #{taskNames.join(' ')}\n\n"
    for name in taskNames
      s += @tasks[name] + "\n\n"
    targetNames = _.keys @targets
    targetNames.sort()
    for name in targetNames
      s += @targets[name].stringify() + "\n\n"
    return s



class Rule

  constructor: (opts) ->
    {@filename, @archive, deps, commands} = opts
    if not @filename?
      if @archive?
        @filename = archiveFile @archive
      else
        console.log opts
        throw "Either filename or archive need to be specified"

    @commands = normalizeCommands commands

    if not deps?
      deps = []

    @deps = []
    @depRules = []

    for dep in deps
      if dep.filename?
        @depRules.push dep
        @deps.push dep.filename
      else
        @deps.push dep

  stringify: ->
    @deps.sort()
    "#{@filename}: #{@deps.join(' ')}\n\t#{@commands.join('\n\t')}"




tarFile = (options) ->
  {archive, deps, resultDir, getCommands, mounts} = options
  tmp = "#{os.tmpdir()}/oxg/#{crypto.randomBytes(8).toString('hex')}"

  mounts = [] if not mounts?
  resultDir = '/' if not resultDir?
  deps = [] if not deps?

  mountLines = []
  for root, source of mounts
    # Since we're mounting it, we must be dependent on it
    if source.filename?
      filename = source.filename
      deps.push source
    else
      filename = archiveFile source
      deps.push filename
    mountLines.push "mkdir -p #{tmp}#{root}"
    mountLines.push "tar xf #{filename} -C #{tmp}#{root}"

  new Rule
    archive: archive
    deps: deps
    commands: ["rm -rf #{tmp}", "mkdir -p #{tmp}"]
      .concat mountLines
      .concat(normalizeCommands getCommands(tmp))
      .concat ["mkdir -p .cache && tar cf #{archiveFile archive} -C #{tmp}#{resultDir} ."]


gitCheckout = (name, refFile) ->
  archive = "checkouts-#{name}"
  new Rule
    archive: archive
    deps: [refFile]
    commands: ["git --git-dir .git archive $(shell cat #{refFile}) > #{archiveFile archive}"]

gitCheckoutBranch = (branch) ->
  gitCheckout branch, ".git/refs/heads/#{branch}"

gitCheckoutTag = (tag) ->
  gitCheckout tag, ".git/refs/tags/#{tag}"


workingTree = (options) ->
  {name, deps} = options
  new Rule
    archive: name
    deps: deps
    commands: """
      git ls-files -o -i --exclude-standard > /tmp/excludes
      rm -f #{archiveFile name}
      # We are excluding  so tar doesn't complain about recursion
      tar cf #{archiveFile name} --exclude .git --exclude #{archiveFile name} --exclude-from=/tmp/excludes .
    """


googleFonts = (googleUrl) ->
  tarFile
    archive: 'fonts'
    resultDir: '/out'
    getCommands: (tmp) -> """
      wget -O #{tmp}/index.css "#{googleUrl}"
      cat #{tmp}/index.css | grep -o -e "http.*ttf" > #{tmp}/download.list
      (cd #{tmp} && wget -i download.list)
      mkdir #{tmp}/out
      cp #{tmp}/*.ttf #{tmp}/out
      sed 's/http.*\\/\\(.*\\.ttf\\)/\"..\\/fonts\\/\\1\"/g' < #{tmp}/index.css > #{tmp}/out/index.css
    """


fileDownload = (options) ->
  {filename, url} = options
  tarFile
    archive: "download-#{filename}"
    getCommands: (tmp) -> """
      wget -O #{tmp}/#{filename} "#{url}"
    """


tarFromZip = (options) ->
  {name, url} = options
  tarFile
    archive: name
    resultDir: '/out'
    getCommands: (tmp) -> """
      wget #{url} -O #{tmp}/src-#{name}.zip
      mkdir #{tmp}/out
      unzip #{tmp}/src-#{name}.zip -d #{tmp}/out
    """

localNpmPackage = (name) ->
  tarFile
    archive: "npm-#{name}"
    deps: ["node_modules/#{name}/package.json"]
    getCommands: (tmp) -> """
      cp -R node_modules/#{name}/* #{tmp}
    """


module.exports = {
  normalizeCommands: normalizeCommands
  archiveFile: archiveFile
  Makefile: Makefile
  Rule: Rule
  tarFile: tarFile
  workingTree: workingTree
  gitCheckout: gitCheckout
  gitCheckoutBranch: gitCheckoutBranch
  gitCheckoutTag: gitCheckoutTag
  tarFromZip: tarFromZip
  googleFonts: googleFonts
  fileDownload: fileDownload
  localNpmPackage: localNpmPackage
}
