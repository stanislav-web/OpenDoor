#!/usr/bin/env python

from multiprocessing import Pool
import time
import urllib2


def millis():
    return int(round(time.time() * 1000))


def http_get(url):
    start_time = millis()
    result = {"url": url, "data": urllib2.urlopen(url, timeout=5).read()[:100]}
    print url + " took " + str(millis() - start_time) + " ms"
    return result


urls = ['http://www.google.com/', 'https://foursquare.com/', 'http://www.yahoo.com/', 'http://www.bing.com/',
        "https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/","https://www.yelp.com/"]

pool = Pool(processes=10)

start_time = millis()
results = pool.map(http_get, urls)

print "\nTotal took " + str(millis() - start_time) + " ms\n"

for result in results:
    print result