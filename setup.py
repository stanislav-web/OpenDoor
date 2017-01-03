#! /usr/bin/env python

#    OpenDoor Web Directory Scanner
#    Copyright (C) 2016  Stanislav Menshov
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Development Team: Stanislav Menshov (Stanislav WEB)

from setuptools import setup, find_packages
from src.Version import Version

setup(
    name='opendoor',
    version=Version.get_local_version(),
    packages=find_packages(),
    url='https://github.com/stanislav-web/OpenDoor',
    license='GPL',
    test_suite='tests',
    author='Stanislav Menshov',
    author_email='stanisov@gmail.com',
    description='OWASP Directory Access scanner',
    long_description=open('README.rst').read(),
    keywords=['owasp scanner', 'directory scanner', 'access directory scanner', 'web spider', 'auth scanner'],
    entry_points={
        'console_scripts': [
            'coveralls = coveralls.cli:main',
        ],
    },
    scripts=['opendoor.py'],
    install_requires=[line.rstrip('\n') for line in open('requirements.txt')],

    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: src :: Python Modules',
    ],
)
