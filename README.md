Teleport
========

[![Join the chat at https://gitter.im/cosmic-api/teleport](https://badges.gitter.im/cosmic-api/teleport.svg)](https://gitter.im/cosmic-api/teleport?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Teleport is a lightweight type system that extends JSON. It can be used for:

* Serializing data
* Validating input
* Generating documentation
* Building custom JSON serializers
* Building API clients

Teleport is:

* Portable and extendable
* Open Source ([MIT license](http://opensource.org/licenses/MIT))

Status
======

The latest [specification](http://www.teleport-json.org/spec/draft-03/) has been submitted as [an Internet Draft](https://datatracker.ietf.org/doc/draft-boronine-teleport/) on Sep 27, 2015. It is implemented as a [Python library](http://www.teleport-json.org/python/0.4/).

Build Instructions
==================

[Nix](https://nixos.org/nix/) is required to build Teleport and its documentation.

To build site:

	nix-build -A site

Output for current build goes into the `result` directory. See `default.nix` for other buildable derivations.

To launch a static web server immediatedly after building:

	./serve site

License
-------

Copyright (C) 2016 Alexei Boronine

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
