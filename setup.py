#!/usr/bin/python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name = 'teleport',
    version = "0.0.5",
    py_modules = ['teleport'],
    description = 'An extandable serialization system',
    license = "MIT",
    author_email = "alexei.boronine@gmail.com",
    install_requires=[
      "Werkzeug >= 0.8.3"
    ],
    long_description = long_description
)
