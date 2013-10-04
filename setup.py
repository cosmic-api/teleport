#!/usr/bin/python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name = 'teleport',
    version = "0.2.1",
    py_modules = ['teleport'],
    description = 'An extandable serialization system',
    license = "MIT",
    author = "8313547 Canada Inc.",
    author_email = "alexei.boronine@gmail.com",
    install_requires=[
        "isodate>=0.4.9",
    ],
    long_description = long_description
)
