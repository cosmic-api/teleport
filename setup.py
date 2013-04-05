#!/usr/bin/python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name = 'teleport',
    version = "0.0.1",
    modules = ['teleport'],
    description = 'Extandable serialization system',
    license = "MIT",
    author_email = "alexei.boronine@gmail.com",
    long_description = long_description
)
