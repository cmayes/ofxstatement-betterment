.. :changelog:


History
-------

0.3.0 (2015-11-15)
------------------

* Updated to support newer CSV format by using header row rather than index, support
  the new date format, and sort by date for beginning and ending balance.

0.2.4 (2015-10-18)
------------------

* Changed to a SHA-256 hash for the pseudo-unique transaction ID in order to improve
  ID stability while preserving uniqueness.

0.2.2 (2015-10-04)
------------------

* Added filter to remove pending transactions (which have a blank ending balance)

0.2.1 (2015-09-27)
------------------

* Small documentation improvements.

0.2.0 (2015-09-27)
------------------

* Added tests
* Wired up to Travis CI
* Added coveralls test coverage reporting.

0.1.0 (2015-09-26)
------------------

* Uploaded to pypi
* Added to github
