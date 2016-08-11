from setuptools import setup, find_packages
from Libraries import Version


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
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': [
            'coveralls = coveralls.cli:main',
        ],
    },
    install_requires=[line.rstrip('\n') for line in open('requirements.txt')],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)