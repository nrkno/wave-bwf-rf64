"""Simple class to read IFF chunks.

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

An IFF chunk (used in formats such as AIFF, TIFF, RMFF (RealMedia File
Format)) has the following structure:

+----------------+
| ID (4 bytes)   |
+----------------+
| size (4 bytes) |
+----------------+
| data           |
| ...            |
+----------------+

The ID is a 4-byte string which identifies the type of chunk.

The size field (a 32-bit value, encoded using big-endian byte order)
gives the size of the whole chunk, including the 8-byte header.

Usually an IFF-type file consists of one or more chunks.  The proposed
usage of the Chunk class defined here is to instantiate an instance at
the start of each chunk and read from the instance until it reaches
the end, after which a new instance can be instantiated.  At the end
of the file, creating a new instance will fail with a EOFError
exception.

Usage:
while True:
    try:
        chunk = Chunk(file)
    except EOFError:
        break
    chunktype = chunk.getname()
    while True:
        data = chunk.read(nbytes)
        if not data:
            pass
        # do something with data

The interface is file-like.  The implemented methods are:
read, close, seek, tell, isatty.
Extra methods are: skip() (called by close, skips to the end of the chunk),
getname() (returns the name (ID) of the chunk)

The __init__ method has one required argument, a file-like object
(including a chunk instance), and one optional argument, a flag which
specifies whether or not chunks are aligned on 2-byte boundaries.  The
default is 1, i.e. aligned.
"""


class Chunk:
    def __init__(self, file, align=True, bigendian=True, inclheader=False,
                 set_data_chunk_size=None):
        import struct
        self.closed = False
        self.align = align      # whether to align to word (2-byte) boundaries
        if bigendian:
            strflag = '>'
        else:
            strflag = '<'
        self.file = file
        self.chunkname = file.read(4)
        if len(self.chunkname) < 4:
            raise EOFError
        if set_data_chunk_size is not None and self.chunkname == b'data':
            self.chunksize = set_data_chunk_size
            # Read dummy value
            struct.unpack(strflag+'L', file.read(4))
        else:
            try:
                self.chunksize = struct.unpack(strflag+'L', file.read(4))[0]
            except struct.error:
                raise EOFError
        if inclheader:
            self.chunksize = self.chunksize - 8  # subtract header
        self.size_read = 0
        try:
            self.offset = self.file.tell()
        except (AttributeError, IOError):
            self.seekable = False
        else:
            self.seekable = True

    def getname(self):
        """Return the name (ID) of the current chunk."""
        return self.chunkname

    def getsize(self):
        """Return the size of the current chunk."""
        return self.chunksize

    def setsize(self, newsize):
        # ***
        self.chunksize = newsize

    def close(self):
        if not self.closed:
            try:
                self.skip()
            finally:
                self.closed = True

    def isatty(self):
        if self.closed:
            raise ValueError('I/O operation on closed file')
        return False

    def seek(self, pos, whence=0):
        """Seek to specified position into the chunk.
        Default position is 0 (start of chunk).
        If the file is not seekable, this will result in an error.
        """

        if self.closed:
            raise ValueError('I/O operation on closed file')
        if not self.seekable:
            raise IOError('cannot seek')
        if whence == 1:
            pos = pos + self.size_read
        elif whence == 2:
            pos = pos + self.chunksize
        if pos < 0 or pos > self.chunksize:
            # print(pos, self.chunksize)
            raise RuntimeError
        self.file.seek(self.offset + pos, 0)
        self.size_read = pos

    def tell(self):
        if self.closed:
            raise ValueError('I/O operation on closed file')
        return self.size_read

    def read(self, size=-1):
        """Read at most size bytes from the chunk.

        If size is omitted or negative, read until the end
        of the chunk.
        """

        if self.closed:
            raise ValueError('I/O operation on closed file')
        if self.size_read >= self.chunksize:
            return b''
        if size < 0:
            size = self.chunksize - self.size_read
        if size > self.chunksize - self.size_read:
            size = self.chunksize - self.size_read
        data = self.file.read(size)
        self.size_read = self.size_read + len(data)
        if self.size_read == self.chunksize and \
           self.align and \
           (self.chunksize & 1):
            dummy = self.file.read(1)
            self.size_read = self.size_read + len(dummy)
        return data

    def skip(self):
        """Skip the rest of the chunk.

        If you are not interested in the contents of the chunk,
        this method should be called so that the file points to
        the start of the next chunk.
        """

        if self.closed:
            raise ValueError('I/O operation on closed file')
        if self.seekable:
            try:
                n = self.chunksize - self.size_read
                # maybe fix alignment
                if self.align and (self.chunksize & 1):
                    n = n + 1
                self.file.seek(n, 1)
                self.size_read = self.size_read + n
                return
            except IOError:
                pass
        while self.size_read < self.chunksize:
            n = min(8192, self.chunksize - self.size_read)
            dummy = self.read(n)
            if not dummy:
                raise EOFError

