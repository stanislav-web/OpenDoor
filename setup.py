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

from pathlib import Path

from setuptools import find_packages, setup


PROJECT_ROOT = Path(__file__).resolve().parent


def read_text(filename: str) -> str:
    """
    Read a text file from the project root.

    :param filename: Relative filename in the project root.
    :return: File content as UTF-8 text.
    """
    return (PROJECT_ROOT / filename).read_text(encoding='utf-8').strip()


def read_requirements(filename: str) -> list[str]:
    """
    Read requirements from a plain text file.

    Blank lines and comment-only lines are ignored.

    :param filename: Relative filename in the project root.
    :return: Parsed requirement lines.
    """
    lines = (PROJECT_ROOT / filename).read_text(encoding='utf-8').splitlines()

    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith('#')
    ]


VERSION = read_text('VERSION')
README = read_text('README.md')


setup(
    name='opendoor',
    version=VERSION,
    description='Fast CLI for directory discovery, subdomain enumeration, and web asset reconnaissance',
    long_description=README,
    long_description_content_type='text/markdown; charset=UTF-8; variant=GFM',
    url='https://github.com/stanislav-web/OpenDoor',
    author='stanislav-web',
    license='GPL-3.0-only',
    license_files=['LICENSE'],
    python_requires='>=3.12,<3.15',
    zip_safe=False,
    packages=find_packages(exclude=('tests', 'tests.*')),
    include_package_data=True,
    data_files=[
        ('.', ['opendoor.conf']),
        (
            'data',
            [
                'data/directories.dat',
                'data/ignored.dat',
                'data/proxies.dat',
                'data/subdomains.dat',
                'data/useragents.dat',
            ],
        ),
    ],
    keywords=[
        'directory scanner',
        'subdomain scanner',
        'subdomain enumeration',
        'content discovery',
        'asset discovery',
        'web reconnaissance',
        'security testing',
        'cli',
        'owasp',
    ],
    install_requires=read_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'opendoor=src:main',
        ]
    },
    platforms=['any'],
    project_urls={
        'Homepage': 'https://github.com/stanislav-web/OpenDoor',
        'Source': 'https://github.com/stanislav-web/OpenDoor',
        'Documentation': 'https://opendoor.readthedocs.io',
        'Bug Tracker': 'https://github.com/stanislav-web/OpenDoor/issues',
        'Changelog': 'https://github.com/stanislav-web/OpenDoor/releases',
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Topic :: Internet',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Security',
        'Topic :: Utilities',
    ],
)