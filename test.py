import Queue
import urllib2
import os
import signal
import sys
import time
import threading
from socket import error  as _SocketError
urls = ["http://broadcast.lds.org/churchmusic/MP3/1/2/nowords/271.mp3",
"http://s1.fans.ge/mp3/201109/08/John_Legend_So_High_Remix(fans_ge).mp3",
"http://megaboon.com/common/preview/track/786203.mp3"]
queue = Queue.Queue()
def do_exit(sigNum, stack):
    # handle unix signal recived and exit
    sys.stderr.write("Received signal %d " % (sigNum))
    raise SystemExit("Exiting")
class ThreadedFetch(threading.Thread):
    """ docstring for ThreadedFetch
    """
    def __init__(self, queue, count = 1):
        super(ThreadedFetch, self).__init__()
        self.queue = queue
    def run(self):
        while True:
            # grabs url of link and path to saveTo and save to lst
            host = self.queue.get()
            # submit the url for download and location where to save.
            self._downloadFile(host[0], host[1])
    def _downloadFile(self, url, saveTo=None):
        file_name = url.split('/')[-1]
        self.setName("Parent_%s_thread" % file_name.split(".")[0])
        if not saveTo:
            saveTo = '/Users/krystoSan/Desktop'
        try:
            u = urllib2.urlopen(url)
        except urllib2.URLError , er:
            print("%s for %s failed to download." % (er.reason, file_name))
            self.queue.task_done()
            print "Exiting: %s" % self.getName()
        except _SocketError , err:
            print("%s \n %s failed to download." % (err, file_name))
            self.queue.task_done()
        else:
            th = threading.Thread(
                    target=self._fileWriteToDisk,
                    args=(saveTo, u, file_name),
                    name="fileWrite_Child_of_%s" % self.getName(),
                    )
            # if the user clicks close while the thread is still running,
            # then the programme will wait till the save is done,
            # then it will close.
            th.daemon = False
            th.start()
            time.sleep(0.1)
            print "Writing to disk using child: %s " % th.name
    def _fileWriteToDisk(self, saveTo, urlObject, file_name):
        path = os.path.join(saveTo, file_name)
        try:
            f = open(path, 'wb')
        except IOError , er:
            self.queue.task_done()
            print er
            return
        meta = urlObject.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s : %s " % (file_name, sizeof(file_size))
        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = urlObject.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            sys.stdout.write('%s\r' % status)
            time.sleep(.05)
            sys.stdout.flush()
            if file_size_dl == file_size:
                print r"Download Completed %s%% for file %s, saved to %s" % (file_size_dl * 100. / file_size, file_name, saveTo)
        f.close()
        # signals to queue job is done
        self.queue.task_done()
def main():
    # Register signal in main thread
    signal.signal(signal.SIGINT, do_exit)
    try:
        # spawn a pool of threads, and pass them queue instance
        for i in range(len(urls)):
            t = ThreadedFetch(queue)
            t.setDaemon(True)
            time.sleep(0.1)
            t.start()
        urls_saveTo = {urls[0]: None, urls[1]: None, urls[2]: None}
        # populate queue with data
        for item, value in urls_saveTo.iteritems():
            queue.put([item, value])
        # wait on the queue until everything has been processed
        queue.join()
        print '*** Done'
    except (KeyboardInterrupt, SystemExit):
        print '\n! Received keyboard interrupt, quitting threads.\n'
def sizeof(bytes):
    """
    Takes the size of file or folder in bytes and returns size formatted in kb, MB or more..
    """
    alternative = [
        (1024 ** 5, ' PB'),
        (1024 ** 4, ' TB'),
        (1024 ** 3, ' GB'),
        (1024 ** 2, ' MB'),
        (1024 ** 1, ' KB'),
        (1024 ** 0, (' byte', ' bytes')),
    ]
    for factor, suffix in alternative:
        if bytes >= factor:
            break
    amount = int(bytes/factor)
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return "%s %s" % (str(amount), suffix)
if __name__ == "__main__":
    main()