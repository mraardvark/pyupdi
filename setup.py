#!/usr/bin/env python

from setuptools import setup, find_packages

name = "pyupdi"
author = "mraardvark"
url = "https://github.com/%s/%s" % (author, name)

setup(
    name = name,
    author = author,
    url = url,
    entry_points = {
        'console_scripts': ['pyupdi=updi:_main'],
    },
    packages = find_packages(),
    python_requires = '>3',
    install_requires = [r.strip() for r in open("requirements.txt").readlines()]
)
