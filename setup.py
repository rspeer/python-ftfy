from setuptools import setup
import sys

setup(
    name="ftfy",
    version='4.3.0',
    maintainer='Luminoso Technologies, Inc.',
    maintainer_email='info@luminoso.com',
    license="MIT",
    url='http://github.com/LuminosoInsight/python-ftfy',
    platforms=["any"],
    description="Fixes some problems with Unicode text after the fact",
    packages=['ftfy', 'ftfy.bad_codecs'],
    package_data={'ftfy': ['char_classes.dat']},

    # Oh no, we grew a dependency! We could actually go back to having no
    # dependencies if we drop support for Python <= 3.4, because the feature
    # we need from html5lib is now in the standard library, as html.unescape.
    install_requires=['html5lib'],
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


if sys.version_info[0] < 3:
    sys.stderr.write("""
    Heads up! You're now running ftfy 4.x on Python 2.x. This is fine, but
    here's an advance warning that you won't be able to upgrade ftfy
    forever without upgrading Python.

    The next major version of ftfy, version 5.0, will probably only work
    on Python 3, making it easier to develop and ensure its consistency.

    It's fine if you're happy with Python 2 and ftfy 4. Save yourself a
    headache later and be sure to pin a version in your dependencies.
    Instead of just asking for 'ftfy', you should ask for:

        'ftfy >= 4, < 5'
    """.strip(' '))

