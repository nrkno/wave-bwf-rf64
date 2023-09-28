"""Stuff to parse WAVE files.

Copyright 2014 British Broadcasting Corporation.
Modified by NRK 2015-2023.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Usage.

Reading WAVE files:
      f = wave.open(file, 'r')
where file is either the name of a file or an open file pointer.
The open file pointer must have methods read(), seek(), and close().
When the setpos() and rewind() methods are not used, the seek()
method is not  necessary.

This returns an instance of a class with the following public methods:
      getnchannels()  -- returns number of audio channels (1 for
                         mono, 2 for stereo)
      getsampwidth()  -- returns sample width in bytes
      getframerate()  -- returns sampling frequency
      getnframes()    -- returns number of audio frames
      getcomptype()   -- returns compression type ('NONE' for linear samples)
      getcompname()   -- returns human-readable version of
                         compression type ('not compressed' linear samples)
      getparams()     -- returns a tuple consisting of all of the
                         above in the above order
      getmarkers()    -- returns None (for compatibility with the
                         aifc module)
      getmark(id)     -- raises an error since the mark does not
                         exist (for compatibility with the aifc module)
      readframes(n)   -- returns at most n frames of audio
      rewind()        -- rewind to the beginning of the audio stream
      setpos(pos)     -- seek to the specified position
      tell()          -- return the current position
      close()         -- close the instance (make it unusable)

The position returned by tell() and the position given to setpos()
are compatible and have nothing to do with the actual position in the
file.
The close() method is called automatically when the class instance
is destroyed.

bext chunk methods:
      get_bext_description()                -- get description (returns max 256 chars)
      get_bext_originator()                 -- get originator (returns max 32 chars)
      get_bext_originator_reference()       -- get originator reference (returns max 32 chars)
      get_bext_origination_date()           -- get origination date (returns [year, month, day])
      get_bext_origination_time()           -- get origination date (returns [hours, minutes, seconds])
      get_bext_time_reference()             -- get time reference (returns [high, low])
      get_bext_umid()                       -- get UMID (returns list of 64 chars)
      get_bext_loudness_value()             -- get loudness value (returns float)
      get_bext_loudness_range()             -- get loudness range (returns float)
      get_bext_max_true_peak_level()        -- get max true peak level (returns float)
      get_bext_max_momentary_loudness()     -- get max momentary loudness (returns float)
      get_bext_max_short_term_loudness()    -- get max momentary loudness (returns float)
      get_bext_coding_history()             -- get coding history (returns any number of chars)



Writing WAVE files:
      f = wave.open(file, 'w')
where file is either the name of a file or an open file pointer.
The open file pointer must have methods write(), tell(), seek(), and
close().

This returns an instance of a class with the following public methods:
      setnchannels(n) -- set the number of channels
      setsampwidth(n) -- set the sample width
      setframerate(n) -- set the frame rate
      setnframes(n)   -- set the number of frames
      setcomptype(type, name)
                      -- set the compression type and the
                         human-readable compression type
      setparams(tuple)
                      -- set all parameters at once
      tell()          -- return current position in output file
      writeframesraw(data)
                      -- write audio frames without pathing up the
                         file header
      writeframes(data)
                      -- write audio frames and patch up the file header
      close()         -- patch up the file header and close the
                         output file

bext chunk methods:
      set_bext_description(string)          -- set description (max 256 chars)
      set_bext_originator(string)           -- set originator (max 32 chars)
      set_bext_originator_reference(data)   -- set originator reference (max 32 chars)
      set_bext_origination_date(tuple)      -- set origination date ([year, month, day])
      set_bext_origination_time(tuple)      -- set origination date ([hours, minutes, seconds])
      set_bext_time_reference(tuple)        -- set time reference ([high, low])
      set_bext_umid(tuple)                  -- set UMID (list of 64 chars)
      set_bext_loudness_value(n)            -- set loudness value (float)
      set_bext_loudness_range(n)            -- set loudness range (float)
      set_bext_max_true_peak_level(n)       -- set max true peak level (float)
      set_bext_max_momentary_loudness(n)    -- set max momentary loudness (float)
      set_bext_max_short_term_loudness(n)   -- set max momentary loudness (float)
      set_bext_coding_history(string)       -- set coding history (any number of chars)
      set_bext()                            -- update bext chunk before writing to file (must be done)

You should set the parameters before the first writeframesraw or
writeframes.  The total number of frames does not need to be set,
but when it is set to the correct value, the header does not have to
be patched up.
It is best to first set all parameters, perhaps possibly the
compression type, and then write audio frames using writeframesraw.
When all frames have been written, either call writeframes('') or
close() to patch up the sizes in the header.
The close() method is called automatically when the class instance
is destroyed.
"""

# import __builtin__
import builtins

__all__ = ["open", "openfp", "Error", "R64mMarker"]

import dataclasses
import enum
import typing
import audioop
import struct
import sys

from .chunk import Chunk
from collections import namedtuple
import datetime


