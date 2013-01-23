# -*- coding: utf-8 -
import os
import tulip
from io import BytesIO


class StreamUnreader(object):

    def __init__(self, stream):
        self.buf = BytesIO()
        self.stream = stream

    def chunk(self):
        raise NotImplementedError()

    def read(self, size=None):
        if size is not None and not isinstance(size, int):
            raise TypeError("size parameter must be an int or long.")

        if size is not None:
            if size == 0:
                return b""
            if size < 0:
                size = None

        self.buf.seek(0, os.SEEK_END)

        if size is None and self.buf.tell():
            ret = self.buf.getvalue()
            self.buf = BytesIO()
            return ret

        if size is None:
            d = yield from self.chunk()
            return d

        while self.buf.tell() < size:
            chunk = yield from self.chunk()
            if not len(chunk):
                ret = self.buf.getvalue()
                self.buf = six.BytesIO()
                return ret

            self.buf.write(chunk)

        data = self.buf.getvalue()
        self.buf = six.BytesIO()
        self.buf.write(data[size:])
        return data[:size]

    def unread(self, data):
        self.buf.seek(0, os.SEEK_END)
        self.buf.write(data)

    def chunk(self):
        if not self.stream:
            return b''

        try:
            return (yield from self.stream.read(1024))
        except tulip.CancelledError:
            self.stream = None
            return b""
