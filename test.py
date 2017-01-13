import time
import threading
import datetime as DT
import logging
logger = logging.getLogger(__name__)

def worker(cond):
    i = 0
    while True:
        with cond:
            cond.wait()
            logger.info(i)
            time.sleep(0.01)
            i += 1

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s %(threadName)s] %(message)s',
                    datefmt='%H:%M:%S')

cond = threading.Condition()
t = threading.Thread(target=worker, args=(cond, ))
t.daemon = True
t.start()

start = DT.datetime.now()
while True:
    now = DT.datetime.now()
    if (now-start).total_seconds() > 60: break
    if now.second % 2:
        with cond:
            cond.notify()