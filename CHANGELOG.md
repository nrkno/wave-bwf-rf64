# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The declaration of this project's public API can be found in the [`README.md`](README.md#versioning).


## [Unreleased]

This patch adds support for Python version 3.13 and above.

### Added

- Support for Python 3.13 and above
- Copyright and license notices for the original code from the Python project

### Changed

- The `byteswap` function from `audioop` is replaced by a Python implementation when missing.
  It will likely be slower than before.
  
  This function is used when reading or writing audio frames with a bytesize greater than 1
  on a big-endian computer, so this probably does not affect you.
  If it does, you can try installing a compatible Pypi package that provides `audioop`.

  Note that this means that the deprecated `audioop` module will still be in use when you use Python <= 3.12.
  The warning `DeprecationWarning: 'audioop' is deprecated and slated for removal in Python 3.13` will therefore still be emitted.
  You can safely ignore this warning when it is emitted from this version of `wave_bwf_rf64.wave`.
  To avoid the warning, you can configure Python to ignore or raise it instead of printing it, for example by starting Python
  with `-W error::DeprecationWarning:wave_bwf_rf64.wave` .


## [2.0.1] - 2023-09-29

This patch release contains no code changes.

### Fixed

- Improve how the project is presented on Pypi.org


## [2.0.0] - 2023-09-28

This is the first public release of NRK's fork of BBC's fork of the Python Standard Library.

### Added

- Semantic versioning
- A proper `README.md`, including a declaration of which parts are considered our public API with respect to semantic versioning
- Project metadata in `pyproject.toml`, a format which does not require execution of Python code

### Changed

- The project is structured using [the src layout][src layout], with the modules living inside a package.
  You must update your `import` statements accordingly:
  - `import wave_bwf_levl_RF64` → `import wave_bwf_rf64` if you only need `open()`
  - `import wave_bwf_levl_RF64` → `import wave_bwf_rf64.wave` if you need access to the classes directly
  - `import chunk_levl_RF64` → `import wave_bwf_rf64.chunk`

[src layout]: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/


## [1.1.0] - 2022-12-07

### Added
- Support for reading RF64 markers from `r64m` chunks


## [1.0.6] - 2017-12-14

### Added
- Support for Python v3.5 or higher

### Removed
- Support for Python v2


## [1.0.5] - 2017-01-02

### Added
- Added a new method on the Wave_write class to update an existing BEXT coding history
  field. Important as we always want to retain the encoding history the audio file has
  been through


## [1.0.4] - 2016-12-12

No changelog was provided.


## [1.0.3] - 2015-09-02

No changelog was provided.

There is no recorded commit for release 1.0.2.


## [1.0.1] - 2015-01-30

No changelog was provided.


## Older releases

This package is based on the [chunk] and [wave] modules from the Python Standard Library.

David Marston of BBC added support for Broadcast Wave File (BWF).

The addition of the `MD5` and `levl` chunks and the `RF64` support was implemented by Tormod Værvågen of NRK (Norwegian Broadcasting Corporation).

BBC's fork was public at the time, but has since been taken down.

[chunk]: https://docs.python.org/3.11/library/chunk.html
[wave]: https://docs.python.org/3.11/library/wave.html

<!-- Links to GitHub diffs for all linked versions -->
[unreleased]: https://github.com/nrkno/wave-bwf-rf64/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/nrkno/wave-bwf-rf64/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/nrkno/wave-bwf-rf64/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/nrkno/wave-bwf-rf64/compare/v1.0.6...v1.1.0
[1.0.6]: https://github.com/nrkno/wave-bwf-rf64/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/nrkno/wave-bwf-rf64/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/nrkno/wave-bwf-rf64/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/nrkno/wave-bwf-rf64/compare/v1.0.1...v1.0.3
[1.0.1]: https://github.com/nrkno/wave-bwf-rf64/releases/tag/v1.0.1
