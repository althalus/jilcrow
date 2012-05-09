import os
from setuptools import setup


README_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README')
description = 'A small static site generator that uses Jinja templates.'

if os.path.exists(README_PATH):
    long_description = open(README_PATH).read()
else:
    long_description = description

setup(
    name='jilcrow',
    version='0.1.1',
    install_requires=['BeautifulSoup', 'python-dateutil', 'Jinja2', 'Markdown',
                      'PyRSS2Gen', 'PyYAML'],
    description=description,
    long_description=long_description,
    author='Liam Cooke, Steve Losh',
    url='http://bitbucket.org/sjl/jilcrow/',
    packages=['jilcrow'],
    scripts=['bin/jilcrow'],
)

