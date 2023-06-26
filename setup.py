#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Development Team: Brain Storm Team
"""

from setuptools import setup, find_packages
NAME = 'opendoor'
VERSION = '4.0.6'
DESCRIPTION = 'OWASP WEB Directory Scanner'
LONG_DESCRIPTION = open('README.md', 'r+', encoding='utf-8').read()
HOMEPAGE = 'https://github.com/stanislav-web/OpenDoor'
AUTHOR = 'Brain Storm Team',
AUTHOR_EMAIL = 'nomail@gmail.com',
MAINTAINER = 'Brain Storm Team',
FULL_NAME = 'Brain Storm'
DOWNLOAD_URL = 'https://github.com/stanislav-web/OpenDoor/archive/refs/heads/master.zip'
setup(name=NAME,

      # Versions should comply with PEP440.  For a discussion on single-sourcing
      # the version across setup.py and the project code, see
      # https://packaging.python.org/en/latest/single_source_version.html

      version=VERSION,

      description=DESCRIPTION,

      long_description=LONG_DESCRIPTION,

      long_description_content_type="text/markdown",

      # The project's main homepage.
      url=HOMEPAGE,

      # Author details
      author="".join(AUTHOR),

      fullname="".join(FULL_NAME),

      author_email="".join(AUTHOR_EMAIL),

      maintainer="".join(MAINTAINER),

      maintainer_email="".join(AUTHOR_EMAIL),

      # You can just specify the packages manually here if your project is
      # simple. Or you can use find_packages().
      zip_safe=False,
      packages=find_packages(),
      data_files=[('.', ['opendoor.conf']),
                  ('data', [
                      'data/directories.dat',
                      'data/ignored.dat',
                      'data/proxies.dat',
                      'data/subdomains.dat',
                      'data/useragents.dat',
                  ])
                  ],
      include_package_data=True,

      script_name='opendoor.py',
      # Choose your license
      license='GPL',
      # Unittests suite directory
      test_suite='tests',

      # What does your project relate to?
      keywords=[
          'owasp scanner',
          'directory scanner',
          'access directory scanner',
          'fuzzer',
          'auth scanner',
          'dir search',
          'dirmap'
      ],

      download_url=DOWNLOAD_URL,

      # To provide executable scripts, use entry points in preference to the
      # "scripts" keyword. Entry points provide cross-platform support and allow
      # pip to create the appropriate form of executable for the target platform.
      entry_points={'console_scripts': [
          'opendoor=src:main',
          'coveralls = coveralls.cli:main'
      ]},

      install_requires=[line.rstrip('\n') for line in open('requirements.txt')],
      tests_require=[line.rstrip('\n') for line in open('requirements-dev.txt')],

      platforms=['any'],
      # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
      # How mature is this project? Common values are
      classifiers=[
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          'Development Status :: 5 - Production/Stable',

          # Language
          'Natural Language :: English',

          # Indicate who your project is intended for
          'Intended Audience :: Developers',

          # OS, which support this package
          'Operating System :: MacOS',
          'Operating System :: Unix',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.

          'Programming Language :: Python',
          'Programming Language :: Python :: 3',

          # Specify the additional categories
          'Topic :: Utilities',
          'Topic :: Internet :: WWW/HTTP :: Site Management :: Link Checking',
          'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
          'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
      ])
