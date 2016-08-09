from setuptools import setup, find_packages

setup(
    name='opendoor',
    version='1.3.52',
    packages=find_packages(),
    url='https://github.com/stanislav-web/OpenDoor',
    license='GPL',
    test_suite='tests',
    author='Stanislav Menshov',
    author_email='stanisov@gmail.com',
    description='OWASP Directory Access scanner',
    long_description=open('README.md').read(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'opendoor = opendoor',
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