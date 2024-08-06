import sys

from setuptools import setup

# Before we get to the rest of setup, with dependencies on setuptools and the
# Python 3 standard library, let's make sure we're not on Python 2 and provide
# a helpful message if we are.

PY2_MESSAGE = "Python 2 is no longer supported. Please upgrade."


if sys.version_info[0] < 3:
    print(PY2_MESSAGE)
    readable_version = sys.version.split(" ")[0]
    print("The version of Python you're running is: %s" % readable_version)
    print("Python is running from: %r" % sys.executable)
    sys.exit(1)


DESCRIPTION = open("README.md", encoding="utf-8").read()

setup(
    name="ftfy",
    version="6.2.3",
    maintainer="Robyn Speer",
    maintainer_email="rspeer@arborelia.net",
    license="Apache 2.0",
    url="http://github.com/rspeer/python-ftfy",
    platforms=["any"],
    description="Fixes some problems with Unicode text after the fact",
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=["ftfy", "ftfy.bad_codecs"],
    install_requires=["wcwidth"],
    tests_require=["pytest"],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Development Status :: 5 - Production/Stable",
    ],
    entry_points={"console_scripts": ["ftfy = ftfy.cli:main"]},
    extras_require={"docs": ["furo", "sphinx"]},
    project_urls={
        "Documentation": "http://ftfy.readthedocs.io",
    },
)
