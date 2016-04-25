rec {

  pkgs = import <nixpkgs> {};
  nodejs = pkgs.nodejs-5_x;
  sphinx = pkgs.python3Packages.sphinx;

  specBuilder = pkgs.buildPythonPackage rec {
    name = "xml2rfc-2.5.1";
    propagatedBuildInputs = with pkgs.pythonPackages; [ lxml requests2 ];
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/source/x/xml2rfc/xml2rfc-2.5.1.tar.gz";
      sha256 = "67d44fce6548c44e6065b95d0ef5b3a6e08928e6d659d4396928d8937c2be32d";
    };
  };

  nodeModules = pkgs.stdenv.mkDerivation {
    # npm2nix is neat but broken, consider trying again in a few months
    name = "node-modules";
    packageJson = ./package.json;
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      HOME=.
      cp $packageJson package.json
      $nodejs/bin/npm install
      mkdir $out
      cp -R node_modules $out/node_modules
    ";
    inherit nodejs;
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
    siteDir = ./_site;
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      mkdir $out
      cp -R $siteDir/* $out
      cp -R $nodeModules/node_modules $out/node_modules
    ";
    inherit nodeModules;
  };

  rfc2html = rfc : pkgs.stdenv.mkDerivation {
    name = "rfc2html";
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      $nodejs/bin/node $nodeBuilder/spec.js < $rfc > $out
    ";
    inherit rfc;
    inherit nodejs;
    inherit nodeBuilder;
  };

  inject = {htmlTree, opts} : pkgs.stdenv.mkDerivation {
    name = "inject";
    buildInputs = [nodejs];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      PATH=$nodeModules/node_modules/.bin:$PATH
      cp -R --no-preserve=mode $htmlTree $out
      find $out -iname \\*.html | xargs node $nodeBuilder/inject.js $opts
    ";
    inherit nodejs;
    inherit nodeBuilder;
    inherit htmlTree;
    inherit opts;
  };

  xml2rfc = xmlFile : pkgs.stdenv.mkDerivation {
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
    inherit xmlFile;
    inherit specBuilder;
  };

  pythonDocs = pythonRoot : pkgs.stdenv.mkDerivation {
    name = "sphinx-docs";
    buildInputs = [pkgs.python3 sphinx];
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      cp -R $pythonRoot/* .
      sphinx-build -W -b html docs $out
    ";
    inherit pythonRoot;
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
    name = "bootstrap";
    staticCss = _site/static/static.css;
    fontsCss = _site/static/fonts.css;
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      PATH=$nodejs/bin:$nodeModules/node_modules/.bin:$PATH

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
    inherit bootswatch;
    inherit bootstrapDist;
    inherit highlightjs;
    inherit nodeModules;
    inherit fontAwesome;
    inherit googleFonts;
    inherit nodejs;
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
      PATH=$nodeBuilder/node_modules/.bin:$PATH

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

}


