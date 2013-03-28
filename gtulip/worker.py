# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.
#

import io
import os
import urllib.parse
from datetime import datetime

import tulip
import httpclient

import gunicorn.http.wsgi as wsgi
import gunicorn.workers.base as base
import gunicorn.http.errors as gerrors


class TulipWorker(base.Worker):

    def init_process(self):
        # create new event_loop after fork
        tulip.get_event_loop().close()

        self.ev_loop = tulip.new_event_loop()
        tulip.set_event_loop(self.ev_loop)

        super().init_process()

    def run(self):
        self._run()
        return self.ev_loop.run_forever()

    @tulip.task
    def _run(self):
        def factory():
            return tulip.http.WSGIServerHttpProtocol(
                self.wsgi, readpayload=True)

        # insert sockets to event_loop
        for sock in self.sockets:
            self.ev_loop.start_serving(factory, sock=sock)

        # If our parent changed then we shut down.
        pid = os.getpid()
        try:
            while self.alive:
                self.notify()

                if pid == os.getpid() and self.ppid != os.getppid():
                    self.log.info("Parent changed, shutting down: %s", self)
                    break

                yield from tulip.sleep(1.0)
        except KeyboardInterrupt:
            pass

        tulip.get_event_loop().stop()
        tulip.get_event_loop().close()
