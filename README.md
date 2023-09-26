# wave-bwf-rf64

[![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech/)

Python modules for handling the Broadcast Wave Format and RF64 files.

Installing:

```shell
$ pip install wave-bwf-rf64
```

Basic example:

```python
import contextlib

import wave_bwf_rf64

with contextlib.closing(wave_bwf_rf64.open("input.wav", "rb")) as f:
    print("Num frames:", f.getnframes())
```

## Features

This package gives you the ability to work with both BWF and RF64 compatible WAV-files in Python.

Supported file IDs (first four bytes):

* RIFF
* RF64

Supported WAVE formats:

* PCM

Supported chunk types:

* ds64
* fmt
* data
* bext
* axml
* MD5
* levl
* chna
* r64m (only when reading)

This package's scope is limited to BWF and RF64 WAV files in the PCM format.
Feature requests and pull requests for other types of (WAV) files are outside of this scope and would increase our maintenance burden if accepted.
They will therefore not be considered.
You are, however, more than welcome to publish such additions in a fork of your own.


## Compatibility

This project requires Python version 3.10 or higher.


## Versioning

We use [semantic versioning](https://semver.org/spec/v2.0.0.html).

The Semantic Versioning Specification requires that we declare a public API.
We may only introduce breaking changes to this public API if we simultaneously increment the major version.
No such commitment is made for the parts of this project that are outside of the public API.

The public API is:
* `wave_bwf_rf64.open`
* `wave_bwf_rf64.chunk.Chunk`
* `wave_bwf_rf64.wave.`
  * `__all__`
  * `Error`
  * `WAVE_FORMAT_PCM`
  * `Bext`
  * `Chna`
  * `R64mMarker`
  * `R64m`
  * `Wave_read`
  * `Wave_write`
  * `open`
* All methods and attributes of any classes mentioned above, where the method or attribute name does not start with an underscore (`!= _*`)
* All methods and attributes of any classes mentioned above, where the method or attribute name is a [system-defined name], i.e. their name starts and ends with two underscores (`== __*__`)

[system-defined name]: https://docs.python.org/3/reference/datamodel.html#specialnames


## License

This project is licensed under the GNU General Public License version 3 or later.
See [LICENSE](LICENSE) for details.

`wave-bwf-rf64` is a modified version of BBC's `wave-bwf` project.
The latter is, to the best of our knowledge, no longer available.
See the [changelog](CHANGELOG.md) for the history of this project, which spans back to 2014/2015.


## Known issues

* There is no rendered documentation for the `open` function and the classes it may return
* The `open` function does not accept `pathlib.Path` objects
* The object returned by `open` is not a context manager, so it cannot be used with a `with` statement directly
* Issues where the size in the RIFF file header is too small or equal to 0, as may be the case when a recording was abruptly stopped or is accessed mid-recording, are not handled gracefully
* The project is lacking quality control
* The project is missing type annotations, so type checkers and IDEs may not help you so much


## Specifications

* Primary specification: [Recommendation ITU-R BS.2088-1](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.2088-1-201910-I!!PDF-E.pdf)
* Superseded specification containing information on the RF64 marker chunk (r64m): [EBU-TECH 3306: MBWF/RF64: An extended File Format for Audio](https://tech.ebu.ch/docs/tech/tech3306v1_1.pdf)


## Modules

### chunk.py

[The original Python module for handling RIFF chunks][chunk] with extensions for handling RF64.

### wave.py

Extension of the Python Standard Library's [wave module][wave] with BWF handling added (bext, chna, axml, md5 and levl chunks).

[chunk]: https://docs.python.org/3.11/library/chunk.html
[wave]: https://docs.python.org/3.11/library/wave.html


## Todo

* Incorporate changes made to the [chunk] and [wave] modules in the Python Standard Library after this fork was made
* Adapt tests from the Python Standard Library and expand them with tests for the added functionality
* Adapt documentation from the Python Standard Library and expand it with descriptions of the added functionality
* Run tests and other quality control tools automatically
* Set up automatic release pipeline
* Refactor the user-facing API for easier use
* Refactor the internals, so that type checking works and the code is more readable