class Error(Exception):
    pass


WAVE_FORMAT_PCM = 0x0001
# Not supported, as the parsing that existed just blew up with an AttributeError on
# read/open..
WAVE_FORMAT_MPEG = 0x0050
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

_array_fmts = None, 'b', 'h', None, 'l'


_wave_params = namedtuple('_wave_params',
                          'nchannels sampwidth framerate nframes comptype compname')


class Bext:
    def __init__(self):
        self._description = None
        self._originator = None
        self._originator_reference = None
        now = datetime.datetime.now()
        self._origination_date = [now.year, now.month, now.day]
        self._origination_time = [now.hour, now.minute, now.second]
        self._time_reference = [0, 0]
        self._version = 1
        self._umid = [b'\0']*64
        self._loudness_value = 0x7fff
        self._loudness_range = 0x7fff
        self._max_true_peak_level = 0x7fff
        self._max_momentary_loudness = 0x7fff
        self._max_short_term_loudness = 0x7fff
        self._coding_history = b''
        self._loudness_params_pos = 344

    def pack_chunk(self):
        chunk = struct.pack('<0256s', self._description)
        chunk += struct.pack('<032s', self._originator)
        chunk += struct.pack('<032s', self._originator_reference)
        chunk += struct.pack('<04s', ('{0:04d}'.format(
            self._origination_date[0]).encode('utf-8')))
        chunk += b'-'
        chunk += struct.pack('<02s', ('{0:02d}'.format(
            self._origination_date[1]).encode('utf-8')))
        chunk += b'-'
        chunk += struct.pack('<02s', ('{0:02d}'.format(
            self._origination_date[2]).encode('utf-8')))
        chunk += struct.pack('<02s', ('{0:02d}'.format(
            self._origination_time[0]).encode('utf-8')))
        chunk += b'-'
        chunk += struct.pack('<02s', ('{0:02d}'.format(
            self._origination_time[1]).encode('utf-8')))
        chunk += b'-'
        chunk += struct.pack('<02s', ('{0:02d}'.format(
            self._origination_time[2]).encode('utf-8')))
        chunk += struct.pack('<ll', self._time_reference[0], self._time_reference[1])
        chunk += struct.pack('<h', self._version)
        for i in range(0, 64):
            chunk += struct.pack('<c', self._umid[i])
        self._loudness_params_pos = len(chunk)
        if self._version >= 2:
            chunk += struct.pack('<h', self._loudness_value)
            chunk += struct.pack('<h', self._loudness_range)
            chunk += struct.pack('<h', self._max_true_peak_level)
            chunk += struct.pack('<h', self._max_momentary_loudness)
            chunk += struct.pack('<h', self._max_short_term_loudness)
        else:
            for i in range(0, 10):
                chunk += b'\0'
        for i in range(0, 180):
            chunk += b'\0'
        chunk += self._coding_history
        if (len(self._coding_history) % 2) == 1:
            chunk += b'\0'
        return chunk

    def unpack_chunk(self, chunk):
        chunk.seek(0, 0)
        self._description = struct.unpack('<0256s', chunk.read(256))[0]
        self._originator = struct.unpack('<032s', chunk.read(32))[0]
        self._originator_reference = struct.unpack('<032s', chunk.read(32))[0]
        self._origination_date[0] = int(struct.unpack('<04s', chunk.read(4))[0])
        chunk.read(1)
        self._origination_date[1] = int(struct.unpack('<02s', chunk.read(2))[0])
        chunk.read(1)
        self._origination_date[2] = int(struct.unpack('<02s', chunk.read(2))[0])
        self._origination_time[0] = int(struct.unpack('<02s', chunk.read(2))[0])
        chunk.read(1)
        self._origination_time[1] = int(struct.unpack('<02s', chunk.read(2))[0])
        chunk.read(1)
        self._origination_time[2] = int(struct.unpack('<02s', chunk.read(2))[0])
        self._time_reference[0], self._time_reference[1] = struct.unpack('<ll', chunk.read(8))
        self._version = struct.unpack('<h', chunk.read(2))[0]

        for i in range(0, 64):
            self._umid[i] = struct.unpack('<c', chunk.read(1))[0]
        if self._version >= 2:
            self._loudness_value = struct.unpack('<h', chunk.read(2))[0]
            self._loudness_range = struct.unpack('<h', chunk.read(2))[0]
            self._max_true_peak_level = struct.unpack('<h', chunk.read(2))[0]
            self._max_momentary_loudness = struct.unpack('<h', chunk.read(2))[0]
            self._max_short_term_loudness = struct.unpack('<h', chunk.read(2))[0]
        else:
            chunk.read(10)
        chunk.read(180)
        self._coding_history = chunk.read(-1)

    def scaleup(self, val):
        x = 0
        if val >= 0.0 and val < 100.0:
            x = int((100.0 * val) + 0.5)
        elif val > -100.0:
            x = int((100.0 * val) - 0.5)
        else:
            x = 0x7fff
        return x

    def scaledown(self, val):
        x = None
        if val != 0x7fff:
            x = float(val) / 100.0
        return x

    def generate_coding_history(self, framerate, sampwidth, nchannels):
        """The format of the coding_history is based on EBU R98-1999"""
        if nchannels == 1:
            chnstr = b'mono'
        elif nchannels == 2:
            chnstr = b'stereo'
        else:
            chnstr = b'%d' % (nchannels)
        self._coding_history = b'A=PCM,F=%u,W=%hu,M=%s,T=%s-%s\r\n' % (
            framerate, sampwidth * 8, chnstr, b'wave_bwf_levl_RF64.py', b'1.0.6')
        if (len(self._coding_history) % 2) == 1:
            self._coding_history += b'\0'

    def loudness_params_pos(self):
        return self._loudness_params_pos

    def rewrite_loudness_parameters(self):
        chunk = struct.pack('<h', self._loudness_value)
        chunk += struct.pack('<h', self._loudness_range)
        chunk += struct.pack('<h', self._max_true_peak_level)
        chunk += struct.pack('<h', self._max_momentary_loudness)
        chunk += struct.pack('<h', self._max_short_term_loudness)
        return chunk


