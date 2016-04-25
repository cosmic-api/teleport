#!/usr/bin/python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name='teleport',
    version="0.5.0",
    packages=['teleport', 'teleport.testsuite'],
    description='Lightweight JSON type system',
    license="MIT",
    author="Alexei Boronine",
    author_email="alexei@boronine.com",
    url="http://www.teleport-json.org",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
    ],
    long_description=long_description,
    test_suite='teleport.testsuite.suite'
)
