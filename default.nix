rec {
  pkgs = import (pkgsSrc) {};
  pkgsOriginal = import <nixpkgs> {};

  pkgsSrc = pkgsOriginal.fetchzip {
    url = "https://github.com/NixOS/nixpkgs/archive/refs/tags/22.05.zip";
    sha256 = "sha256-M6bJShji9AIDZ7Kh7CPwPBPb/T7RiVev2PAcOi4fxDQ=";
  };

  nodejs = pkgs.nodejs;
  sphinx = pkgs.python3Packages.sphinx;

  specBuilder = pkgs.python3Packages.buildPythonPackage rec {
    name = "xml2rfc-2.5.1";
    propagatedBuildInputs = with pkgs.python3Packages; [ lxml requests ];
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/source/x/xml2rfc/xml2rfc-2.5.1.tar.gz";
      sha256 = "67d44fce6548c44e6065b95d0ef5b3a6e08928e6d659d4396928d8937c2be32d";
    };
  };

  nodeModules = pkgs.stdenv.mkDerivation {
    inherit nodejs;
    name = "node-modules";
    propagatedBuildInputs = [nodejs];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      HOME=.
      npm install cheerio@0.19.0
      npm install clean-css@3.4.12
      npm install highlight.js@8.3.0
      npm install jquery@2.1.1
      npm install minimist@1.1.0
      npm install mustache@0.8.1
      npm install namespace-css@0.1.3
      npm install glob@5.0.14
      mkdir $out
      cp -R node_modules $out/node_modules
      ln -sv $out/node_modules/.bin $out/bin
    ";
  };

  zip2dir = zipFile: pkgs.stdenv.mkDerivation {
    name = "unzip";
    buildInputs = [pkgs.unzip];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      mkdir $out
      unzip $zipFile -d $out
    ";
    inherit zipFile;
  };

  nodeBuilder = pkgs.stdenv.mkDerivation {
    name = "node-builder";
    propagatedBuildInputs = [nodeModules nodejs];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      mkdir $out
      cp -R $siteDir/* $out
      cp -R $nodeModules/* $out
    ";
    siteDir = ./_site;
    inherit nodeModules;
  };

  rfc2html = rfc : pkgs.stdenv.mkDerivation {
    inherit rfc nodejs nodeBuilder;
    name = "rfc2html";
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      $nodejs/bin/node $nodeBuilder/spec.js < $rfc > $out
    ";
  };

  inject = {htmlTree, opts} : pkgs.stdenv.mkDerivation {
    inherit nodejs nodeBuilder htmlTree opts;
    name = "inject";
    buildInputs = [nodejs];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      cp -R --no-preserve=mode $htmlTree $out
      find $out -iname \\*.html | xargs node $nodeBuilder/inject.js $opts
    ";
  };

  xml2rfc = xmlFile : pkgs.stdenv.mkDerivation {
    inherit xmlFile specBuilder;
    name = "spec";
    specs = ./_spec;
    python = pkgs.python3;
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      PATH=$python/bin:$PATH
      mkdir cache
      $specBuilder/bin/xml2rfc --no-network --cache=./cache $xmlFile --text --out=$out
      chmod 644 $out
    ";
  };

  pythonDocs = pythonRoot : pkgs.stdenv.mkDerivation {
    inherit pythonRoot;
    name = "sphinx-docs";
    buildInputs = [pkgs.python3 sphinx];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      cp -R $pythonRoot/* .
      SOURCE_DATE_EPOCH=1451606400 # sphinx overrides copyright year based on this environment variable
      sphinx-build -v -W -b html docs $out
    ";
  };

  pythonDocs02 = inject {
    htmlTree = pythonDocs ./python/0.2;
    opts = "--navbar python/0.2 --bs";
  };
  pythonDocs03 = inject {
    htmlTree = pythonDocs ./python/0.3;
    opts = "--navbar python/0.3 --bs";
  };
  pythonDocs04 = inject {
    htmlTree = pythonDocs ./python/0.4;
    opts = "--navbar python/0.4 --bs";
  };

  bootstrapDist = pkgs.fetchzip {
    url = "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip";
    sha256 = "0i014fyw07vzhbjns05zjxv23q0k47m8ks7nfiv8psqaca45l1sy";
  };

  googleFonts = pkgs.stdenv.mkDerivation {
    name = "google-fonts";
    fonts = pkgs.google-fonts;
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      mkdir $out
      cp $fonts/share/fonts/truetype/Lato-Italic.ttf $out
      cp $fonts/share/fonts/truetype/Lato-Bold.ttf $out
      cp $fonts/share/fonts/truetype/Lato-Regular.ttf $out
      cp $fonts/share/fonts/truetype/Inconsolata-Regular.ttf $out
      cp $fonts/share/fonts/truetype/Inconsolata-Bold.ttf $out
    ";
  };

  jqueryMin = pkgs.fetchurl {
    url = "https://code.jquery.com/jquery-2.2.3.min.js";
    sha256 = "16hh52338jahcjk1pppmagqr7gxvsgmlgnry78cd2xkqvgaf0vbb";
  };

  bootswatch = pkgs.fetchzip {
    url = "https://github.com/thomaspark/bootswatch/archive/v3.3.6+1.zip";
    sha256 = "1d2pdxk5zavs6v9am4gv3im19x9mra19cc6xipb7qnwab1wqmb1d";
  };

  highlightjs = pkgs.fetchzip {
    url = "https://github.com/isagalaev/highlight.js/archive/9.3.0.zip";
    sha256 = "1m53mrfx59hiz6kbl6d3vczhxxqca8l2jx5qx2ndi4l8wwkf75nd";
  };

  fontAwesome = pkgs.fetchzip {
    url = "https://github.com/FortAwesome/Font-Awesome/archive/v4.6.1.zip";
    sha256 = "0iw5xzsmj04yzhf8kwav7wy7izvjnnqxzlmn38vp4nhnwr2av4cg";
  };

  bootstrap = pkgs.stdenv.mkDerivation {
    inherit bootswatch bootstrapDist highlightjs nodeModules fontAwesome googleFonts nodejs;
    name = "bootstrap";
    staticCss = _site/static/static.css;
    fontsCss = _site/static/fonts.css;
    buildInputs = [nodeModules nodejs];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup

      mkdir $out
      cp -R $bootstrapDist/js $out/js
      mkdir $out/css
      mkdir $out/fonts
      cp -R $googleFonts/* $out/fonts
      cp $fontAwesome/fonts/fontawesome-webfont.ttf $out/fonts

      touch everything.css
      cat $bootswatch/flatly/bootstrap.css | sed '/googleapis/d' > everything.css
      cat $highlightjs/src/styles/default.css >> everything.css
      cat $staticCss >> everything.css
      # Make the css safe to mix with other css
      namespace-css everything.css -s .bs >> everything-safe.css
      sed -i.bak 's/\\.bs\\ body/\\.bs,\\ \\.bs\\ body/g' everything-safe.css
      # @font-face shouldn't be namespaced
      cat $fontsCss >> everything-safe.css
      cat $fontAwesome/css/font-awesome.css >> everything-safe.css
      cp everything-safe.css $out/css/bootstrap.css
      cleancss $out/css/bootstrap.css > $out/css/bootstrap.min.css
    ";
  };

  specLegacy = zip2dir ./_site/archive/spec-old.zip;

  site = pkgs.stdenv.mkDerivation {
    name = "site";
    staticDir = ./_site/static;
    buildInputs = [pkgs.unzip nodejs];
    specLegacy = zip2dir ./_site/archive/spec-old.zip;
    spec00 = rfc2html (xml2rfc ./_spec/draft-00.xml);
    spec01 = rfc2html (xml2rfc ./_spec/draft-01.xml);
    spec02 = rfc2html (xml2rfc ./_spec/draft-02.xml);
    spec03 = rfc2html (xml2rfc ./_spec/draft-03.xml);
    spec04 = rfc2html (xml2rfc ./_spec/draft-04.xml);

    builder = builtins.toFile "builder.sh" ''
      source $stdenv/setup
      PATH=$nodeBuilder/bin:$PATH

      echo $(pwd)

      mkdir -p static
      cp -R $staticDir/* static
      cp $jqueryMin static/jquery.min.js
      cp -R $bootstrap static/bootstrap
      node $nodeBuilder/index.js > index.html
      node $nodeBuilder/inject.js index.html --navbar '/' --bs --highlight

      mkdir spec
      cp -R --no-preserve=mode $specLegacy/spec-old spec/1.0
      node $nodeBuilder/inject.js spec/1.0/index.html --navbar 'spec/1.0' --bs

      mkdir -p spec/draft-00
      cat $spec00 > spec/draft-00/index.html
      node $nodeBuilder/inject.js spec/draft-00/index.html --navbar 'spec/draft-00' --bs

      mkdir -p spec/draft-01
      cat $spec01 > spec/draft-01/index.html
      node $nodeBuilder/inject.js spec/draft-01/index.html --navbar 'spec/draft-01' --bs

      mkdir -p spec/draft-02
      cat $spec02 > spec/draft-02/index.html
      node $nodeBuilder/inject.js spec/draft-02/index.html --navbar 'spec/draft-02' --bs

      mkdir -p spec/draft-03
      cat $spec03 > spec/draft-03/index.html
      node $nodeBuilder/inject.js spec/draft-03/index.html --navbar 'spec/draft-03' --bs

      mkdir -p spec/draft-04
      cat $spec04 > spec/draft-04/index.html
      node $nodeBuilder/inject.js spec/draft-04/index.html --navbar 'spec/draft-04' --bs

      mkdir python
      cp -R --no-preserve=mode $pythonDocs02 python/0.2
      cp -R --no-preserve=mode $pythonDocs03 python/0.3
      cp -R --no-preserve=mode $pythonDocs04 python/0.4

      mkdir -p $out
      cp -R . $out
    '';
    inherit nodejs;
    inherit bootstrap;
    inherit jqueryMin;
    inherit nodeBuilder;
    inherit pythonDocs02;
    inherit pythonDocs03;
    inherit pythonDocs04;
  };

  siteGA = inject {
    htmlTree = site;
    opts = "--analytics";
  };

  deploySite = pkgs.stdenv.mkDerivation {
    name = "deploy";
    buildInputs = [site nodeModules nodejs];
    # nix-build -A site
    # aws s3 sync result s3://www.teleport-json.org
    builder = builtins.toFile "builder.sh" ''
      source $stdenv/setup
      touch $out
    '';
    inherit site;
  };

}


