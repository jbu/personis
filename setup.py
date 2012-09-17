from setuptools import setup, find_packages

install_requires=[
    'google-api-python-client',
    'pyyaml',
    'cherrypy >= 3.0',
    'pyparsing',
    'distribute'
    ]

long_desc = """The Personis user model server and associated client library. Also some sample clients."""

import personis
version = personis.__version__

setup(
    name = "personis",
    packages = find_packages(),
    scripts = [],

    install_requires = install_requires,
    include_package_data = True,
    package_data = {
        'personis.server': ['static/images/*.*', 'static/js/*.js']
    },
    entry_points = {
        'console_scripts': [
            'watcher = personis.examples.activity.__main__:go',
            'umbrowser = personis.examples.browser.__main__:go',
        ]
    },
    version=version,
    description="Peronis user model library",
    long_description=long_desc,
    author='Bob Kummerfeld, James Uther, Mark Assad, Judy Kay, et. al.',
    author_email='bob.kummerfeld@sydney.edu.au',
    url='http://github.com/jbu/personis',
    license="GPL3",
    keywords="personis user-model server",
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
