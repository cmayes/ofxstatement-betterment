#!/usr/bin/python3
"""Setup
"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'ofxstatement'
]

setup(name='ofxstatement-betterment',
      version='0.1.0',
      author="Chris Mayes",
      author_email="cmayes@cmay.es",
      url="https://github.com/cmayes/ofxstatement-betterment",
      description="Betterment plugin for ofxstatement",
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
      packages=[
          'ofxstatement', 'ofxstatement.plugins',
      ],
      package_dir={'ofxstatement': 'ofxstatement',
                   'ofxstatement.plugins': 'ofxstatement/plugins'},
      namespace_packages=["ofxstatement", "ofxstatement.plugins"],
      entry_points={
          'ofxstatement':
              ['betterment = ofxstatement.plugins.betterment:BettermentPlugin']
      },
      install_requires=requirements,
      include_package_data=True,
      zip_safe=True,
      test_suite='tests',
      tests_require=requirements
      )
