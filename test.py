import time
from functools import wraps


def fn_timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        print ("Total time running %s: %s seconds" %
               (function.func_name, str(t1 - t0))
               )
        return result

    return function_timer


# standard libraries
from datetime import datetime
import Queue
from threading import Thread

# third party libraries
import requests

# capture current time
startTime = datetime.now()

# create the instance
q = Queue.LifoQueue()

# specify sitemap to get all site links
url = [
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",
    "http://www.craigaddyman.com/sitemap.xml",

]
for u in url:
    q.put(u)

@fn_timer
def grab_data_from_queue():
    while not q.empty():  # check that the queue isn't empty

        url = q.get()  # get the item from the queue

        r = requests.get(url.strip())  # request the url

        print r.status_code, r.url  # print the response code and destination url

        q.task_done()  # specify that you are done with the item


for i in range(10):  # aka number of threadtex
    t1 = Thread(target=grab_data_from_queue)  # target is the above function
    t1.start()  # start the thread

q.join()

# print current time minus the start time
print datetime.now() - startTime