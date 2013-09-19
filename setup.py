#!/usr/bin/python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name = 'teleport',
    version = "0.2.0",
    py_modules = ['teleport'],
    description = 'An extandable serialization system',
    license = "MIT",
    author = "8313547 Canada Inc.",
    author_email = "alexei.boronine@gmail.com",
    install_requires=[],
    long_description = long_description
)