class Chna:
    def __init__(self):
        self._num_tracks = 0
        self._num_uids = 0
        self._ch_id = []

    def add_new_track(self, track_idx, track_uid, track_ref, pack_ref):
        ch_id = []
        ch_id.append(track_idx)   # WORD
        ch_id.append(track_uid)   # string[12]
        ch_id.append(track_ref)   # string[14]
        ch_id.append(pack_ref)    # string[11]
        self._ch_id.append(ch_id)
        self._num_tracks += 1
        self._num_uids += 1

    def add_existing_track(self, track_idx, track_uid, track_ref, pack_ref):
        ch_id = []
        ch_id.append(track_idx)   # WORD
        ch_id.append(track_uid)   # string[12]
        ch_id.append(track_ref)   # string[14]
        ch_id.append(pack_ref)    # string[11]
        self._ch_id.append(ch_id)
        self._num_uids += 1

    def read_num_tracks(self):
        return self._num_tracks

    def read_num_uids(self):
        return self._num_uids

    def read_track(self, num):
        return self._ch_id[num]

    def pack_chunk(self):
        chunk = struct.pack('<h', self._num_tracks)
        chunk += struct.pack('<h', self._num_uids)
        for i in range(self._num_uids):
            chunk += struct.pack('<H', (self._ch_id[i][0]))      # track_idx
            chunk += struct.pack('<012s', (self._ch_id[i][1]))   # track_uid
            chunk += struct.pack('<014s', (self._ch_id[i][2]))   # track_ref
            chunk += struct.pack('<011s', (self._ch_id[i][3]))   # pack_ref
            chunk += struct.pack('<c', '\0')                     # padding
        if self._num_uids < 32:
            ex_uids = 32
        else:
            ex_uids = 2048
        for i in range(ex_uids - self._num_uids):
            chunk += struct.pack('<H', 0)      # track_idx
            chunk += struct.pack('<012s', '\0')   # track_uid
            chunk += struct.pack('<014s', '\0')   # track_ref
            chunk += struct.pack('<011s', '\0')   # pack_ref
            chunk += struct.pack('<c', '\0')    # padding
        return chunk

    def unpack_chunk(self, chunk):
        chunk.seek(0, 0)
        self._num_tracks = struct.unpack('<h', chunk.read(2))[0]
        self._num_uids = struct.unpack('<h', chunk.read(2))[0]
        self._ch_id = []
        for i in range(self._num_uids):
            ch_id = []
            ch_id.append(struct.unpack('<H', chunk.read(2))[0])       # track_idx
            ch_id.append(struct.unpack('<012s', chunk.read(12))[0])   # track_uid
            ch_id.append(struct.unpack('<014s', chunk.read(14))[0])   # track_ref
            ch_id.append(struct.unpack('<011s', chunk.read(11))[0])   # pack_ref
            chunk.read(1)                   # padding
            self._ch_id.append(ch_id)


@dataclasses.dataclass
class R64mMarker:
    sample_offset: int
    time_offset: datetime.timedelta
    label: str


class RawR64mMarkerEntry(typing.NamedTuple):
    flags: int
    sample_offset: int
    byte_offset: int
    intra_sample_offset: int
    label_text: bytes
    label_chunk_identifier: int
    vendor_and_product: bytes
    user_data_1: int
    user_data_2: int
    user_data_3: int
    user_data_4: int


class MarkerEntryFlags(enum.Flag):
    ENTRY_IS_VALID = enum.auto()
    BYTE_OFFSET_IS_VALID = enum.auto()
    INTRA_SAMPLE_OFFSET_IS_VALID = enum.auto()
    LABEL_IS_IN_LABL_CHUNK = enum.auto()
    LABEL_TEXT_IS_UTF_8 = enum.auto()


