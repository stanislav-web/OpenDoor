from setuptools import setup

setup(
    name='opendoor',
    version='1.3.51',
    packages=['opendoor'],
    url='https://github.com/stanislav-web/OpenDoor',
    license='GPL',
    author='Stanislav Menshov',
    author_email='stanisov@gmail.com',
    description='OWASP Directory Access scanner',
    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.md').read(),
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