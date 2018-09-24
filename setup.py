import sys

# Before we get to the rest of setup, with dependencies on setuptools and the
# Python 3 standard library, let's make sure we're not on Python 2 and provide
# a helpful message if we are.

PY2_MESSAGE = """
Sorry, this version of ftfy is no longer written for Python 2.

The older version of ftfy, version 4.4, is still available and can run on
Python 2. Try this:

    pip install ftfy==4.4.3
"""

if sys.version_info[0] < 3:
    print(PY2_MESSAGE)
    readable_version = sys.version.split(' ')[0]
    print("The version of Python you're running is: %s" % readable_version)
    print("Python is running from: %r" % sys.executable)
    sys.exit(1)


from setuptools import setup

DESCRIPTION = open('README.md', encoding='utf-8').read()

setup(
    name="ftfy",
    version='5.5.0',
    maintainer='Luminoso Technologies, Inc.',
    maintainer_email='info@luminoso.com',
    license="MIT",
    url='http://github.com/LuminosoInsight/python-ftfy',
    platforms=["any"],
    description="Fixes some problems with Unicode text after the fact",
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    packages=['ftfy', 'ftfy.bad_codecs'],
    package_data={'ftfy': ['char_classes.dat']},
    install_requires=['wcwidth'],
    tests_require=['pytest'],
    python_requires='>=3.3',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
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
    },
    project_urls={
        'Documentation': 'http://ftfy.readthedocs.io',
    }
)
