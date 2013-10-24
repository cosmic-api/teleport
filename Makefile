.PHONY: docs live

docs:
	tox -e py27 --notest
	(. .tox/py27/bin/activate; cd docs; make clean; make html)

live:
	livereload --browser docs/build/html

