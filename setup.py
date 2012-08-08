from setuptools import setup



long_desc = """The Google API Client for Python is a client library for
accessing the Plus, Moderator, and many other Google APIs."""

install_requires=[
    'google-api-python-client',
    'pyyaml',
    'cherrypy>=3.0',
    'pyparsing',
    'shove'
    ]

packages = [
  'personis'
  ]

needs_json = True
try:
  import json
  needs_json = False
except ImportError:
  try:
    import simplejson
    needs_json = False
  except ImportError:
    needs_json = True

if needs_json:
  install_requires.append('simplejson')

long_desc = """The Personis user model server and associated client library. Also some sample clients."""

import personis
version = personis.__version__

setup(name="personis",
    version=version,
    description="Peronis user model library",
    long_description=long_desc,
    author='Bob Kummerfeld, James Uther, Mark Assad, Judy Kay, et. al.',
    author_email='bob.kummerfeld@sydney.edu.au',
    url='http://github.com/jbu/personis',
    install_requires=install_requires,
    packages=packages,
    package_data={},
    scripts=[],
    license="GPL3",
    keywords="personis user-model server",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL3',
        'Operating System :: POSIX',
        'Topic :: Internet :: WWW/HTTP'
    ]
)