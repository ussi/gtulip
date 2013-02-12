# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.
#

import inspect
import os
import tulip
from tulip.http_client import StreamReader
from datetime import datetime

import gunicorn.http.wsgi as wsgi
import gunicorn.workers.base as base
import gunicorn.http.errors as gerrors

from gtulip.parser import RequestParser


class TulipWorker(base.Worker):

    def init_process(self):
        # create new event_loop after fork
        tulip.get_event_loop().close()

        self.ev_loop = tulip.new_event_loop()
        tulip.set_event_loop(self.ev_loop)

        super().init_process()

    def run(self):
        tulip.Task(self._run())
        return self.ev_loop.run_forever()

    def _run(self):
        def factory():
            return HTTPHandler(self, self.wsgi, self.cfg, self.log)

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


class TransportWrapper:
    """ emulate socket object """

    def __init__(self, transport):
        self.transport = transport

    def timeout(self):
        return 0.0

    def send(self, data):
        self.transport.write(data)

    def sendall(self, data):
        self.transport.write(data)


class HTTPHandler:

    nr = 0
    task = None

    def __init__(self, worker, wsgi, cfg, log):
        self.worker = worker
        self.wsgi = wsgi
        self.cfg = cfg
        self.log = log
        self._close_callbacks = []

    def connection_made(self, transport):
        self.transport = transport
        self.transport_wrp = TransportWrapper(transport)
        self.stream = StreamReader()
        self.parser = RequestParser(self.cfg, self.stream)

    def data_received(self, data):
        if self.task is None:
            self.task = tulip.Task(self.handle())

        self.stream.feed_data(data)

    def eof_received(self):
        self.stream.feed_eof()
        for cb in self._close_callbacks:
            cb()

    def connection_lost(self, exc):
        if self.task and not self.task.done():
            self.log.debug("Ignored premature client disconnection.")
            self.task.cancel()

    def add_close_callback(self, cb):
        self._close_callbacks.append(cb)

    def handle(self):
        req = None
        try:
            req = yield from self.parser.get()
            yield from self.handle_request(req)
        except tulip.CancelledError:
            pass
        except gerrors.NoMoreData as e:
            self.log.debug("Ignored premature client disconnection. %s", e)
        except Exception as e:
            self.worker.handle_error(req, self.transport_wrp, ['', ''], e)
        finally:
            self.task = None

    def handle_request(self, req):
        environ = {}
        resp = None
        try:
            self.cfg.pre_request(self, req)
            request_start = datetime.now()
            resp, environ = wsgi.create(
                req, self.transport_wrp, None, '', self.cfg)

            environ['tulip.read'] = self.stream.read
            environ['tulip.write'] = self.transport.write
            environ['tulip.close'] = self.transport.close
            environ['tulip.add_close_callback'] = self.add_close_callback
            environ['tulip.closed'] = False

            self.nr += 1
            respiter = self.wsgi(environ, resp.start_response)
            if (inspect.isgenerator(respiter) or
                inspect.isgeneratorfunction(respiter)):
                respiter = yield from respiter

            try:
                # TODO: use resp.write_file for wsgi.file_wrapper
                for item in respiter:
                    if isinstance(item, tulip.Future):
                        if not data.done():
                            item = yield from data
                        else:
                            item = data.result()

                    resp.write(item)

                if not environ['tulip.closed']:
                    resp.close()
                else:
                    resp.force_close()
                request_time = datetime.now() - request_start
                self.log.access(resp, req, environ, request_time)
            finally:
                if hasattr(respiter, "close"):
                    respiter.close()

        except tulip.CancelledError:
            raise

        except Exception as e:
            # Only send back traceback in HTTP in debug mode.
            self.worker.handle_error(req, self.transport_wrp, ['', ''], e)

        finally:
            if resp is not None:
                if resp.should_close():
                    self.transport.close()
            else:
                self.transport.close()

            try:
                self.cfg.post_request(self, req, environ, resp)
            except Exception:
                self.log.exception("Exception in post_request hook")
