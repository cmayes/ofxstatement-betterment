#!/usr/bin/python3
"""Setup
"""
from setuptools import find_packages
from distutils.core import setup
import ofxstatement

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'ofxstatement'
]

setup(name='ofxstatement-betterment',
      version=ofxstatement.plugins.betterment.__version__,
      author="Chris Mayes",
      author_email="cmayes@cmay.es",
      url="https://github.com/cmayes/ofxstatement-betterment",
      description=("Betterment plugin for ofxstatement"),
      long_description=readme + '\n\n' + history,
      license="GPLv3",
      keywords=["ofx", "banking", "statement"],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3',
          'Natural Language :: English',
          'Topic :: Office/Business :: Financial :: Accounting',
          'Topic :: Utilities',
          'Environment :: Console',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU Affero General Public License v3'],
      packages=find_packages('src'),
      package_dir={'': 'src'},
      namespace_packages=["ofxstatement", "ofxstatement.plugins"],
      entry_points={
          'ofxstatement':
          ['betterment = ofxstatement.plugins.betterment:BettermentPlugin']
          },
      install_requires=['ofxstatement'],
      include_package_data=True,
      zip_safe=True
      )