class R64m:
    def __init__(self):
        self._markers: list[R64mMarker] = []

    def read_markers(self):
        return self._markers

    def unpack_chunk(self, chunk: Chunk, sample_rate: int):
        chunk.seek(0, 0)
        chunk_size = chunk.getsize()
        while chunk.tell() < chunk_size:
            raw_values = struct.unpack("<L Q Q Q 256s L 16s 4L", chunk.read(320))
            marker_entry = RawR64mMarkerEntry._make(raw_values)

            flags = MarkerEntryFlags(marker_entry.flags)
            if MarkerEntryFlags.ENTRY_IS_VALID not in flags:
                continue

            sample_offset = marker_entry.sample_offset
            seconds_offset = sample_offset / sample_rate
            time_offset = datetime.timedelta(seconds=seconds_offset)

            if MarkerEntryFlags.LABEL_TEXT_IS_UTF_8 in flags:
                encoding = "utf-8"
            else:
                encoding = "windows-1252"
            label_until_null = marker_entry.label_text.rstrip(b'\x00')
            label = label_until_null.decode(encoding)
            self._markers.append(R64mMarker(sample_offset, time_offset, label))


class Wave_read:
    """Variables used in this class:

    These variables are available to the user though appropriate
    methods of this class:
    _file -- the open file with methods read(), close(), and seek()
              set through the __init__() method
    _nchannels -- the number of audio channels
              available through the getnchannels() method
    _nframes -- the number of audio frames
              available through the getnframes() method
    _sampwidth -- the number of bytes per audio sample
              available through the getsampwidth() method
    _framerate -- the sampling frequency
              available through the getframerate() method
    _comptype -- the AIFF-C compression type ('NONE' if AIFF)
              available through the getcomptype() method
    _compname -- the human-readable AIFF-C compression type
              available through the getcomptype() method
    _soundpos -- the position in the audio stream
              available through the tell() method, set through the
              setpos() method

    These variables are used internally only:
    _fmt_chunk_read -- 1 iff the FMT chunk has been read
    _data_seek_needed -- 1 iff positioned correctly in audio
              file for readframes()
    _data_chunk -- instantiation of a chunk class for the DATA chunk
    _framesize -- size of one frame in the file
    """

    def initfp(self, file):
        self._convert = None
        self._soundpos = 0
        self._file = Chunk(file, bigendian=0)
        # ** Check for RF64 header
        # ** If present, read special chunk
        if self._file.getname() not in [b'RIFF', b'RF64']:  # ** Support RF64
            raise Error('file does not start with RIFF id')
        if self._file.read(4) != b'WAVE':
            raise Error('not a WAVE file')
        self._fmt_chunk_read = 0
        self._data_chunk = None
        self._bext_chunk = None
        self._axml_chunk = None
        self._md5_chunk = None
        self._levl_chunk = None
        self._chna_chunk = None
        self._r64m_chunk = None
        self._bext = Bext()
        self._chna = Chna()
        self._r64m = R64m()

        # Check for RF64
        if self._file.getname() == b'RF64':
            self._RF64 = True
            ds64 = Chunk(self._file, bigendian=0)
            self._read_ds64_chunk(ds64)

            # Correct the file length
            self._file.setsize(self._riffSize)

        else:
            self._RF64 = False
            self.dataSize = None

        while 1:
            self._data_seek_needed = 1
            try:
                # RF64 set new data length
                chunk = Chunk(self._file, bigendian=0, set_data_chunk_size=self.dataSize)
            except EOFError:
                break
            chunkname = chunk.getname()
            if chunkname == b'fmt ':
                self._read_fmt_chunk(chunk)
                self._fmt_chunk_read = 1
            elif chunkname == b'data':
                # ** RF64 check real length
                if not self._fmt_chunk_read:
                    raise Error('data chunk before fmt chunk')
                self._data_chunk = chunk
                self._nframes = chunk.chunksize // self._framesize  # ** Chunksize may be FFFFFFFF read real length from separate chunk
                self._data_seek_needed = 0
                # break
            elif chunkname == b'bext':
                self._bext_chunk = chunk
            elif chunkname == b'axml':
                self._axml_chunk = chunk
            elif chunkname == b'MD5 ':
                self._md5_chunk = chunk
            elif chunkname == b'levl':
                self._levl_chunk = chunk
            elif chunkname == b'chna':
                self._chna_chunk = chunk
            elif chunkname == b'r64m':
                self._r64m_chunk = chunk
            chunk.skip()
        if not self._fmt_chunk_read or not self._data_chunk:
            raise Error('fmt chunk and/or data chunk missing')

    def __init__(self, f):
        self._i_opened_the_file = None
        if isinstance(f, str):
            f = builtins.open(f, 'rb')
            self._i_opened_the_file = f
        # else, assume it is an open file object already
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def __del__(self):
        self.close()
    #
    # User visible methods.
    #
    def getfp(self):
        return self._file

    def rewind(self):
        self._data_seek_needed = 1
        self._soundpos = 0

    def close(self):
        if self._i_opened_the_file:
            self._i_opened_the_file.close()
            self._i_opened_the_file = None
        self._file = None

    def tell(self):
        return self._soundpos

    def getnchannels(self):
        return self._nchannels

    def getnframes(self):
        return self._nframes

    def getsampwidth(self):
        return self._sampwidth

    def getframerate(self):
        return self._framerate

    def getcomptype(self):
        return self._comptype

    def getcompname(self):
        return self._compname

    def getparams(self):
        return self.getnchannels(), self.getsampwidth(), \
               self.getframerate(), self.getnframes(), \
               self.getcomptype(), self.getcompname()

    def getmarkers(self):
        return None

    def getmark(self, id):
        raise Error('no marks')

    def setpos(self, pos):
        if pos < 0 or pos > self._nframes:
            raise Error('position not in range')
        self._soundpos = pos
        self._data_seek_needed = 1

    def readframes(self, nframes):
        if self._data_seek_needed:
            self._data_chunk.seek(0, 0)
            pos = self._soundpos * self._framesize
            if pos:
                self._data_chunk.seek(pos, 0)
            self._data_seek_needed = 0
        if nframes == 0:
            return b''
        data = self._data_chunk.read(nframes * self._framesize)
        if self._sampwidth != 1 and sys.byteorder == 'big':
            data = audioop.byteswap(data, self._sampwidth)
            # # unfortunately the fromfile() method does not take
            # # something that only looks like a file object, so
            # # we have to reach into the innards of the chunk object
            # import array
            # chunk = self._data_chunk
            # data = array.array(_array_fmts[self._sampwidth])
            # nitems = nframes * self._nchannels
            # if nitems * self._sampwidth > chunk.chunksize - chunk.size_read:
            #     nitems = (chunk.chunksize - chunk.size_read) / self._sampwidth
            # data.fromfile(chunk.file.file, nitems)
            # # "tell" data chunk how much was read
            # chunk.size_read = chunk.size_read + nitems * self._sampwidth
            # # do the same for the outermost chunk
            # chunk = chunk.file
            # chunk.size_read = chunk.size_read + nitems * self._sampwidth
            # data.byteswap()
            # data = data.tostring()
        if self._convert and data:
            data = self._convert(data)
        self._soundpos = self._soundpos + len(data) // (self._nchannels * self._sampwidth)
        return data

    def read_bext(self):
        if not self._bext_chunk:
            return False
        self._bext.unpack_chunk(self._bext_chunk)
        return True

    def get_bext_description(self):
        return self._bext._description

    def get_bext_originator(self):
        return self._bext._originator

    def get_bext_originator_reference(self):
        return self._bext._originator_reference

    def get_bext_origination_date(self):
        return self._bext._origination_date

    def get_bext_origination_time(self):
        return self._bext._origination_time

    def get_bext_time_reference(self):
        return self._bext._time_reference

    def get_bext_umid(self):
        return self._bext._umid

    def get_bext_version(self):
        return self._bext._version

    def get_bext_loudness_value(self):
        return self._bext.scaledown(self._bext._loudness_value)

    def get_bext_loudness_range(self):
        return self._bext.scaledown(self._bext._loudness_range)

    def get_bext_max_true_peak_level(self):
        return self._bext.scaledown(self._bext._max_true_peak_level)

    def get_bext_max_momentary_loudness(self):
        return self._bext.scaledown(self._bext._max_momentary_loudness)

    def get_bext_max_short_term_loudness(self):
        return self._bext.scaledown(self._bext._max_short_term_loudness)

    def get_bext_coding_history(self):
        return self._bext._coding_history

    def get_bext_chunk(self):
        self._bext.unpack_chunk(self._bext_chunk)
        return self._bext.pack_chunk()

    def read_axml(self):
        if self._axml_chunk is not None:
            self._axml_chunk.seek(0, 0)
        else:
            return False
        data = self._axml_chunk.read()
        return data

    def read_md5(self):
        if self._md5_chunk is not None:
            self._md5_chunk.seek(0, 0)
        else:
            return False
        data = self._md5_chunk.read()
        return data

    def read_levl(self):
        if self._levl_chunk is not None:
            self._levl_chunk.seek(0, 0)
        else:
            return False
        data = self._levl_chunk.read()
        return data

    def get_chna_num_tracks(self):
        return self._chna.read_num_tracks()

    def get_chna_num_uids(self):
        return self._chna.read_num_uids()

    def get_chna_track(self, num):
        return self._chna.read_track(num)

    def read_chna(self):
        if not self._chna_chunk:
            return False
        self._chna.unpack_chunk(self._chna_chunk)
        return True

    def read_r64m(self):
        if not self._r64m_chunk:
            return False
        self._r64m.unpack_chunk(self._r64m_chunk, self.getframerate())
        return True

    def get_r64m_markers(self):
        return self._r64m.read_markers()

    #
    # Internal methods.
    #

    def _read_fmt_chunk(self, chunk):
        wFormatTag, self._nchannels, self._framerate, dwAvgBytesPerSec, wBlockAlign = struct.unpack('<Hhllh', chunk.read(14))
        if wFormatTag == WAVE_FORMAT_PCM:
            sampwidth = struct.unpack('<h', chunk.read(2))[0]
            self._sampwidth = (sampwidth + 7) // 8
        elif wFormatTag == WAVE_FORMAT_EXTENSIBLE:
            sampwidth, cbSize = struct.unpack('<hh', chunk.read(4))
            self._sampwidth = (sampwidth + 7) // 8
            if cbSize != 22:
                raise Error('WAVE_FORMAT_EXTENSIBLE format, wrong cbSize: %r' % (cbSize))
            subFormat = [0, 0, 0, 0]
            wValidBitsPerSample, dwChannelMask, subFormat[0], subFormat[1], subFormat[2], subFormat[3] = struct.unpack('<hLLLLL', chunk.read(22))
        else:
            raise Error('unknown format: %r' % (wFormatTag,))
        self._framesize = self._nchannels * self._sampwidth
        self._comptype = 'NONE'
        self._compname = 'not compressed'


    def _read_ds64_chunk(self, chunk):
        self._riffSize, self.dataSize, self.sampleCount, self._tableLength = struct.unpack('<qqql', chunk.read(28))


