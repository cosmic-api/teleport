.PHONY: docs

docs:
	tox -e py27 --notest
	(. .tox/py27/bin/activate; cd docs; make clean; make html)

