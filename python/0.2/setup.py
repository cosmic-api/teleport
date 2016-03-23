#!/usr/bin/python

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name='teleport',
    version="0.2.1",
    packages=['teleport', 'teleport.testsuite'],
    description='An extandable serialization system',
    license="MIT",
    author="Alexei Boronine",
    author_email="alexei@boronine.com",
    install_requires=[
        "isodate>=0.4.9",
        "ordereddict>=1.1"
    ],
    long_description=long_description,
    test_suite='teleport.testsuite.suite'
)