class Wave_write:
    """Variables used in this class:

    These variables are user settable through appropriate methods
    of this class:
    _file -- the open file with methods write(), close(), tell(), seek()
              set through the __init__() method
    _comptype -- the AIFF-C compression type ('NONE' in AIFF)
              set through the setcomptype() or setparams() method
    _compname -- the human-readable AIFF-C compression type
              set through the setcomptype() or setparams() method
    _nchannels -- the number of audio channels
              set through the setnchannels() or setparams() method
    _sampwidth -- the number of bytes per audio sample
              set through the setsampwidth() or setparams() method
    _framerate -- the sampling frequency
              set through the setframerate() or setparams() method
    _nframes -- the number of audio frames written to the header
              set through the setnframes() or setparams() method

    These variables are used internally only:
    _datalength -- the size of the audio samples written to the header
    _nframeswritten -- the number of frames actually written
    _datawritten -- the size of the audio samples actually written
    """

    def __init__(self, f):
        self._i_opened_the_file = None
        if isinstance(f, str):
            f = builtins.open(f, 'wb')
            self._i_opened_the_file = f
        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise

    def initfp(self, file):
        self._file = file
        self._convert = None
        self._nchannels = 0
        self._sampwidth = 0
        self._framerate = 0
        self._nframes = 0
        self._nframeswritten = 0
        self._datawritten = 0
        self._datalength = 0

        self._bext_chunk_data = None
        self._axml_chunk_data = None
        self._md5_chunk_data = None
        self._levl_chunk_data = None
        self._chna_chunk_data = None
        self._bext = Bext()
        self._chna = Chna()

        self._headerwritten = False

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    #
    # User visible methods.
    #
    def setnchannels(self, nchannels):
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        if nchannels < 1:
            raise Error('bad # of channels')
        self._nchannels = nchannels

    def getnchannels(self):
        if not self._nchannels:
            raise Error('number of channels not set')
        return self._nchannels

    def setsampwidth(self, sampwidth):
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        if sampwidth < 1 or sampwidth > 4:
            raise Error('bad sample width')
        self._sampwidth = sampwidth

    def getsampwidth(self):
        if not self._sampwidth:
            raise Error('sample width not set')
        return self._sampwidth

    def setframerate(self, framerate):
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        if framerate <= 0:
            raise Error('bad frame rate')
        self._framerate = int(round(framerate))

    def getframerate(self):
        if not self._framerate:
            raise Error('frame rate not set')
        return self._framerate

    def setnframes(self, nframes):
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        self._nframes = nframes

    def getnframes(self):
        return self._nframeswritten

    def setcomptype(self, comptype, compname):
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        if comptype not in ('NONE',):
            raise Error('unsupported compression type')
        self._comptype = comptype
        self._compname = compname

    def getcomptype(self):
        return self._comptype

    def getcompname(self):
        return self._compname

    def setparams(self, params):
        nchannels, sampwidth, framerate, nframes, comptype, compname = params
        if self._datawritten:
            raise Error('cannot change parameters after starting to write')
        self.setnchannels(nchannels)
        self.setsampwidth(sampwidth)
        self.setframerate(framerate)
        self.setnframes(nframes)
        self.setcomptype(comptype, compname)

    def getparams(self):
        if not self._nchannels or not self._sampwidth or not self._framerate:
            raise Error('not all parameters set')
        return _wave_params(self._nchannels, self._sampwidth, self._framerate,
                            self._nframes, self._comptype, self._compname)

    def setmark(self, id, pos, name):
        raise Error('setmark() not supported')

    def getmark(self, id):
        raise Error('no marks')

    def getmarkers(self):
        return None

    def tell(self):
        return self._nframeswritten

    def writeframesraw(self, data):
        if not isinstance(data, (bytes, bytearray)):
            data = memoryview(data).cast('B')
        self._ensure_header_written(len(data))
        nframes = len(data) // (self._sampwidth * self._nchannels)
        if self._convert:
            data = self._convert(data)

        if self._sampwidth != 1 and sys.byteorder == 'big':
            data = audioop.byteswap(data, self._sampwidth)

        self._file.write(data)
        self._datawritten += len(data)
        self._nframeswritten = self._nframeswritten + nframes

    def writeframes(self, data):
        self.writeframesraw(data)
        if self._datalength != self._datawritten:
            self._patchheader()

    def close(self):
        try:
            if self._file:
                self._ensure_header_written(0)
                # if self._datalength != self._datawritten:
                self._patchheader()
                if self._axml_chunk_data:
                    self._write_axml_chunk()
                if self._levl_chunk_data:
                    self._write_levl_chunk()
                if self._md5_chunk_data:
                    self._write_md5_chunk()
                self._file.flush()
        finally:
            self._file = None
            file = self._i_opened_the_file
            if file:
                self._i_opened_the_file = None
                file.close()

    #
    # This is the expansion to support BWF/LEVL/RF64
    #

    def set_bext_description(self, val):
        self._bext._description = val

    def set_bext_originator(self, val):
        self._bext._originator = val

    def set_bext_originator_reference(self, val):
        self._bext._originator_reference = val

    def set_bext_origination_date(self, val):
        self._bext._origination_date = val

    def set_bext_origination_time(self, val):
        self._bext._origination_time = val

    def set_bext_time_reference(self, val):
        self._bext._time_reference = val

    def set_bext_umid(self, val):
        self._bext._umid = val

    def set_bext_loudness_value(self, val):
        self._bext._loudness_value = self._bext.scaleup(val)
        self._bext._version = 2

    def set_bext_loudness_range(self, val):
        self._bext._loudness_range = self._bext.scaleup(val)
        self._bext._version = 2

    def set_bext_max_true_peak_level(self, val):
        self._bext._max_true_peak_level = self._bext.scaleup(val)
        self._bext._version = 2

    def set_bext_max_momentary_loudness(self, val):
        self._bext._max_momentary_loudness = self._bext.scaleup(val)
        self._bext._version = 2

    def set_bext_max_short_term_loudness(self, val):
        self._bext._max_short_term_loudness = self._bext.scaleup(val)
        self._bext._version = 2

    def set_bext_coding_history(self, val):
        self._bext._coding_history = val

    def set_bext(self):
        if self._bext._coding_history == b'':
            self._bext.generate_coding_history(self._framerate,
                                               self._sampwidth, self._nchannels)
        self._bext_chunk_data = self._bext.pack_chunk()

    def update_bext_coding_history(self):
        """Update an existing bext coding history chunk with a new line."""
        old_history = self._bext._coding_history
        self._bext.generate_coding_history(self._framerate, self._sampwidth,
                                           self._nchannels)
        history_addition = self._bext._coding_history
        # Only add a newline to the old one if it didn't have one
        if old_history.endswith(b'\r\n'):
            self._bext._coding_history = old_history + history_addition
        else:
            self._bext._coding_history = old_history + b'\r\n' + history_addition

    def copy_bext(self, _bext_chunk):
        self._bext_chunk_data = _bext_chunk

    def set_axml(self, data):
        self._axml_chunk_data = data
        if (len(self._axml_chunk_data) % 2) == 1:
            self._axml_chunk_data += b' '

    def set_md5(self, data):
        self._md5_chunk_data = data
        if (len(self._md5_chunk_data) % 2) == 1:
            self._md5_chunk_data += b' '

    def set_levl(self, data):
        self._levl_chunk_data = data
        if (len(self._levl_chunk_data) % 2) == 1:
            self._levl_chunk_data += b' '  # Don't know if this is needed

    def chna_add_new_track(self, track_idx, track_uid, track_ref, pack_ref):
        self._chna.add_new_track(track_idx, track_uid, track_ref, pack_ref)

    def chna_add_existing_track(self, track_idx, track_uid, track_ref, pack_ref):
        self._chna.add_existing_track(track_idx, track_uid, track_ref, pack_ref)

    def set_chna(self):
        self._chna_chunk_data = self._chna.pack_chunk()

    #
    # Internal methods.
    #

    def _ensure_header_written(self, datasize):
        # if not self._datawritten:
        if not self._headerwritten:
            if not self._nchannels:
                raise Error('# channels not specified')
            if not self._sampwidth:
                raise Error('sample width not specified')
            if not self._framerate:
                raise Error('sampling rate not specified')

            self._write_header(datasize)
            if self._bext_chunk_data:
                self._write_bext_chunk()
            if self._chna_chunk_data:
                self._write_chna_chunk()

            self._write_data_header()

    def _write_header(self, initlength):
        # *** MOD
        assert not self._headerwritten
        if not self._nframes:
            self._nframes = initlength / (self._nchannels * self._sampwidth)
        self._datalength = self._nframes * self._nchannels * self._sampwidth

        # RF64 territory
        if self._datalength > 2140483647:  # eg 2147483647 - some space for other chunks
            self._type = b'RF64'
            self._file.write(b'RF64')
            self._form_length_pos = self._file.tell()
            self._file.write(struct.pack('<l', -1))
            self._file.write(b'WAVE')
            self._form_length_pos = self._file.tell()
            self._write_ds64_header()
            self._write_fmt()
        else:
            self._type = b'RIFF'
            self._file.write(b'RIFF')
            self._form_length_pos = self._file.tell()
            self._file.write(struct.pack('<L4s',
                                         36 + self._datalength, b'WAVE'))
            self._write_fmt()

        self._headerwritten = True

    # Add
    def _write_ds64_header(self, new_size=None):
        if not new_size:
            self._file.write(struct.pack(
                '<4slqqql', b'ds64', 28, self._datalength + 36 + 36,
                self._datalength, self._nframes, 0))
        else:
            self._file.write(struct.pack(
                '<4slqqql', b'ds64', 28, new_size + 36,
                self._datawritten, self._nframes, 0))

            # Add 36 byte for ds64 header

    def _write_fmt(self):
        self._file.write(struct.pack('<4slhhllhh',
                                     b'fmt ', 16,
                                     WAVE_FORMAT_PCM, self._nchannels, self._framerate,
                                     self._nchannels * self._framerate * self._sampwidth,
                                     self._nchannels * self._sampwidth,
                                     self._sampwidth * 8))

    def _write_data_header(self):
        self._file.write(struct.pack('<4s', b'data'))
        self._data_length_pos = self._file.tell()
        if self._type == b'RF64':
            self._file.write(struct.pack('<l', -1))
        else:
            self._file.write(struct.pack('<l', self._datalength))

    def _patchheader(self):
        # if self._datawritten == self._datalength:
        #    return
        # Mask values before struct.pack & 0xFFFFFFFF
        assert self._headerwritten
        curpos = self._file.tell()
        self._file.seek(self._form_length_pos, 0)
        new_size = 36                  # fmt chunk size
        new_size += self._datawritten  # data chunk size
        if self._bext_chunk_data:           # bext chunk size
            new_size += len(self._bext_chunk_data) + 8
        if self._chna_chunk_data:           # chna chunk size
            new_size += len(self._chna_chunk_data) + 8
        if self._axml_chunk_data:           # axml chunk size
            new_size += len(self._axml_chunk_data) + 8
        if self._md5_chunk_data:           # md5  chunk size
            new_size += len(self._md5_chunk_data) + 8
        if self._levl_chunk_data:           # levl chunk size
            new_size += len(self._levl_chunk_data) + 8
        if self._type == b'RF64':
            self._write_ds64_header(new_size)
        else:
            self._file.write(struct.pack('<l', new_size))
            self._file.seek(self._data_length_pos, 0)
            self._file.write(struct.pack('<l', self._datawritten))
        if self._bext_chunk_data:
            self._file.seek(self._loudness_params_pos, 0)
            self._file.write(self._bext.rewrite_loudness_parameters())
        self._file.seek(curpos, 0)
        self._datalength = self._datawritten

    def _write_bext_chunk(self):
        self._file.write(struct.pack('<4s', b'bext'))
        self._file.write(struct.pack('<l', len(self._bext_chunk_data)))
        self._loudness_params_pos = self._bext.loudness_params_pos() + self._file.tell()
        self._file.write(self._bext_chunk_data)

    def _write_axml_chunk(self):
        self._file.write(struct.pack('<4s', b'axml'))
        self._file.write(struct.pack('<l', len(self._axml_chunk_data)))
        self._file.write(self._axml_chunk_data)

    def _write_md5_chunk(self):
        self._file.write(struct.pack('<4s', b'MD5 '))
        self._file.write(struct.pack('<l', 16))
        self._file.write(struct.pack('>16s', self._md5_chunk_data[::-1]))

    def _write_levl_chunk(self):
        self._file.write(struct.pack('<4s', b'levl'))
        self._file.write(struct.pack('<l', len(self._levl_chunk_data)))
        self._file.write(self._levl_chunk_data)

    def _write_chna_chunk(self):
        self._file.write(struct.pack('<4s', b'chna'))
        self._file.write(struct.pack('<l', len(self._chna_chunk_data)))
        self._file.write(self._chna_chunk_data)


def open(f, mode=None):
    if mode is None:
        if hasattr(f, 'mode'):
            mode = f.mode
        else:
            mode = 'rb'
    if mode in ('r', 'rb'):
        return Wave_read(f)
    elif mode in ('w', 'wb'):
        return Wave_write(f)
    else:
        raise Error("mode must be 'r', 'rb', 'w', or 'wb'")


openfp = open  # B/W compatibility
