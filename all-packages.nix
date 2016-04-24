rec {

  pkgs = import <nixpkgs> {};
  nodejs = pkgs.nodejs-5_x;

  xml2rfc = pkgs.buildPythonPackage rec {
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

  injectNavbar = {htmlSite, args} : pkgs.stdenv.mkDerivation {
    name = "inject";
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      mkdir $out
      cp -R $htmlSite/* $out
      find $out -iname \\*.html | xargs $nodejs/bin/node $nodeBuilder/inject.js $args
    ";
    inherit nodejs;
    inherit nodeBuilder;
  };

  spec = version : pkgs.stdenv.mkDerivation {
    name = "spec-${version}";
    specs = ./_spec;
    python = pkgs.python3;
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      PATH=$python/bin:$PATH
      mkdir cache
      $xml2rfc/bin/xml2rfc --no-network --cache=./cache $specs/draft-${version}.xml --text --out=$out
    ";
    inherit version;
    inherit xml2rfc;
  };

  spec00 = spec "00";
  spec01 = spec "01";
  spec02 = spec "02";
  spec03 = spec "03";
  spec04 = spec "04";

  bootstrapDist = pkgs.fetchzip {
      url = "https://github.com/twbs/bootstrap/releases/download/v3.3.0/bootstrap-3.3.0-dist.zip";
      sha256 = "0i014fyw07vzhbjns05zjxv23q0k47m8ks7nfiv8psqaca45l1sy";
  };

  googleFonts= pkgs.stdenv.mkDerivation {
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
      cat $bootswatch/lumen/bootstrap.css >> everything.css
      cat $highlightjs/src/styles/default.css >> everything.css
      cat $staticCss >> everything.css
      # Make the css safe to mix with other css
      namespace-css everything.css -s .bs >> everything-safe.css
      sed -i.bak 's/\\.bs\\ body/\\.bs,\\ \\.bs\\ body/g' everything-safe.css

      cp everything-safe.css $out/css/bootstrap.css
      cleancss $out/css/bootstrap.css > $out/css/bootstrap.min.css

      cat $fontAwesome/css/font-awesome.css >> $out/css/bootstrap.css

    ";
    inherit bootswatch;
    inherit bootstrapDist;
    inherit highlightjs;
    inherit nodeModules;
    inherit fontAwesome;
    inherit googleFonts;
    inherit nodejs;
  };

  site = pkgs.stdenv.mkDerivation {
    name = "site";
    staticDir = ./_site/static;
    spec00 = rfc2html(spec "00");
    spec01 = spec "01";
    spec02 = spec "02";
    spec03 = spec "03";
    spec04 = spec "04";
    builder = builtins.toFile "builder.sh" "
      source $stdenv/setup
      PATH=$nodejs/bin:$nodeBuilder/node_modules/.bin:$PATH
      mkdir -p $out/static
      cp -R $staticDir/* $out/static
      cp -R $bootstrap $out/static/bootstrap
      node $nodeBuilder/index.js > $out/index.html
    ";
    inherit nodejs;
    inherit bootstrap;
    inherit nodeBuilder;
  };

}


