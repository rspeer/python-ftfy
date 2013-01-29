from setuptools import setup

setup(
    name="ftfy",
    version='2.0',
    maintainer='Luminoso, LLC',
    maintainer_email='dev@lumino.so',
    license="MIT",
    url='http://github.com/LuminosoInsight/ftfy',
    platforms=["any"],
    description="Fixes some problems with Unicode text after the fact",
    packages=['ftfy'],
    entry_points={
        'console_scripts': [
            'ftfy = ftfy.cli:main'
        ]
    }
)
