import time
import sys
import os

def countd():

    seconds = 59
    minutes = 4
    five_minutes = 0

    os.system('clear')
    os.system('setterm -cursor off')

    while five_minutes != 300:
        sys.stdout.write("\r%d:%02.f\t" % (minutes, seconds))
        sys.stdout.flush()
        seconds -= 1
        if seconds == -1:
            minutes -= 1
            seconds = 59

        five_minutes += 1
        time.sleep(1)

countd()

os.system('setterm -cursor on')