#!/usr/bin/env python

from urllib3 import HTTPConnectionPool


import time

i = 0

num_status_code = 0

other_status_code = 0

pool = HTTPConnectionPool('127.0.0.1', maxsize=1, port=80, timeout=None)

while i < 10:

    r = pool.request('GET', '/')
    time.sleep(1)
    i += 1

    # count the status code

if r.status == 200:
    num_status_code += 1
else:
    other_status_code += 1
print "number of 200 OK %s:" % num_status_code
print "number of other status codes: %s" % other_status_code