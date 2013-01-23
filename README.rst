Experimental Tulip based Gunicorn worker
========================================

Experimental async worker for gunicorn based on tulip library (PEP-3156).

Paster configuration example::

   [server:main]
   use = egg:gunicorn#main
   host = 0.0.0.0
   port = 8080
   worker = gtulip.TulipWorker



Requirements
------------

- Python 3.3

- gunicorn 0.17.2

- tulip http://code.google.com/p/tulip/


License
-------

gtulip is offered under the MIT license.
