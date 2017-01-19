import time
import socket
while True:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    start = time.time()
    s.connect(('www.google.at',80))
    print 'time taken ', int(time.time()-start) ,' ms'
    s.close()
    time.sleep(1)