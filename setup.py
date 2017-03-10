from setuptools import setup
import sys

setup(
    name="ftfy",
    version='4.4.1',
    maintainer='Luminoso Technologies, Inc.',
    maintainer_email='info@luminoso.com',
    license="MIT",
    url='http://github.com/LuminosoInsight/python-ftfy',
    platforms=["any"],
    description="Fixes some problems with Unicode text after the fact",
    packages=['ftfy', 'ftfy.bad_codecs'],
    package_data={'ftfy': ['char_classes.dat']},

    # We could drop the html5lib dependency if we drop support for Python <=
    # 3.4, because the feature we need from html5lib is now in the standard
    # library, as html.unescape.
    install_requires=['html5lib', 'wcwidth'],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Development Status :: 5 - Production/Stable"
    ],
    entry_points={
        'console_scripts': [
            'ftfy = ftfy.cli:main'
        ]
    }
)
