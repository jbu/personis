from setuptools import setup, find_packages
import fnmatch
import os

import distribute_setup
distribute_setup.use_setuptools()

long_desc = """The Google API Client for Python is a client library for
accessing the Plus, Moderator, and many other Google APIs."""

install_requires=[
    'google-api-python-client',
    'pyyaml',
    'cherrypy >= 3.0',
    'pyparsing',
    'shove',
    'distribute'
    ]

packages = [
  'personis',
  'personis.client',
  'personis.examples',
  'personis.examples.browser',
  'personis.examples.activity',
  'personis.examples.asker',
  'personis.examples.log-llum',
  'personis.examples.aelog',
  'personis.server',
  'personis.server.test'
  ]


include_patterns = '*.html *.css *.png *.gif *.yaml *.json *.conf *.rst *.jpg *.ico *.txt *.js *.doctree Makefile README *.pdf *.sh *.svg'.split()
matches = []
for root, dirnames, filenames in os.walk('personis'):
    for pat in include_patterns:
        for filename in fnmatch.filter(filenames, pat):
            matches.append(os.path.join(root, filename))

#matches = [i for i in matches if (i.startswith('./personis') or i.startswith('./server_conf'))]

packagedat = {
    '': matches
    }

long_desc = """The Personis user model server and associated client library. Also some sample clients."""

import personis
version = personis.__version__

setup(
    name="personis",
    version=version,
    description="Peronis user model library",
    long_description=long_desc,
    author='Bob Kummerfeld, James Uther, Mark Assad, Judy Kay, et. al.',
    author_email='bob.kummerfeld@sydney.edu.au',
    url='http://github.com/jbu/personis',
    install_requires=install_requires,
    packages=packages,
    scripts=[],
    license="GPL3",
    package_data=packagedat,
    keywords="personis user-model server",
    include_package_data = True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Framework :: CherryPy',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)