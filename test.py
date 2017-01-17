import sys
import time
import string
import random
def id_generator(size=50, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def show_progress(value):

    sys.stderr.write('%s\r' % id_generator())

for i in xrange(10):
    show_progress(i)

    time.sleep(.1)