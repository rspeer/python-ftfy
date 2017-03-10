from setuptools import setup
import sys


PY2_MESSAGE = """
Sorry, this version of ftfy is no longer written for Python 2.

It is much easier to provide consistent handling of Unicode when developing
only for Python 3. ftfy is exactly the kind of library that Python 3 is
designed for, and now there is enough Python 3 usage that we can take advantage
of it and write better, simpler code.

The older version of ftfy, version 4.4, is still available and can run on
Python 2. Try this:

    pip install ftfy==4.4.1
"""


if sys.version_info[0] < 3:
    print(PY2_MESSAGE)
    sys.exit(1)


setup(
    name="ftfy",
    version='5.0.1',
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
