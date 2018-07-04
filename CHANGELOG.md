# Change Log
This documents the (major) changes to the python wave library with support for both
BWF and RF64 versions of the WAVE / RIFF format.

## [1.0.6] - 2017-12-14
### Changed
- Updated to support Python3. We are no longer python2 friendly.

## [1.0.5] - 2017-01-02
### Added
- Added a new method on the Wave_write class to update an existing BEXT coding history
  field. Important as we always want to retain the encoding history the audio file has
  been through
