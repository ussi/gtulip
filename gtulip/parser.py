# -*- coding: utf-8 -
import tulip
from gtulip.message import Request
from gtulip.unreader import StreamUnreader


class Parser(object):

    def __init__(self, mesg_class, cfg, stream):
        self.mesg_class = mesg_class
        self.cfg = cfg
        self.unreader = StreamUnreader(stream)

        self.mesg = None

        # request counter (for keepalive connetions)
        self.req_count = 0

    @tulip.coroutine
    def get(self):
        # Stop if HTTP dictates a stop.
        if self.mesg and self.mesg.should_close():
            raise StopIteration()

        # Discard any unread body of the previous message
        if self.mesg:
            data = self.mesg.body.read(8192)
            while data:
                data = self.mesg.body.read(8192)

        # Parse the next request
        self.req_count += 1
        self.mesg = self.mesg_class(self.cfg, self.unreader, self.req_count)
        if not self.mesg:
            raise StopIteration()

        unused = yield from self.mesg.parse(self.unreader)
        self.unreader.unread(unused)
        self.mesg.set_body_reader()

        return self.mesg


class RequestParser(Parser):

    def __init__(self, *args, **kwargs):
        super(RequestParser, self).__init__(Request, *args, **kwargs)
